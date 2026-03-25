"""
FinPersona-Bench: Claude-Only Targeted Experiment
===================================================
Runs the full benchmark matrix for Claude Sonnet 4.6 only,
at T=200 with 5 seeds to characterise MSD at longer horizons.

Configuration:
  Model:           claude-sonnet-4-6 only
  Personas:        ENTJ, ISFJ, INTJ
  Scenarios:       flat, bull_trap, crash
  Agent types:     static, memory
  Seeds:           5 (42, 123, 456, 789, 999)
  Crash discounts: 0.85, 0.92, 0.95 (crash only)
  T:               200 trading days

Total runs: 150
Total API calls: 150 x 200 = 30,000
Estimated time: ~2.5 hours with 10 concurrent workers
"""

import os
import threading
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from simulation.runner import run_simulation

# ── Configuration ──────────────────────────────────────────

MODEL           = "claude-sonnet-4-6"
PERSONAS        = ["ENTJ", "ISFJ", "INTJ"]
SCENARIOS       = ["flat", "bull_trap", "crash"]
AGENT_TYPES     = ["static", "memory"]
SEEDS           = [42, 123, 456, 789, 999]
CRASH_DISCOUNTS = [0.85, 0.92, 0.95]
T               = 200
MAX_WORKERS     = 10

CIDEAL_MAP = {
    "ISFJ": 1.0,
    "INTJ": 0.5,
    "ENTJ": 0.2,
}

RESULTS_DIR     = os.path.join("results", "claude_targeted")
CHECKPOINT_FILE = os.path.join(RESULTS_DIR, "checkpoint.txt")

_checkpoint_lock = threading.Lock()

# ── Run ID ─────────────────────────────────────────────────

def make_run_id(persona, agent_type, scenario, seed, crash_discount):
    if scenario == "crash":
        return f"{MODEL}__{persona}__{agent_type}__{scenario}__seed{seed}__discount{crash_discount}"
    return f"{MODEL}__{persona}__{agent_type}__{scenario}__seed{seed}"

# ── Checkpointing ──────────────────────────────────────────

def load_checkpoint() -> set:
    if not os.path.exists(CHECKPOINT_FILE):
        return set()
    with open(CHECKPOINT_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_checkpoint(run_id: str):
    with _checkpoint_lock:
        with open(CHECKPOINT_FILE, "a") as f:
            f.write(run_id + "\n")

# ── Metrics ────────────────────────────────────────────────

def calculate_metrics(df: pd.DataFrame, initial_cash: float) -> dict:
    if df is None or df.empty:
        return {}

    final_value      = df.iloc[-1]["Portfolio_Value"]
    total_return_pct = ((final_value - initial_cash) / initial_cash) * 100

    rolling_max      = df["Portfolio_Value"].cummax()
    daily_drawdown   = df["Portfolio_Value"] / rolling_max - 1.0
    max_drawdown_pct = daily_drawdown.min() * 100

    trades      = df[df["Action"].isin(["BUY", "SELL"])]
    trade_count = len(trades)

    if "Fundamental_Value" not in df.columns:
        rationality_score = float("nan")
    else:
        def compute_yt(row):
            action   = row["Action"]
            pt       = row["Price"]
            vt       = row["Fundamental_Value"]
            holdings = max(0.0, row["Portfolio_Value"] - row["Cash"])
            if pd.isna(vt) or vt <= 0:
                return float("nan")
            if action == "BUY":
                return 1 if pt < vt else 0
            elif action == "SELL":
                return 1 if pt > vt else 0
            elif action == "HOLD":
                return 1 if (pt > vt) or (holdings > 1.0) else 0
            return float("nan")

        yt_values         = df.apply(compute_yt, axis=1)
        valid             = yt_values.dropna()
        rationality_score = round(float(valid.mean() * 100), 1) if len(valid) > 0 else float("nan")

    persona  = df["MBTI"].iloc[0] if "MBTI" in df.columns else "UNKNOWN"
    cideal   = CIDEAL_MAP.get(persona, 0.5)
    pv       = df["Portfolio_Value"].replace(0, float("nan"))
    cf       = df["Cash"] / pv
    mas_dev  = round(float((cf - cideal).abs().mean()), 4)
    avg_cash = round(float(cf.mean() * 100), 1)

    return {
        "Final_Value":       round(final_value, 2),
        "Return_Pct":        round(total_return_pct, 2),
        "Max_Drawdown_Pct":  round(max_drawdown_pct, 2),
        "Trade_Count":       trade_count,
        "Rationality_Score": rationality_score,
        "MAS_Deviation":     mas_dev,
        "Avg_Cash_Pct":      avg_cash,
        "Cideal":            cideal,
    }

# ── Single run worker ──────────────────────────────────────

def run_single(config: tuple) -> dict:
    persona, agent_type, scenario, seed, crash_discount = config
    run_id = make_run_id(persona, agent_type, scenario, seed, crash_discount)

    if scenario == "crash":
        output_dir = os.path.join(
            RESULTS_DIR, MODEL, scenario,
            f"discount{crash_discount}", f"seed{seed}"
        )
    else:
        output_dir = os.path.join(
            RESULTS_DIR, MODEL, scenario, f"seed{seed}"
        )

    try:
        df = run_simulation(
            mbti_type=persona,
            agent_type=agent_type,
            scenario=scenario,
            model_name=MODEL,
            output_dir=output_dir,
            initial_cash=10000.0,
            max_days=T,
            seed=seed,
            crash_discount=crash_discount,
        )

        if df is None:
            print(f"[FAILED] {run_id}: returned None")
            return {
                "Model": MODEL, "Persona": persona,
                "Agent_Type": agent_type, "Scenario": scenario,
                "Seed": seed, "Crash_Discount": crash_discount,
                "Status": "FAIL: silent_failure"
            }

        metrics = calculate_metrics(df, 10000.0)
        metrics.update({
            "Model":          MODEL,
            "Persona":        persona,
            "Agent_Type":     agent_type,
            "Scenario":       scenario,
            "Seed":           seed,
            "Crash_Discount": crash_discount,
            "T":              T,
            "Status":         "PASS",
        })
        save_checkpoint(run_id)
        return metrics

    except Exception as e:
        print(f"[FAILED] {run_id}: {e}")
        return {
            "Model": MODEL, "Persona": persona,
            "Agent_Type": agent_type, "Scenario": scenario,
            "Seed": seed, "Crash_Discount": crash_discount,
            "Status": f"FAIL: {e}"
        }

# ── Main ───────────────────────────────────────────────────

def main():
    print("="*60)
    print("FinPersona-Bench: Claude-Only Targeted Experiment")
    print(f"Model: {MODEL} | T={T} | Seeds={SEEDS}")
    print("="*60)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Build all configs
    all_configs = [
        (persona, agent_type, scenario, seed, crash_discount)
        for scenario       in SCENARIOS
        for seed           in SEEDS
        for persona        in PERSONAS
        for agent_type     in AGENT_TYPES
        for crash_discount in (CRASH_DISCOUNTS if scenario == "crash" else [0.92])
    ]

    # Filter already completed
    completed = load_checkpoint()
    pending = [
        c for c in all_configs
        if make_run_id(*c) not in completed
    ]

    total_api_calls = len(all_configs) * T
    print(f"\nTotal configs:    {len(all_configs)}")
    print(f"Already done:     {len(completed)}")
    print(f"Remaining:        {len(pending)}")
    print(f"Total API calls:  {len(all_configs) * T:,}")
    print(f"Remaining calls:  {len(pending) * T:,}")
    print(f"Est. time:        ~{round(len(pending) * T * 3 / MAX_WORKERS / 3600, 1)} hours")

    if not pending:
        print("\nAll runs already completed.")
        return

    # Run with thread pool
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    master_log = os.path.join(RESULTS_DIR, f"claude_summary_{timestamp}.csv")
    all_results = []

    print(f"\nLogging to: {master_log}")
    print("-"*60)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_single, cfg): cfg for cfg in pending}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            all_results.append(result)

            discount_info = (
                f" | discount={result.get('Crash_Discount')}"
                if result.get("Scenario") == "crash" else ""
            )
            print(
                f"[{i+1}/{len(pending)}] "
                f"{result.get('Persona'):4s} | "
                f"{result.get('Agent_Type'):6s} | "
                f"{result.get('Scenario'):10s}"
                f"{discount_info} | "
                f"seed{result.get('Seed')} → "
                f"{result.get('Status')}"
            )

            # Save incrementally
            pd.DataFrame(all_results).to_csv(master_log, index=False)

    # ── Quick summary ──────────────────────────────────────
    df = pd.DataFrame(all_results)
    df = df[df["Status"] == "PASS"]

    print("\n" + "="*60)
    print(f"RESULTS SUMMARY — Claude Sonnet 4.6 at T={T}")
    print("="*60)

    scenario_metrics = {
        "flat":      ("MAS_Deviation",     False, "Stability (MAS)"),
        "crash":     ("Max_Drawdown_Pct",  False, "Safety (MDD)"),
        "bull_trap": ("Rationality_Score", True,  "Rationality (RG)"),
    }

    # Use default crash discount for summary
    df_main = df[
        (df["Scenario"] != "crash") |
        (df["Crash_Discount"] == 0.92)
    ]

    print(f"\n{'Scenario':<12} {'Metric':<20} {'Static':>10} {'Memory':>10} {'Gap%':>8} {'Direction'}")
    print("-"*70)

    for scenario, (metric, higher_is_better, label) in scenario_metrics.items():
        s_vals = df_main[
            (df_main["Scenario"] == scenario) &
            (df_main["Agent_Type"] == "static")
        ][metric].dropna()

        m_vals = df_main[
            (df_main["Scenario"] == scenario) &
            (df_main["Agent_Type"] == "memory")
        ][metric].dropna()

        if s_vals.empty or m_vals.empty:
            continue

        mean_s = s_vals.mean()
        mean_m = m_vals.mean()

        if higher_is_better:
            gap    = (mean_m - mean_s) / abs(mean_s) * 100 if mean_s != 0 else 0
            better = "memory ✓" if gap > 0 else "static"
        else:
            gap    = (mean_s - mean_m) / abs(mean_s) * 100 if mean_s != 0 else 0
            better = "memory ✓" if gap > 0 else "static"

        print(
            f"{scenario:<12} {label:<20} "
            f"{mean_s:>10.4f} {mean_m:>10.4f} "
            f"{gap:>+8.2f}% {better}"
        )

    print(f"\nFull results: {master_log}")
    print(f"Per-step CSVs: {RESULTS_DIR}/")
    print("="*60)
    print("\nDone. Run analysis/numerical_analysis.py pointing")
    print(f"RESULTS_DIR to '{RESULTS_DIR}' for full statistical analysis.")


if __name__ == "__main__":
    main()
