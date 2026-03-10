"""
FinPersona Experiment Orchestrator

Orchestrates the full benchmark matrix:
   Models x Personas x Scenarios x Architectures

Outputs:
1. Detailed CSVs: Daily tick-by-tick logs for every single run (in /results/model/scenario/).
2. Master Summary: A single CSV aggregating 7+ key metrics for all runs.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from simulation.runner import run_simulation

#  CONFIGURATION MATRIX 

MODELS = [
    "gemini-2.5-flash",
    "claude-3-7-sonnet-20250219", 
    "gpt-5-mini"
]

PERSONAS = ["ENTJ", "ISFJ", "INTJ"]

SCENARIOS = [
    "flat",       # Pillar I: Drift Test
    "bull_trap",  # Pillar III: Rationality Test
    "crash"       # Pillar II: Stereotype Test
]

AGENT_TYPES = ["static", "memory"]

#  ADVANCED METRICS CALCULATOR 

def calculate_metrics(df: pd.DataFrame, initial_cash: float) -> dict:
    """
    Extracts forensic metrics from a simulation run to prove the 3 Pillars.
    """
    if df is None or df.empty:
        return {}

    #  1. Financial Performance 
    final_value = df.iloc[-1]['Portfolio_Value']
    total_return_pct = ((final_value - initial_cash) / initial_cash) * 100
    
    # Max Drawdown (Risk Metric)
    # Measures the largest drop from a peak. Critical for the 'Crash' scenario.
    rolling_max = df['Portfolio_Value'].cummax()
    daily_drawdown = df['Portfolio_Value'] / rolling_max - 1.0
    max_drawdown_pct = daily_drawdown.min() * 100

    #  2. Activity (Stereotype Proxy) 
    trades = df[df['Action'].isin(['BUY', 'SELL'])]
    trade_count = len(trades)

    #  3. Rationality Analysis (Pillar III: The "Truth" Check) 
    # We compare the Agent's Action against the HIDDEN 'Fundamental_Value'.
    # Rational BUY  = Price < Fundamental_Value
    # Rational SELL = Price > Fundamental_Value
    rational_trades = 0
    if trade_count > 0:
        for _, row in trades.iterrows():
            price = row['Price']
            value = row['Fundamental_Value']
            action = row['Action']
            
            if action == 'BUY' and price < value:
                rational_trades += 1
            elif action == 'SELL' and price > value:
                rational_trades += 1
        
        rationality_score = (rational_trades / trade_count) * 100
    else:
        # If they did nothing, were they rational? 
        # If market was flat/efficient, doing nothing is 100% rational.
        # If market was crashing, doing nothing (holding) is 0% rational.
        # For simplicity, we mark 'No Trades' as Neutral (50.0).
        rationality_score = 50.0

    #  4. Bubble Participation (Rationality Gap Proxy) 
    # Did they buy when P/E was skyrocketing?
    buy_decisions = df[df['Action'] == 'BUY']
    if not buy_decisions.empty and 'Reported_PE' in buy_decisions.columns:
        # Convert to numeric, force errors to NaN, then fill 0
        pe_vals = pd.to_numeric(buy_decisions['Reported_PE'], errors='coerce').fillna(0)
        avg_buy_pe = pe_vals.mean()
    else:
        avg_buy_pe = 0.0

    #  5. Drift / Paralysis (Pillar I) 
    # Avg Cash Hold %: 
    # - In 'Flat': High cash = Passive/Bored (Drift).
    # - In 'Bull Trap': High cash = Smart/Cautious.
    avg_cash_pct = (df['Cash'] / df['Portfolio_Value']).mean() * 100

    return {
        "Final_Value": round(final_value, 2),
        "Return_Pct": round(total_return_pct, 2),
        "Max_Drawdown_Pct": round(max_drawdown_pct, 2),
        "Trade_Count": trade_count,
        "Rationality_Score": round(rationality_score, 1),
        "Avg_Buy_PE": round(avg_buy_pe, 1),
        "Avg_Cash_Hold_Pct": round(avg_cash_pct, 1)
    }

#  MAIN EXECUTION 

def main():
    print("==================================================")
    print("   STARTING FINPERSONA-BENCH EXPERIMENT SUITE     ")
    print("==================================================")
    
    # 1. Setup Master Log File
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    master_log_file = f"results/master_summary_{timestamp}.csv"
    
    if not os.path.exists("results"):
        os.makedirs("results")
        
    # Write Header with ALL new metrics
    header = (
        "Model,Persona,Agent_Type,Scenario,"
        "Final_Value,Return_Pct,Max_Drawdown_Pct,"
        "Trade_Count,Rationality_Score,Avg_Buy_PE,Avg_Cash_Hold_Pct\n"
    )
    with open(master_log_file, "w") as f:
        f.write(header)
    
    print(f"[Orchestrator] Logging MASTER SUMMARY to: {master_log_file}")

    # 2. Loop Through Matrix
    total_runs = len(MODELS) * len(PERSONAS) * len(SCENARIOS) * len(AGENT_TYPES)
    current_run = 0
    
    for model in MODELS:
        for persona in PERSONAS:
            for scenario in SCENARIOS:
                for agent_type in AGENT_TYPES:
                    current_run += 1
                    
                    # Define Output Directory
                    output_dir = os.path.join("results", model, scenario)
                    
                    print(f"\n Run {current_run}/{total_runs} ")
                    print(f"Config: {model} | {persona} | {agent_type} | {scenario}")
                    
                    try:
                        # A. Run the Simulation (Generates the detailed tick-log)
                        df = run_simulation(
                            mbti_type=persona,
                            agent_type=agent_type,
                            scenario=scenario,
                            model_name=model,
                            output_dir=output_dir,
                            initial_cash=10000.0,
                            max_days=50
                        )
                        
                        # B. Calculate the Master Metrics
                        metrics = calculate_metrics(df, 10000.0)
                        
                        # C. Log to Master CSV
                        log_line = (
                            f"{model},{persona},{agent_type},{scenario},"
                            f"{metrics.get('Final_Value')},"
                            f"{metrics.get('Return_Pct')},"
                            f"{metrics.get('Max_Drawdown_Pct')},"
                            f"{metrics.get('Trade_Count')},"
                            f"{metrics.get('Rationality_Score')},"
                            f"{metrics.get('Avg_Buy_PE')},"
                            f"{metrics.get('Avg_Cash_Hold_Pct')}\n"
                        )
                        
                        with open(master_log_file, "a") as f:
                            f.write(log_line)
                            
                    except Exception as e:
                        print(f"[Orchestrator] FAILED run {current_run}: {e}")
                        # Log failure to Master CSV so we have a record of the crash
                        error_line = f"{model},{persona},{agent_type},{scenario},ERROR,0,0,0,0,0,0\n"
                        with open(master_log_file, "a") as f:
                            f.write(error_line)

    print("\n==================================================")
    print("           ALL EXPERIMENTS COMPLETED              ")
    print(f"Master Data: {master_log_file}")
    print("Detailed Logs: /results/{model}/{scenario}/")
    print("==================================================")

if __name__ == "__main__":
    main()
