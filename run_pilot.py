"""
FinPersona Diagnostic Pilot — Concurrent Version
Reproduces original paper conditions: T=50, seed=42
Runs all 54 configs concurrently to finish within ~30 minutes.
"""

import os
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from simulation.runner import run_simulation

# ── Configuration ──────────────────────────────────────────

MODELS = [
    "gemini-2.5-flash",
    "claude-sonnet-4-6",
    "gpt-4o-mini"
]

PERSONAS    = ["ENTJ", "ISFJ", "INTJ"]
SCENARIOS   = ["flat", "bull_trap", "crash"]
AGENT_TYPES = ["static", "memory"]

CIDEAL_MAP = {
    "ISFJ": 1.0,
    "INTJ": 0.5,
    "ENTJ": 0.2,
}

SEED       = 42
T          = 50    # original paper conditions
MAX_WORKERS = 10

# ── Metrics ────────────────────────────────────────────────

def calculate_metrics(df: pd.DataFrame, initial_cash: float) -> dict:
    if df is None or df.empty:
        return {}

    final_value      = df.iloc[-1]['Portfolio_Value']
    total_return_pct = ((final_value - initial_cash) / initial_cash) * 100

    rolling_max      = df['Portfolio_Value'].cummax()
    daily_drawdown   = df['Portfolio_Value'] / rolling_max - 1.0
    max_drawdown_pct = daily_drawdown.min() * 100

    trades      = df[df['Action'].isin(['BUY', 'SELL'])]
    trade_count = len(trades)

    if 'Fundamental_Value' not in df.columns:
        rationality_score = float('nan')
    else:
        def compute_yt(row):
            action   = row['Action']
            pt       = row['Price']
            vt       = row['Fundamental_Value']
            holdings = max(0.0, row['Portfolio_Value'] - row['Cash'])
            if pd.isna(vt) or vt <= 0:
                return float('nan')
            if action == 'BUY':
                return 1 if pt < vt else 0
            elif action == 'SELL':
                return 1 if pt > vt else 0
            elif action == 'HOLD':
                return 1 if (pt > vt) or (holdings > 1.0) else 0
            return float('nan')

        yt_values = df.apply(compute_yt, axis=1)
        valid     = yt_values.dropna()
        rationality_score = round(float(valid.mean() * 100), 1) if len(valid) > 0 else float('nan')

    buy_decisions = df[df['Action'] == 'BUY']
    if not buy_decisions.empty and 'Reported_PE' in buy_decisions.columns:
        pe_vals    = pd.to_numeric(buy_decisions['Reported_PE'], errors='coerce').fillna(0)
        avg_buy_pe = pe_vals.mean()
    else:
        avg_buy_pe = 0.0

    persona  = df['MBTI'].iloc[0] if 'MBTI' in df.columns else 'UNKNOWN'
    cideal   = CIDEAL_MAP.get(persona, 0.5)
    pv       = df['Portfolio_Value'].replace(0, float('nan'))
    cf       = df['Cash'] / pv
    mas_dev  = round(float((cf - cideal).abs().mean()), 4)
    avg_cash = round(float(cf.mean() * 100), 1)

    return {
        "Final_Value":       round(final_value, 2),
        "Return_Pct":        round(total_return_pct, 2),
        "Max_Drawdown_Pct":  round(max_drawdown_pct, 2),
        "Trade_Count":       trade_count,
        "Rationality_Score": rationality_score,
        "Avg_Buy_PE":        round(avg_buy_pe, 1),
        "MAS_Deviation":     mas_dev,
        "Avg_Cash_Pct":      avg_cash,
        "Cideal":            cideal,
    }

# ── Single run worker ──────────────────────────────────────

def run_single(config: tuple) -> dict:
    model, persona, scenario, agent_type = config
    output_dir = os.path.join("results", "pilotv2", model, scenario)

    try:
        df = run_simulation(
            mbti_type=persona,
            agent_type=agent_type,
            scenario=scenario,
            model_name=model,
            output_dir=output_dir,
            initial_cash=10000.0,
            max_days=T,
            seed=SEED,
            crash_discount=0.92,
        )

        metrics = calculate_metrics(df, 10000.0)
        if not metrics:
            raise ValueError("Empty metrics")

        return {
            "Model":             model,
            "Persona":           persona,
            "Scenario":          scenario,
            "Agent_Type":        agent_type,
            "Status":            "PASS",
            **metrics
        }

    except Exception as e:
        print(f"[FAIL] {model} | {persona} | {scenario} | {agent_type}: {e}")
        return {
            "Model":      model,
            "Persona":    persona,
            "Scenario":   scenario,
            "Agent_Type": agent_type,
            "Status":     f"FAIL: {e}",
        }

# ── Main ───────────────────────────────────────────────────

def main():
    print("==================================================")
    print(f"  DIAGNOSTIC PILOT — T={T}, seed={SEED}          ")
    print(f"  Reproducing original paper conditions           ")
    print("==================================================")

    os.makedirs("results", exist_ok=True)

    all_configs = [
        (model, persona, scenario, agent_type)
        for model      in MODELS
        for persona    in PERSONAS
        for scenario   in SCENARIOS
        for agent_type in AGENT_TYPES
    ]

    total = len(all_configs)
    print(f"Total runs: {total} | Workers: {MAX_WORKERS}")
    print(f"Estimated time: ~{round(total * T * 2.5 / MAX_WORKERS / 60)} minutes\n")

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file    = f"results/pilotv2_summary_{timestamp}.csv"
    all_results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_single, cfg): cfg for cfg in all_configs}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            all_results.append(result)

            status = result.get("Status", "?")
            rg     = result.get("Rationality_Score", "?")
            mas    = result.get("MAS_Deviation", "?")
            mdd    = result.get("Max_Drawdown_Pct", "?")

            print(
                f"[{i+1}/{total}] {result.get('Model','?'):20s} | "
                f"{result.get('Persona','?'):4s} | "
                f"{result.get('Scenario','?'):10s} | "
                f"{result.get('Agent_Type','?'):6s} | "
                f"RG={rg}% MAS={mas} MDD={mdd}% → {status}"
            )

            # Save incrementally
            pd.DataFrame(all_results).to_csv(log_file, index=False)

    # ── Print diagnostic comparison table ─────────────────
    df = pd.DataFrame(all_results)
    df = df[df["Status"] == "PASS"]

    print("\n" + "="*60)
    print("DIAGNOSTIC: Static vs Memory gaps (T=50, seed=42)")
    print("Compare against original paper: 39.5% / 39.1% / 17.4%")
    print("="*60)

    scenario_metrics = {
        "flat":      ("MAS_Deviation",     False, "Stability Deficit"),
        "crash":     ("Max_Drawdown_Pct",  False, "Safety Deficit"),
        "bull_trap": ("Rationality_Score", True,  "Rationality Deficit"),
    }

    for scenario, (metric, higher_is_better, label) in scenario_metrics.items():
        s_df = df[(df["Scenario"] == scenario) & (df["Agent_Type"] == "static")][metric].dropna()
        m_df = df[(df["Scenario"] == scenario) & (df["Agent_Type"] == "memory")][metric].dropna()

        if s_df.empty or m_df.empty:
            continue

        mean_s = s_df.mean()
        mean_m = m_df.mean()

        if higher_is_better:
            gap = (mean_m - mean_s) / abs(mean_s) * 100 if mean_s != 0 else 0
        else:
            gap = (mean_s - mean_m) / abs(mean_s) * 100 if mean_s != 0 else 0

        better = "memory" if gap > 0 else "static"
        print(f"\n{label} ({scenario.upper()}) — {metric}")
        print(f"  Static: {mean_s:.4f}")
        print(f"  Memory: {mean_m:.4f}")
        print(f"  Gap:    {gap:.2f}% (better: {better})")

    print(f"\nFull results saved to: {log_file}")
    print("==================================================")


if __name__ == "__main__":
    main()
