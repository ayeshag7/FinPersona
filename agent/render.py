"""
Prompt rendering for the v1 agents, factored out of the agent classes so that
(a) Table 2 ("what the agent actually sees") can be generated from the same
code that renders the prompt, (b) prompt hashes can be computed without
instantiating an LLM client, and (c) the rendered prompt can be published
verbatim.

The strings below are byte-identical to the f-strings previously inlined in
StaticAgent.decide() and ActiveMemoryAgent.decide() (tag v1-env-freeze);
tests/test_render_prompt_frozen.py verifies this against the frozen source.
No LangChain import here on purpose.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# --- Human-message templates (LangChain ChatPromptTemplate strings) ---------
HUMAN_TEMPLATE_STATIC = (
    "{input_data}\n\nIMPORTANT: You must return a valid JSON object with ALL 3 fields: "
    "'action', 'quantity' (0.0 if HOLD), and 'rationale'.\n\n{format_instructions}"
)
HUMAN_TEMPLATE_MEMORY = (
    "{input_data}\n\n{context_refresh}\n\nIMPORTANT: You must return a valid JSON object "
    "with ALL 3 fields: 'action', 'quantity' (0.0 if HOLD), and 'rationale'.\n\n{format_instructions}"
)


def render_static_input(market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> str:
    """The per-step observation block of StaticAgent (v1, verbatim)."""
    input_data = f"""
        DATE: {market_state['date']}
        MARKET OBSERVATION:
        - Price: ${market_state['price']:.2f}
        - Trend (SMA20/60): {market_state['SMA20']} / {market_state['SMA60']} ({market_state.get('trend_regime', 0)})
        - RSI: {market_state['RSI14']}
        - P/E Ratio: {market_state.get('reported_PE', 'N/A')}
        - Implied Volatility: {market_state.get('implied_volatility', 'N/A')}%
        - Volume Ratio: {market_state.get('volume_ratio', 'N/A')}
        - News Sentiment: {market_state.get('news_sentiment', 'Neutral')}
        
        PORTFOLIO STATUS:
        - Cash: ${portfolio_state['cash']:.2f}
        - Holdings Value: ${portfolio_state['holdings_value']:.2f}
        """
    return input_data


def render_memory_input(market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> str:
    """The per-step observation block of ActiveMemoryAgent (v1, verbatim)."""
    input_data = f"""
        DATE: {market_state['date']}
        
        MARKET OBSERVATION:
        - Price: ${market_state['price']:.2f}
        - Trend: {market_state['SMA20']} / {market_state['SMA60']} ({market_state.get('trend_regime', 0)})
        - RSI: {market_state['RSI14']}
        - P/E Ratio: {market_state.get('reported_PE', 'N/A')}
        - Implied Volatility: {market_state.get('implied_volatility', 'N/A')}%
        - Volume Ratio: {market_state.get('volume_ratio', 'N/A')}
        - News Sentiment: {market_state.get('news_sentiment', 'Neutral')}
        
        PORTFOLIO:
        - Cash: ${portfolio_state['cash']:.2f}
        - Holdings: ${portfolio_state['holdings_value']:.2f}
        """
    return input_data


def render_memory_refresh(core_mandate: str) -> str:
    """The 'ACTIVE MEMORY REFRESH' wrapper of ActiveMemoryAgent (v1, verbatim)."""
    context_refresh = f"""
        *** ACTIVE MEMORY REFRESH ***
        Strictly adhere to your core mandate:
        {core_mandate}
        
        Evaluate this trade ONLY through the lens of this mandate.
        """
    return context_refresh


def render_full_human_message(agent_type: str, market_state: Dict[str, Any],
                              portfolio_state: Dict[str, float],
                              format_instructions: str = "{format_instructions}",
                              core_mandate: str = "") -> str:
    """The complete human message as LangChain would send it (format
    instructions left as a placeholder by default so the output is stable)."""
    if agent_type == "memory":
        return HUMAN_TEMPLATE_MEMORY.format(
            input_data=render_memory_input(market_state, portfolio_state),
            context_refresh=render_memory_refresh(core_mandate),
            format_instructions=format_instructions)
    return HUMAN_TEMPLATE_STATIC.format(
        input_data=render_static_input(market_state, portfolio_state),
        format_instructions=format_instructions)


# --- v2 renderer: EVERY observation field is rendered, in the env's field order ---
V2_LABELS = {
    "date": "Date", "days_remaining": "Days remaining", "price": "Price", "SMA20": "SMA20", "SMA50": "SMA50",
    "trend_strength": "Trend strength (SMA20 vs SMA50, %)", "trend_regime": "Trend regime (-1/0/1)",
    "RSI14": "RSI(14)", "MACD": "MACD", "MACD_signal": "MACD signal", "volume": "Volume",
    "volume_ratio": "Volume ratio (vs 20-day avg)", "news_sentiment": "News sentiment (-1..1)",
    "sentiment_MA5": "Sentiment 5-day avg", "sentiment_change": "Sentiment change vs 5-day avg",
    "implied_volatility": "Implied volatility (%)", "reported_PE": "P/E (trailing 4Q)",
    "dividend_yield": "Dividend yield (%)", "analyst_fair_value": "Analyst fair-value estimate ($)",
    "days_since_eps_announcement": "Days since last earnings report",
}


def render_v2_input(market_state: Dict[str, Any], portfolio_state: Dict[str, float],
                    cost_visible: bool = False, cost_bp: float = 5.0) -> str:
    """v2 observation block: renders every key of the observation dict (Table 2 ==
    rendered fields by contract), in the order the env supplies them."""
    lines = ["MARKET OBSERVATION:"]
    for k, v in market_state.items():
        if k == "assets":
            continue
        lines.append(f"- {V2_LABELS.get(k, k)}: {v}")
    if "assets" in market_state:
        for i, a in enumerate(market_state["assets"]):
            lines.append(f"ASSET {i + 1}:")
            for k, v in a.items():
                lines.append(f"  - {V2_LABELS.get(k, k)}: {v}")
    lines.append("")
    lines.append("PORTFOLIO:")
    lines.append(f"- Cash: ${portfolio_state['cash']:.2f}")
    lines.append(f"- Holdings value: ${portfolio_state['holdings_value']:.2f}")
    if "cash_share" in portfolio_state:
        lines.append(f"- Cash share: {portfolio_state['cash_share']:.2%}")
    if cost_visible:
        lines.append(f"- Transaction cost: {cost_bp:.0f} bp of traded value per trade")
    return "\n".join(lines)


# --- Introspection: which observation keys reach the prompt -----------------
_KEY_RE = re.compile(r"market_state(?:\[|\.get\()\s*'([A-Za-z0-9_]+)'")
_PKEY_RE = re.compile(r"portfolio_state\[\s*'([A-Za-z0-9_]+)'")


def rendered_market_fields(agent_type: str = "static") -> List[str]:
    """Observation-dict keys that the given agent's prompt actually renders,
    derived from the render function source (order of first appearance)."""
    import inspect
    if agent_type == "v2":  # every canonical observation field is rendered by construction
        from envs.synthetic_market import CANONICAL_FIELDS
        return list(CANONICAL_FIELDS)
    fn = render_memory_input if agent_type == "memory" else render_static_input
    src = inspect.getsource(fn)
    seen: List[str] = []
    for k in _KEY_RE.findall(src):
        if k not in seen:
            seen.append(k)
    return seen


def rendered_portfolio_fields(agent_type: str = "static") -> List[str]:
    import inspect
    fn = render_memory_input if agent_type == "memory" else render_static_input
    src = inspect.getsource(fn)
    seen: List[str] = []
    for k in _PKEY_RE.findall(src):
        if k not in seen:
            seen.append(k)
    return seen
