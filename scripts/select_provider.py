#!/usr/bin/env python3
"""Decide which LLM provider the Claude Code step should use. Stdlib only.

Mirrors resolve_provider() in llm_provider.py, and imports the probe and the
model map from it so the routing rule and the model slugs have one definition.
The `anthropic` SDK is imported lazily there, so this runs on a bare runner with
no pip install, matching the repo's no-dependencies-on-the-runner policy.

Order: OpenRouter first (spend those credits), personal Anthropic key second.

OpenRouter is chosen when GET /api/v1/key returns 200 and the key still has
credit. A missing secret, a revoked key, an exhausted cap, or an unreachable
endpoint all fall through to Anthropic. If neither is usable, exit non-zero so
the workflow fails at this step rather than burning turns on a doomed run.

Writes to $GITHUB_OUTPUT (or stdout when run locally):
    provider, base_url, model, small_model, use_openrouter

Deliberately does NOT emit the API key. The workflow selects the secret itself
via the use_openrouter flag, so no credential passes through a step output.

Usage in a workflow:
    - name: Choose provider
      id: route
      env:
        OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: python scripts/select_provider.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_provider import BASE_URLS, MODEL_MAP, probe_openrouter  # noqa: E402

# Which aliases the Claude Code step uses. ANTHROPIC_MODEL is the main driver;
# ANTHROPIC_SMALL_FAST_MODEL handles cheap background calls.
MAIN_ALIAS = os.getenv("IGBOAI_MODEL_ALIAS", "sonnet")
SMALL_ALIAS = os.getenv("IGBOAI_SMALL_MODEL_ALIAS", "haiku")


def emit(**kv: str) -> None:
    lines = [f"{k}={v}" for k, v in kv.items()]
    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    else:
        print("\n".join(lines))


def main() -> int:
    or_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    an_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    chosen, why = None, []
    if or_key:
        ok, detail = probe_openrouter(or_key)
        if ok:
            chosen = "openrouter"
            why.append(f"openrouter: {detail}")
        else:
            why.append(f"openrouter unusable: {detail}")
    else:
        why.append("openrouter: OPENROUTER_API_KEY not set")

    if chosen is None:
        # No cheap balance endpoint exists for Anthropic, so presence is all we
        # can check for free. A bad key surfaces as a 401 on the first call.
        if an_key:
            chosen = "anthropic"
            why.append("anthropic: key present (not probed)")
        else:
            why.append("anthropic: ANTHROPIC_API_KEY not set")

    for line in why:
        print(line, file=sys.stderr)

    if chosen is None:
        print(
            "::error::No usable LLM provider. Set OPENROUTER_API_KEY or "
            "ANTHROPIC_API_KEY as a repository secret.",
            file=sys.stderr,
        )
        return 1

    emit(
        provider=chosen,
        base_url=BASE_URLS[chosen],
        model=MODEL_MAP[chosen][MAIN_ALIAS],
        small_model=MODEL_MAP[chosen][SMALL_ALIAS],
        use_openrouter="true" if chosen == "openrouter" else "false",
    )
    print(f"Routing to {chosen} ({MODEL_MAP[chosen][MAIN_ALIAS]})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
