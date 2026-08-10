"""
Does OpenRouter's Anthropic Skin honour provider routing parameters?

The Skin (https://openrouter.ai/api) speaks the Anthropic Messages protocol, but
provider routing is an OpenRouter concept passed in the request body. This probe
checks whether the `provider` block survives that path, because if it does not,
every "pinned" experimental run is silently load-balanced across backends.

Result, 2026-08-10, anthropic SDK 0.x, model anthropic/claude-haiku-4.5:

    only=["anthropic"]      -> 200, response.provider == 'Anthropic'
    only=["google-vertex"]  -> 200, response.provider == 'Google'
    only=["deepinfra"]      -> 404 NotFoundError, "No allowed providers are
                               available for the selected model",
                               metadata.available_providers ==
                               ["google-vertex", "anthropic", "azure", "amazon-bedrock"]

Conclusion: the block is parsed and enforced. Two different pins produce two
different backends, so the first result is a real pin and not a default route.
An unsatisfiable pin fails closed with 404 rather than rerouting, which is the
behaviour reported runs depend on. 404 is a permanent config error and must not
trigger provider demotion.

Also learned: the Skin returns `provider` and `cost` on the response object, so
per-call backend attribution and spend can be logged without the dashboard.

Re-run this after any OpenRouter change to the Skin, and before trusting the pin
in a run you intend to report. Set MODE below to switch cases.

    python scripts/check_openrouter_pin.py
"""

import os

from anthropic import Anthropic, APIStatusError

MODE = "pin"  # "pin" | "counterfactual" | "unsatisfiable"
ONLY = {"pin": ["anthropic"], "counterfactual": ["google-vertex"], "unsatisfiable": ["deepinfra"]}

key = os.environ["OPENROUTER_API_KEY"]
client = Anthropic(
    api_key=key,
    base_url="https://openrouter.ai/api",
    default_headers={"Authorization": f"Bearer {key}"},
)

try:
    resp = client.messages.create(
        model="anthropic/claude-haiku-4.5",
        max_tokens=16,
        messages=[{"role": "user", "content": "Reply with one word: ping."}],
        extra_body={"provider": {"only": ONLY[MODE], "allow_fallbacks": False}},
    )
    print(f"[{MODE}] 200  provider={getattr(resp, 'provider', None)!r}  "
          f"cost={getattr(resp, 'cost', None)}")
except APIStatusError as exc:
    print(f"[{MODE}] {type(exc).__name__} status={exc.status_code}\n{exc.response.text}")