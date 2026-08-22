"""
E0 guard: agent/render.py must reproduce, byte for byte, the prompt strings
that were inlined in the v1 agents at tag v1-env-freeze. If this test fails,
the prompt hash of new runs no longer matches the prompt used for v1 results.
"""
import re
import subprocess

import pytest

from agent.render import (render_static_input, render_memory_input,
                          render_memory_refresh, rendered_market_fields,
                          rendered_portfolio_fields, HUMAN_TEMPLATE_STATIC,
                          HUMAN_TEMPLATE_MEMORY)

SAMPLE_MARKET = {
    "date": "Day-7", "price": 101.2345, "SMA20": 100.1, "SMA60": 99.9,
    "RSI14": 55.2, "MACD": 0.0123, "volume": 1234567, "volume_ratio": 1.23,
    "news_sentiment": -0.12, "sentiment_MA5": 0.0, "sentiment_change": -0.1,
    "implied_volatility": 17.5, "reported_PE": 15.3, "dividend_yield": 2.61,
    "trend_strength": 0.2, "trend_regime": 0,
}
SAMPLE_PORTFOLIO = {"cash": 5000.0, "holdings_value": 5123.456}


def _frozen_source(path: str) -> str:
    try:
        out = subprocess.run(["git", "show", f"v1-env-freeze:{path}"],
                             capture_output=True, text=True, check=True)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"git tag v1-env-freeze not available: {exc}")
    # Python's tokenizer normalises CRLF source to LF inside string literals.
    return out.stdout.replace("\r\n", "\n")


def _extract_fstring(src: str, var: str) -> str:
    m = re.search(rf'{var} = f"""(.*?)"""', src, flags=re.S)
    assert m, f"{var} f-string not found in frozen source"
    return m.group(1)


def _eval_fstring(body: str, **ns) -> str:
    # Re-evaluate the frozen f-string body with the sample inputs.
    return eval('f"""' + body + '"""', {}, ns)


def test_static_input_matches_frozen_source():
    src = _frozen_source("agent/static_agent.py")
    body = _extract_fstring(src, "input_data")
    expected = _eval_fstring(body, market_state=SAMPLE_MARKET, portfolio_state=SAMPLE_PORTFOLIO)
    assert render_static_input(SAMPLE_MARKET, SAMPLE_PORTFOLIO) == expected
    # the source spells the template with escaped newlines
    assert HUMAN_TEMPLATE_STATIC.replace("\n", "\\n") in src


def test_memory_input_and_refresh_match_frozen_source():
    src = _frozen_source("agent/memory_agent.py")
    body = _extract_fstring(src, "input_data")
    expected = _eval_fstring(body, market_state=SAMPLE_MARKET, portfolio_state=SAMPLE_PORTFOLIO)
    assert render_memory_input(SAMPLE_MARKET, SAMPLE_PORTFOLIO) == expected

    class _Self:
        core_mandate = "REMINDER: test mandate."
    body = _extract_fstring(src, "context_refresh")
    expected = _eval_fstring(body, self=_Self())
    assert render_memory_refresh(_Self.core_mandate) == expected
    assert HUMAN_TEMPLATE_MEMORY.replace("\n", "\\n") in src


def test_rendered_fields_introspection():
    # Fields that reach the prompt in v1 (Table 2 is generated from this).
    assert rendered_market_fields("static") == [
        "date", "price", "SMA20", "SMA60", "trend_regime", "RSI14",
        "reported_PE", "implied_volatility", "volume_ratio", "news_sentiment"]
    assert rendered_market_fields("memory") == rendered_market_fields("static")
    assert rendered_portfolio_fields("static") == ["cash", "holdings_value"]
