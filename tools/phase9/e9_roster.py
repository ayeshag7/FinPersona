"""
v2.1 Phase 9 -- the CANDIDATE model configurations: what the smoke tests time and what the roster question is asked
about (execution prompt, "Decisions"; D2 re-framed by P9-1).

**None of these is the roster.** The team chooses the roster; `PREREG_PHASE_9.md` records the choice. A candidate
is a model id the provider served to this account's keys on 11 Sep 2026, in one configuration:

* the temperature SENT (None means none is sent);
* the provider options the client is built with.

Configurations are facts to test, not to rediscover (rule 24):

* Flash runs with thinking off (P8-8).
* `langchain_openai` drops any temperature other than 1 for gpt-5 models, so those are configured and logged at
  1.0 (addendum 6).
* Claude Sonnet 5 and Opus 5 reject any temperature (P8-12), so none is sent. Claude Fable 5.1 was never tested, so it
  starts the same way.
* Every other model runs at the harness default temperature (`experiments.arms_v2.FACTOR_DEFAULTS`, 0.2) with the
  provider's default reasoning.

A smoke confirms or refutes each configuration, and the client's own temperature attribute is logged beside the
configured one.

Prices: only the two E8.5 models carry a price that was read (plan 0.4, 26-27 Aug). Every other run logs its tokens
and no dollar figure, because cost is not a constraint (P9-1) and a price not read is not typed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HARNESS_TEMPERATURE = 0.2                           # experiments/arms_v2.py FACTOR_DEFAULTS["temperature"]
# PREREG_PHASE_9_ADDENDUM.md 7 (12 Sep 2026): OpenRouter configurations only.  Derived from the measured worst case
# across every run on disk (3,097 output tokens per call, GPT-5 nano), not stipulated; a truncated reply would show as
# a parse fallback, which is reported per configuration.
OPENROUTER_MAX_TOKENS = 8192
# USD per M input / output.  The rule is unchanged: a price not READ is not typed.  The first two were read for
# plan 0.4 (26-27 Aug).  The rest were read at source on 17 Sep 2026 -- Google at ai.google.dev/gemini-api/docs/pricing
# and OpenAI at developers.openai.com/api/docs/pricing -- so that every first-party run logs its own cost instead of
# tokens alone; a provider-reported figure still wins over this table wherever one is returned (e9_runner.stage_run).
# Both original entries reproduced exactly from those pages, and the table reproduces gpt-5-mini's provider-reported
# cost to 0.4 % on the E9.2 pilot (0.3357 against 0.3342), which is the check that it is applied correctly.
# Gemini 2.5 Pro is tiered at a 200k PROMPT; every call here is ~1.8k, so the <= 200k rate is the right one.
PRICES_READ = {
    "gemini-2.5-flash": (0.30, 2.50), "gpt-5-mini": (0.25, 2.00),           # plan 0.4, re-verified 17 Sep 2026
    "gemini-2.5-flash-lite": (0.10, 0.40), "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.5-flash": (1.50, 9.00),
    "gpt-5": (1.25, 10.00), "gpt-5-nano": (0.05, 0.40), "gpt-5.4-mini": (0.75, 4.50), "gpt-5.5": (5.00, 30.00),
}


@dataclass(frozen=True)
class ModelConfig:
    model: str
    provider: str                                   # google | openai | anthropic | openrouter
    config_tag: str
    temperature: Optional[float]                    # the temperature SENT; None = none sent
    options: Dict[str, Any] = field(default_factory=dict)
    basis: str = ""
    # OpenRouter only (P9-8; PREREG_PHASE_9_ADDENDUM.md 6): the ONE upstream this configuration may be served by.
    # Chosen by the registered rule -- lowest price per run at our measured token profile, ties to the larger context
    # window -- and enforced with allow_fallbacks: false, so an unavailable upstream fails instead of re-routing.
    upstream: Optional[str] = None

    @property
    def key(self) -> str:
        return f"{self.model}|{self.config_tag}"

    @property
    def slug(self) -> str:
        return self.model.replace("/", "_")


def _g(model, tag="default", options=None, basis="provider default reasoning; harness temperature"):
    return ModelConfig(model, "google", tag, HARNESS_TEMPERATURE, dict(options or {}), basis)


def _o(model, tag="default", options=None, basis="provider default reasoning; gpt-5 models accept only temperature 1"):
    return ModelConfig(model, "openai", tag, 1.0, dict(options or {}), basis)


def _a(model, temperature, tag="default", options=None, basis=""):
    return ModelConfig(model, "anthropic", tag, temperature, dict(options or {}), basis)


def _r(model, upstream, basis, temperature=HARNESS_TEMPERATURE, tag="default", options=None):
    """An OpenRouter configuration pinned to one upstream (P9-8)."""
    return ModelConfig(model, "openrouter", tag, temperature, dict(options or {}), basis, upstream)


CANDIDATES = (
    # timed in E8.5 (batch ledgers)
    _g("gemini-2.5-flash", "thinking0", {"thinking_budget": 0}, "P8-8: thinking off; E8.5's configuration"),
    _o("gpt-5-mini", basis="E8.5's transfer configuration (temperature 1.0, provider default reasoning)"),
    # not yet timed -- smoke
    _g("gemini-2.5-flash-lite"),
    _g("gemini-2.5-pro"),
    _g("gemini-3.5-flash"),
    _o("gpt-5-nano"),
    _o("gpt-5"),
    _o("gpt-5.4-mini"),
    _o("gpt-5.5"),
    _a("claude-haiku-4-5-20251001", HARNESS_TEMPERATURE, basis="accepts a temperature (L3 ran it at 0.0, P8-12)"),
    _a("claude-sonnet-5", None, basis="rejects any temperature (P8-12); adaptive thinking is the provider default"),
    _a("claude-opus-5", None, basis="rejects any temperature (P8-12); adaptive thinking is the provider default"),
    _a("claude-fable-5-1", None, basis="not tested with a temperature; starts as Sonnet 5 / Opus 5 do"),
    # P9-8 (12 Sep 2026): the one budget is $300 of OpenRouter credit.  Claude is represented by Haiku alone, on the
    # route the grid runs; four open-weight families join through the same key.  Every one is pinned to a single
    # upstream by the registered rule (addendum 6): lowest price per run at our measured token profile, ties to the
    # larger context window.  Prices and upstreams read 12 Sep 2026.
    _r("openrouter/anthropic/claude-haiku-4.5", "Anthropic",
       "Claude via OpenRouter, pinned to Anthropic's own API ($0.56/run). Its 252 direct-API runs are NOT pooled with "
       "this route's (addendum 6); they are reported as a route sensitivity"),
    _r("openrouter/deepseek/deepseek-v4-flash", "Baidu",
       "open-weight ($0.040/run; Baidu and StreamLake tie on price, Baidu has the larger context: 1,048,576)"),
    _r("openrouter/qwen/qwen3.7-flash", "Alibaba",
       "open-weight ($0.021/run; Alibaba is the only upstream, so the pin is inherent)"),
    _r("openrouter/z-ai/glm-4.7-flash", "Cloudflare",
       "open-weight ($0.050/run; Venice and Cloudflare tie on price, Cloudflare has the larger context: 131,072). Its "
       "context is the roster's smallest -- ample for a stateless run of ~2,800 tokens per call, not for stateful arms"),
    _r("openrouter/qwen/qwen3-235b-a22b-2507", "GMICloud",
       "open-weight ($0.061/run; cheapest of ten upstreams, context 262,144)"),
)
TIMED_IN_E8_5 = {"gemini-2.5-flash|thinking0", "gpt-5-mini|default"}
# DECISION_LOG P9-2 (11 Sep 2026): the roster was every candidate that passed its smoke (13).
# DECISION_LOG P9-7 (12 Sep 2026): Claude Fable 5.1 is EXCLUDED from Phase 9 on cost -- at $10 / $50 per M tokens it was
# 57 % of the phase's Anthropic bill for token counts within 2 % of Sonnet 5's.  Its smoke and its 93 pilot runs stay on
# disk and are reported; they size nothing.
# DECISION_LOG P9-8 (12 Sep 2026): the phase has one budget, $300 of OpenRouter credit, and no Anthropic credit.  Claude
# Sonnet 5 ($496 to finish its pilot) and Claude Opus 5 ($1,293) are dropped; the direct-API Haiku configuration is
# replaced by the OpenRouter route the grid will run.  Every dropped configuration's runs are reported and size nothing.
EXCLUDED = ("claude-fable-5-1|default", "claude-sonnet-5|default", "claude-opus-5|default",
            "claude-haiku-4-5-20251001|default")
ROSTER = tuple(c.key for c in CANDIDATES if c.key not in EXCLUDED)
# the configurations whose band-MAS sigma_d was measured in the grid's configuration on the grid's four scenarios (E8.5,
# P8-16); every other roster member is piloted (PREREG_PHASE_9.md 2).  GPT-5 mini's E8.5 transfer ran on one scenario only
MEASURED_IN_GRID_CONFIG = {"gemini-2.5-flash|thinking0"}


def by_key(key: str) -> ModelConfig:
    for c in CANDIDATES:
        if c.key == key or (c.model == key and sum(1 for d in CANDIDATES if d.model == key) == 1):
            return c
    raise KeyError(f"no candidate configuration {key!r}; known: {[c.key for c in CANDIDATES]}")


def make_client(mc: ModelConfig, max_retries: int = 8):
    """The provider client with the configuration's options, the client's own retry-with-backoff raised as in E8.5
    (a transient 429 is absorbed before the agent's three attempts make it a fallback)."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
    temp = {} if mc.temperature is None else {"temperature": mc.temperature}
    if mc.provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=mc.model, google_api_key=os.getenv("GOOGLE_API_KEY"), max_retries=max_retries,
                                      **temp, **mc.options)
    if mc.provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=mc.model, api_key=os.getenv("OPENAI_API_KEY"), max_retries=max_retries, **temp, **mc.options)
    if mc.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=mc.model, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"), max_retries=max_retries,
                             **temp, **mc.options)
    if mc.provider == "openrouter":
        # P9-8: one key, one pinned upstream.  `allow_fallbacks: false` makes an unavailable upstream FAIL rather than
        # be re-routed silently, so no run is served by a backend the configuration did not name (addendum 6).
        from langchain_openai import ChatOpenAI
        if not mc.upstream:
            raise ValueError(f"{mc.key}: an OpenRouter configuration must name its upstream (addendum 6)")
        # PREREG_PHASE_9_ADDENDUM.md 7: OpenRouter reads an absent max_tokens as the model's FULL context window, and
        # the upstream then rejects the request as exceeding its own context (Qwen3 235B failed all 400 smoke calls
        # that way).  8,192 is 2.6x the largest mean output per call ever observed on this harness (3,097 tokens,
        # GPT-5 nano) and far below every roster model's context.  The first-party routes still send no cap.
        return ChatOpenAI(model=mc.model[len("openrouter/"):], api_key=os.getenv("OPENROUTER_API_KEY"),
                          base_url="https://openrouter.ai/api/v1", max_retries=max_retries,
                          max_tokens=OPENROUTER_MAX_TOKENS,
                          extra_body={"provider": {"order": [mc.upstream], "allow_fallbacks": False}},
                          **temp, **mc.options)
    raise ValueError(f"unknown provider {mc.provider!r}")


def provider_options_record(mc: ModelConfig, client) -> Dict[str, Any]:
    """What goes into `RunConfig.provider_options` and every row's `Provider_Options` column."""
    return {"provider": mc.provider, "model": mc.model, "config_tag": mc.config_tag,
            "temperature_sent": mc.temperature, "temperature_client": getattr(client, "temperature", None),
            "options": dict(mc.options), "max_tokens_client": getattr(client, "max_tokens", None),
            "max_retries": getattr(client, "max_retries", None),
            "upstream_pinned": mc.upstream,          # None off OpenRouter; the only backend allowed to serve the run
            "base_url": str(getattr(client, "openai_api_base", None) or "") or None}


def price(model: str):
    return PRICES_READ.get(model)
