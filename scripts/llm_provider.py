"""
llm_provider.py

Provider resolution with graceful fallback:

    1. OpenRouter  (OPENROUTER_API_KEY)
    2. Anthropic   (ANTHROPIC_API_KEY)
    3. Fail loudly with an actionable message.

Both providers are called through the Anthropic Messages API. OpenRouter exposes
an Anthropic-compatible endpoint (its "Anthropic Skin") at https://openrouter.ai/api,
so the same `anthropic` SDK client works for both; only the base URL, the key, and
the model slug change.

Pinning (see scripts/check_openrouter_pin.py, verified 2026-08-10): OpenRouter
honours the `provider` routing block on the Skin. With pin=True, requests are
restricted to Anthropic first-party and fail closed (404) rather than being
load-balanced across Vertex, Azure, or Bedrock. Use pin=True for anything you
intend to report; use pin=False for exploration, where failover is a feature.

Note that the pin rides in the request body and therefore applies to SDK calls
only. Claude Code traffic (the GitHub Actions layer) cannot carry it; enforce
provider preferences at the OpenRouter account level if that matters there.

Dependency policy: importing this module and calling probe_openrouter() or
reading MODEL_MAP requires the standard library only, so CI can import it on a
bare runner (see scripts/select_provider.py). The `anthropic` SDK is imported
lazily and is needed only to actually send requests.

Requires (for sending requests, not for importing): pip install "anthropic>=0.40"
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable

log = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api"
ANTHROPIC_BASE_URL = "https://api.anthropic.com"

# Restricts OpenRouter to Anthropic first-party. `order` alone is only a
# try-priority; allow_fallbacks=False is what makes it a pin.
ANTHROPIC_1P_PIN = {"only": ["anthropic"], "allow_fallbacks": False}

# Single source of truth for model slugs, shared by the SDK path and the CI
# routing step. Verify against https://openrouter.ai/models and
# https://docs.claude.com/en/docs/about-claude/models. Use dated snapshots, not
# moving aliases, for anything you will report.
MODEL_MAP: dict[str, dict[str, str]] = {
    "openrouter": {
        "opus": "anthropic/claude-opus-5",
        "sonnet": "anthropic/claude-sonnet-5",
        "haiku": "anthropic/claude-haiku-4.5",
    },
    "anthropic": {
        "opus": "claude-opus-5",
        "sonnet": "claude-sonnet-5",
        "haiku": "claude-haiku-4-5-20251001",
    },
}

BASE_URLS = {"openrouter": OPENROUTER_BASE_URL, "anthropic": ANTHROPIC_BASE_URL}
KEY_ENV = {"openrouter": "OPENROUTER_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}


class NoProviderAvailable(RuntimeError):
    """Raised when no usable API key was found."""


@dataclass
class Call:
    """Per-call record. Append to your run log so routing is visible in the data."""
    provider: str        # which of our two entries served it
    backend: str | None  # OpenRouter's serving backend, e.g. 'Anthropic', 'Google'
    model: str
    cost: float | None
    input_tokens: int | None
    output_tokens: int | None
    pinned: bool


@dataclass
class Provider:
    name: str
    api_key: str
    base_url: str
    models: dict[str, str]
    note: str = ""
    _client: Any = field(default=None, repr=False)

    @property
    def client(self):
        if self._client is None:
            from anthropic import Anthropic  # lazy: keeps import-time deps stdlib-only

            headers: dict[str, str] = {}
            if self.name == "openrouter":
                # OpenRouter's skin authenticates with a bearer token; the SDK
                # sends x-api-key. Sending both keeps either path working.
                headers["Authorization"] = f"Bearer {self.api_key}"
                headers["X-Title"] = os.getenv("OPENROUTER_APP_TITLE", "IgboAI")
            self._client = Anthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers=headers or None,
                max_retries=2,
                timeout=120.0,
            )
        return self._client

    def model(self, alias: str) -> str:
        return self.models.get(alias, alias)


# ---------------------------------------------------------------- key probes


def probe_openrouter(key: str, timeout: float = 5.0) -> tuple[bool, str]:
    """
    GET /api/v1/key: cheap, no tokens spent, no third-party imports.

    Reports remaining per-key credit. Stdlib only so CI can call it on a bare
    runner. Returns (usable, human-readable detail).
    """
    req = urllib.request.Request(
        f"{OPENROUTER_BASE_URL}/v1/key",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False, "key rejected (401/403)"
        return False, f"unexpected status {exc.code}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, f"could not reach OpenRouter ({exc.__class__.__name__})"

    remaining = (body.get("data") or {}).get("limit_remaining")
    if remaining is not None and remaining <= 0:
        return False, "per-key credit limit exhausted"
    left = "unlimited" if remaining is None else f"{remaining:.4f} credits left on key"
    return True, left


def probe_anthropic(key: str) -> tuple[bool, str]:
    """One-token call. Costs a fraction of a cent and confirms auth plus balance."""
    from anthropic import (  # lazy
        Anthropic, APIConnectionError, APIStatusError, AuthenticationError,
    )

    try:
        Anthropic(api_key=key, timeout=20.0, max_retries=0).messages.create(
            model=MODEL_MAP["anthropic"]["haiku"],
            max_tokens=1,
            messages=[{"role": "user", "content": "."}],
        )
    except AuthenticationError:
        return False, "key rejected (401)"
    except APIStatusError as exc:
        if exc.status_code in (400, 402, 403):
            return False, f"key unusable (HTTP {exc.status_code}): billing or permissions"
        # 429 or 5xx: the key is valid, the service is just busy.
        return True, f"reachable, transient HTTP {exc.status_code}"
    except APIConnectionError as exc:
        return False, f"could not reach Anthropic ({exc.__class__.__name__})"
    return True, "key valid"


PROBES = {"openrouter": probe_openrouter, "anthropic": probe_anthropic}


# ------------------------------------------------------------ resolution


def resolve_provider(
    order: Iterable[str] = ("openrouter", "anthropic"),
    verify: bool = True,
) -> Provider:
    """
    Return the first provider with a usable key, in the given order.

    Set verify=False to skip the network probes (faster startup; failures then
    surface on the first real call instead).
    """
    failures: list[str] = []

    for name in order:
        if name not in BASE_URLS:
            raise ValueError(f"unknown provider: {name}")
        env_name = KEY_ENV[name]
        key = os.getenv(env_name, "").strip()

        if not key:
            failures.append(f"  {name:<11} {env_name} not set")
            continue

        if verify:
            ok, detail = PROBES[name](key)
            if not ok:
                failures.append(f"  {name:<11} {detail}")
                log.warning("provider %s unavailable: %s", name, detail)
                continue
        else:
            detail = "not verified"

        log.info("using provider: %s (%s)", name, detail)
        return Provider(name=name, api_key=key, base_url=BASE_URLS[name],
                        models=MODEL_MAP[name], note=detail)

    raise NoProviderAvailable(
        "No usable LLM provider was found.\n"
        + "\n".join(failures)
        + "\n\nFix one of:\n"
        "  export OPENROUTER_API_KEY=sk-or-...   (https://openrouter.ai/settings/keys)\n"
        "  export ANTHROPIC_API_KEY=sk-ant-...   (https://console.anthropic.com/settings/keys)"
    )


# ------------------------------------------------------------ thin wrapper


class LLM:
    """
    Resolves once at construction and demotes to the next provider if the active
    one runs out of credit mid-run.

    pin=True  : restrict OpenRouter to Anthropic first-party. A 429 is then a
                real rate limit on the only backend you accept, so we back off
                and retry rather than demoting to a second key that would hit
                the same limit. Reported runs want this.
    pin=False : let OpenRouter load-balance. Faster to recover, but the serving
                backend can change mid-sweep. Exploration only.
    """

    def __init__(
        self,
        order: Iterable[str] = ("openrouter", "anthropic"),
        verify: bool = True,
        pin: bool = True,
        max_backoff_attempts: int = 5,
    ):
        self._order = list(order)
        self._verify = verify
        self.pin = pin
        self.max_backoff_attempts = max_backoff_attempts
        self.trace: list[Call] = []
        self.provider = resolve_provider(self._order, verify=verify)

    def _request_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        kwargs = dict(kwargs)
        kwargs.setdefault("max_tokens", 1024)
        if self.pin and self.provider.name == "openrouter":
            extra = dict(kwargs.get("extra_body") or {})
            extra.setdefault("provider", ANTHROPIC_1P_PIN)
            kwargs["extra_body"] = extra
        return kwargs

    def complete(self, prompt: str, alias: str = "sonnet", **kwargs: Any) -> str:
        from anthropic import APIStatusError  # lazy

        attempt = 0
        while True:
            try:
                resp = self.provider.client.messages.create(
                    model=self.provider.model(alias),
                    messages=[{"role": "user", "content": prompt}],
                    **self._request_kwargs(kwargs),
                )
                break
            except APIStatusError as exc:
                status = exc.status_code

                # 404 on a pinned run means the pin cannot be satisfied. That is a
                # configuration error, not a transient one. Fail loudly.
                if status == 404 and self.pin:
                    raise RuntimeError(
                        "Pinned provider unavailable for this model. Response:\n"
                        f"{exc.response.text}\n"
                        "Either the model is not served by Anthropic first-party or the "
                        "slug is wrong. Do not silently unpin a reported run."
                    ) from exc

                # Rate limited on the only backend we accept: wait, do not switch.
                if status == 429 and self.pin:
                    attempt += 1
                    if attempt > self.max_backoff_attempts:
                        raise
                    delay = min(60.0, 2 ** attempt) * (0.5 + random.random())
                    log.warning("429 on pinned backend; sleeping %.1fs (attempt %d/%d)",
                                delay, attempt, self.max_backoff_attempts)
                    time.sleep(delay)
                    continue

                # Unpinned, or out of credit: try the next key.
                if status in (401, 402, 429) and len(self._order) > 1:
                    dead = self.provider.name
                    log.warning("%s returned HTTP %s; falling back", dead, status)
                    self._order = [p for p in self._order if p != dead]
                    self.provider = resolve_provider(self._order, verify=self._verify)
                    attempt = 0
                    continue
                raise

        usage = getattr(resp, "usage", None)
        self.trace.append(Call(
            provider=self.provider.name,
            backend=getattr(resp, "provider", None),   # Skin only; None on direct Anthropic
            model=self.provider.model(alias),
            cost=getattr(resp, "cost", None),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            pinned=self.pin and self.provider.name == "openrouter",
        ))
        return "".join(b.text for b in resp.content if b.type == "text")

    def spend(self) -> float:
        """Total cost recorded so far. OpenRouter reports it per call; direct Anthropic does not."""
        return sum(c.cost or 0.0 for c in self.trace)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        llm = LLM(pin=True)
    except NoProviderAvailable as exc:
        raise SystemExit(str(exc))
    print(f"[{llm.provider.name}] {llm.complete('Reply with one word: ping.', alias='haiku')}")
    print(llm.trace[-1])
