"""
Schemas Module

This module defines the strict data structures (schemas) for the agent's output.
It acts as a contract/interface between the LLM and the execution engine.
"""

from pydantic import BaseModel, Field
from typing import Literal


class TradeDecision(BaseModel):
    """
    Represents a single trading decision made by an agent.

    The LLM must populate this structure exactly.
    """

    action: Literal["BUY", "SELL", "HOLD"] = Field(
        ...,
        description="The action to take. BUY to enter/add, SELL to exit/reduce, "
        "HOLD to do nothing.",
    )

    quantity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The quantity to trade expressed as a percentage (0.0 to 1.0). "
        "For BUY: % of available cash. For SELL: % of current holdings. "
        "REQUIRED: If action is HOLD, you MUST set this to 0.0.",
    )

    rationale: str = Field(
        ...,
        description="A concise explanation (max 2-3 sentences) linking the "
        "decision to the agent's personality and the current market indicators. "
        "REQUIRED: You MUST provide a reason even if the decision is HOLD.",
    )


class TargetAllocation(BaseModel):
    """
    v2 action (plan 2.1 block 9; decision 5): the agent states the cash share it
    wants to hold after today's trade. The harness trades the difference, charges
    cost on the traded value, and derives BUY/SELL/HOLD labels with a 1-point
    dead band for scoring. For N > 1 assets, `target_weights` are the risky
    sleeve weights (sum to 1); the cash share is `target_cash_share`.
    """

    target_cash_share: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The fraction of the portfolio to hold in cash after today's trade (0.0 = fully invested, "
        "1.0 = all cash). Stating your current cash share means no trade.",
    )

    target_weights: list[float] | None = Field(
        default=None,
        description="Multi-asset only: weights of the risky sleeve across assets (must sum to 1). Omit for one asset.",
    )

    rationale: str = Field(
        ...,
        description="A concise explanation (max 2-3 sentences) linking the target allocation to your mandate and "
        "the current market observation.",
    )
