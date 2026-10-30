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


def _v(model, basis, temperature=HARNESS_TEMPERATURE, tag="default", options=None):
    """Open weights served by our own vLLM on HiPerGator: no key, no price, no upstream to pin."""
    return ModelConfig(model, "vllm", tag, temperature, dict(options or {}), basis)


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
    # DeepSeek's newest official release (10 Sep 2026), and the first on its Causal Encoder-Decoder architecture
    # (763B total, 510 GB), so it is a generational step within one lab against the V4 Flash already piloted.
    # Named by its version, never by the undated V4 Flash name: from 10 Sep DeepSeek's own API silently routes that
    # name to V4.1.  (Our V4 Flash pilot is unaffected -- OpenRouter's records show every sampled generation served
    # as deepseek-v4-flash-20260423 by Baidu.)  Upstream by the registered rule, read 19 Sep 2026: DeepInfra is the
    # cheapest of 21 at our measured token profile and serves fp8, so the rule does not select a 4-bit upstream here.
    _r("openrouter/deepseek/deepseek-v4.1-flash", "DeepInfra",
       "open-weight ($0.100/run at DeepInfra, fp8; cheapest of 21 upstreams, context 1,048,576)"),
    # Served on HiPerGator's own GPUs (fire-finai, RTX PRO 6000 Blackwell 96 GB) rather than bought by the token.
    # Apache-2.0, 30.7B dense, 59 GB in BF16, so it fits one GPU with room for the KV cache; vLLM 0.29.0 loaded and
    # served it in the E9.2 smoke.  Pinned by Hugging Face revision, which is the strongest reproducibility guarantee
    # on the roster: unlike every hosted route, these exact weights can be re-served byte-for-byte.
    _v("vllm/google/gemma-4-31b-it",
       "open-weight, served locally on fire-finai GPUs (no token cost); pinned to HF revision "
       "842da3794eaa0b77d5f08bae87a17459d91ff475"),
    # The other three that fit one 96 GB GPU in BF16, each from a DIFFERENT lab, so an effect seen across them is not
    # one lab's post-training signature.  All Apache-2.0, all pinned by HF revision.
    _v("vllm/openai/gpt-oss-20b",
       "open-weight (OpenAI, 20.9B, 28 GB), served locally; pinned to HF revision "
       "6cee5e81ee83917806bbde320786a8fb61efebee"),
    _v("vllm/qwen/qwen3.8-27b",
       "open-weight (Alibaba, 27.8B dense, 56 GB), served locally; pinned to HF revision "
       "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"),
    _v("vllm/meta/muse-glimmer-30b",
       "open-weight (Meta, 29.8B dense, 60 GB), served locally; pinned to HF revision "
       "a4e59da52a7bc87ae7251dd5545c0dd437c44b68"),
    # The Gemma 4 SCALE LADDER.  Every other open configuration sits at 20-31B, so model size and model family are
    # confounded: a difference between two of them could be either.  These two hold the lab, the training recipe and
    # the tokenizer fixed and vary only size against gemma-4-31b-it, which makes capability a factor we can read.
    _v("vllm/google/gemma-4-12b-it",
       "open-weight (Google, 12.0B dense, 24 GB), served locally; the ladder's middle rung against gemma-4-31b-it; "
       "pinned to HF revision 707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7"),
    _v("vllm/google/gemma-4-e4b-it",
       "open-weight (Google, 8.0B dense, 16 GB), served locally; the ladder's bottom rung against gemma-4-31b-it; "
       "pinned to HF revision ee0ef6023621cff504d758262d4e04895a5af4a2"),
    # DECISION_LOG P9-12 (24 Oct 2026): the headline runs first on open weights served on the FinAI HiPerGator
    # allocation, whose policy forbids models developed by Chinese organisations on the cluster.  One configuration per
    # lab -- Google, OpenAI, Meta, AI2, Mistral -- plus gemma-4-e4b-it as the within-lab size contrast.  These three join
    # the roster for that run; each is Apache-2.0, fits one B200, and is pinned by Hugging Face revision.
    # DECISION_LOG P9-13 (24 Oct 2026): OpenAI's configuration in that headline is gpt-oss-20b.  gpt-oss-120b was piloted
    # and is no quieter (band-MAS sigma_d limit 0.1496 against 0.1364, F-test p = 0.58), so it stays here as a pilot.
    _v("vllm/openai/gpt-oss-120b",
       "open-weight (OpenAI, 116.8B MoE with 5.1B active, MXFP4, 65 GB), served locally; piloted 24 Oct 2026 and not "
       "in the headline (DECISION_LOG P9-13); pinned to HF revision b5c939de8f754692c1647ca79fbf85e8c1e70f8a"),
    _v("vllm/allenai/olmo-3.1-32b-instruct",
       "open-weight (AI2, 32.2B dense, 64 GB, training data released), served locally; pinned to HF revision "
       "ac0587e4a7744a551c059d8cd17ba220bc940dae"),
    _v("vllm/mistralai/ministral-3-14b-instruct-2512",
       "open-weight (Mistral, 13.9B dense, the BF16 release mistralai/Ministral-3-14B-Instruct-2512-BF16, 28 GB), "
       "served locally; pinned to HF revision 3cea74c1ebaf5ce5f5a2553de470e2ceab825142"),
    # DECISION_LOG P9-17 (26 Oct 2026): the second stage-1 batch, the open models comparable published studies run --
    # Llama 3.1 at 8B and 70B, the pair most of them use, and Microsoft's Phi-4 (Cook et al., FEDS 2026-006).  Llama 3.1
    # is gated, so its files come from NousResearch's open copy, equal to Meta's on every weight shard, config and
    # tokenizer file, with Meta's own tokenizer_config.json (the current chat template) put back; the pin is Meta's.
    _v("vllm/meta-llama/llama-3.1-8b-instruct",
       "open-weight (Meta, 8.0B dense, 16 GB, Llama 3.1 Community License), served locally; pinned to Meta's HF revision "
       "0e9e39f249a16976918f6564b8830bc894c89659, files from NousResearch/Meta-Llama-3.1-8B-Instruct@d10aef7 with "
       "Meta's tokenizer_config.json"),
    _v("vllm/meta-llama/llama-3.1-70b-instruct",
       "open-weight (Meta, 70.6B dense, 141 GB, Llama 3.1 Community License), served locally; pinned to Meta's HF "
       "revision 1605565b47bb9346c5515c34102e054115b4f98b, files from NousResearch/Meta-Llama-3.1-70B-Instruct@d50656e "
       "with Meta's tokenizer_config.json"),
    _v("vllm/microsoft/phi-4",
       "open-weight (Microsoft, 14.7B dense, 29 GB, MIT, a 16,384-token context), served locally; pinned to HF revision "
       "2db69c1c3e91a05d2c64a3185acfbaf36f744e25"),
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
# DECISION_LOG P9-12, P9-13, P9-14 (24 Oct 2026): the open-weight headline, one configuration per lab plus Gemma 4 E4B as
# the size contrast.  Sized over these six only (`e9_2_pilot --stages open`); its manifest is
# e9_4/manifest_headline_open.json, registered in PREREG_PHASE_9_STAGE1_OPEN.md.
HEADLINE_OPEN = ("vllm/google/gemma-4-31b-it|default", "vllm/google/gemma-4-e4b-it|default",
                 "vllm/openai/gpt-oss-20b|default", "vllm/meta/muse-glimmer-30b|default",
                 "vllm/allenai/olmo-3.1-32b-instruct|default", "vllm/mistralai/ministral-3-14b-instruct-2512|default")
# DECISION_LOG P9-17 (26 Oct 2026): the second batch, analysed as the six are, each model its own family.
HEADLINE_OPEN_B2 = ("vllm/meta-llama/llama-3.1-8b-instruct|default", "vllm/meta-llama/llama-3.1-70b-instruct|default",
                    "vllm/microsoft/phi-4|default")

# ---------------------------------------------------------------------------------------- stage 2 (E2-E5)
# `HEADLINE_MODEL_SELECTION.md` section 4.3, from the rule `e9_4/selection/CRITERIA.md` as `tools/phase9/e9_4_select.py`
# implements it: the core is the size-6 subset of the nine with the smallest coverage loss (0.0395), the same six in
# 200 of 200 path-bootstrap draws.  Muse Glimmer 30B and Llama 3.1 70B are out -- each has its nearest neighbour inside
# the core, and they are two of the three most expensive per run (0.0172 and 0.0076 GPU-hours against 0.0009-0.0037).
CORE_OPEN = ("vllm/google/gemma-4-e4b-it|default", "vllm/openai/gpt-oss-20b|default",
             "vllm/allenai/olmo-3.1-32b-instruct|default", "vllm/mistralai/ministral-3-14b-instruct-2512|default",
             "vllm/meta-llama/llama-3.1-8b-instruct|default", "vllm/microsoft/phi-4|default")
# E2 and E3 need an effect to decompose (R_effect).  gpt-oss-20b's POOLED band-MAS CI includes 0 -- its cells cancel,
# 7 of 12 excluding 0 with opposite signs -- so it is pruned, and the rule's top-up is the excluded model that covers
# the nine best: Gemma 4 31B, which is also the model whose ENTJ cells most show re-injection WORSENING adherence
# (3 of 4 positive and significant), so E2 and E3 keep that sign in view.
CAUSAL_OPEN = tuple(k for k in CORE_OPEN if k != "vllm/openai/gpt-oss-20b|default") + ("vllm/google/gemma-4-31b-it|default",)


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
    if mc.provider == "vllm":
        # Open weights served by our own vLLM on HiPerGator (OpenAI-compatible API).  There is no key and no price:
        # the run costs GPU hours, not tokens, so it logs its tokens and no dollar figure, exactly as an unpriced
        # first-party configuration does.  There is no upstream to pin either -- the weights ARE the pin, by their
        # Hugging Face revision, which is recorded in `options` and reproduces the server exactly.  `VLLM_BASE_URL`
        # names the server; a run against an absent server FAILS rather than falling back to any hosted route.
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=mc.model[len("vllm/"):], api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
                          base_url=os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1"),
                          max_retries=max_retries, **temp, **mc.options)
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
