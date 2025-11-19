"""
Main Execution Script for FinPersona

Run this file to start the simulation.
"""

from simulation.runner import run_simulation

if __name__ == "__main__":
    TARGET_PERSONA = "ENTJ"

    print(f" FinPersona Backtest Initialization: {TARGET_PERSONA} ")

    run_simulation(mbti_type=TARGET_PERSONA, initial_cash=10000.0, max_days=50)
