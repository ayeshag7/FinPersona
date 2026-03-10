"""
FinPersona PILOT RUN (Smoke Test)
"""

import os
import pandas as pd
from datetime import datetime
from simulation.runner import run_simulation

#  PILOT CONFIGURATION 

MODELS = [
    "gemini-2.5-flash",
    "claude-3-7-sonnet-20250219", 
    "gpt-5-mini"
]

PERSONAS = ["ENTJ"]
SCENARIOS = ["bull_trap"]
AGENT_TYPES = ["static", "memory"]

# Increase days to ensure the Environment math works
# (The Bull Trap logic needs at least ~10 days to generate phases)
PILOT_DAYS = 15

def quick_metrics(df, initial_cash):
    if df is None or df.empty: 
        return None  # Return None to signal failure
    
    final_val = df.iloc[-1]['Portfolio_Value']
    trade_counts = len(df[df['Action'].isin(['BUY', 'SELL'])])
    
    return {
        "Final_Value": round(final_val, 2),
        "Trade_Count": trade_counts
    }

def main():
    print("==================================================")
    print(f"   STARTING PILOT RUN ({PILOT_DAYS} Days)        ")
    print("==================================================")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pilot_log_file = f"results/pilot_summary_{timestamp}.csv"
    
    if not os.path.exists("results"):
        os.makedirs("results")
        
    with open(pilot_log_file, "w") as f:
        f.write("Model,Persona,Agent_Type,Status,Final_Value,Trade_Count\n")

    for model in MODELS:
        for persona in PERSONAS:
            for scenario in SCENARIOS:
                for agent_type in AGENT_TYPES:
                    
                    print(f"\n Testing: {model} | {agent_type} ")
                    
                    try:
                        # Create specific pilot directory
                        output_dir = os.path.join("results", "pilot", model)
                        
                        df = run_simulation(
                            mbti_type=persona,
                            agent_type=agent_type,
                            scenario=scenario,
                            model_name=model,
                            output_dir=output_dir,
                            initial_cash=10000.0,
                            max_days=PILOT_DAYS 
                        )
                        
                        metrics = quick_metrics(df, 10000.0)
                        
                        # Explicitly check if metrics exist
                        if metrics is None:
                            raise ValueError("Simulation returned NO data (Environment Crash)")
                        
                        # Log Success
                        with open(pilot_log_file, "a") as f:
                            f.write(f"{model},{persona},{agent_type},PASS,{metrics['Final_Value']},{metrics['Trade_Count']}\n")
                        print(f"PASS: {model}")
                        
                    except Exception as e:
                        # Log Failure
                        print(f"FAIL: {model} - {e}")
                        with open(pilot_log_file, "a") as f:
                            f.write(f"{model},{persona},{agent_type},FAIL,0,0\n")

    print("\n==================================================")
    print("             PILOT COMPLETE                       ")
    print(f"Check results in: {pilot_log_file}")
    print("==================================================")

if __name__ == "__main__":
    main()
