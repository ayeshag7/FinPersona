import os
import json
import time
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Internal Imports
from agent.base import BaseAgent
from agent.static_agent import StaticAgent
from agent.schemas import TradeDecision
from agent.render import render_memory_input, render_memory_refresh, HUMAN_TEMPLATE_MEMORY

load_dotenv()

class ActiveMemoryAgent(StaticAgent):
    """
    SOTA Agent (ReMemR1 Inspired).
    
    Architecture:
    - Inherits base setup from StaticAgent.
    - Implements 'Periodic Mandate Retrieval' (Pillar I).
    - Injects the Core Mandate into the ACTIVE CONTEXT (User Prompt) 
      before every decision to prevent attention decay.
      
    Hypothesis:
    - This agent will maintain a high Mandate Adherence Score (MAS) 
      and resist drifting into neutrality.
    """

    def __init__(self, mbti_type: str, model_name: str = "gemini-2.0-flash"):
        # Initialize the base StaticAgent to get the LLM and Parser setup
        super().__init__(mbti_type, model_name)
        
        # Load the specific 'Core Mandate' for active injection
        self._load_core_mandate()
        
        # Re-build the chain to accept the extra 'context_refresh' variable
        self._setup_memory_chain()

    def _load_core_mandate(self):
        """
        Loads the short, imperative 'Core Mandate' from the JSON.
        """
        json_path = os.path.join(os.path.dirname(__file__), "personas", "mbti_profiles.json")
        try:
            with open(json_path, 'r') as f:
                profiles = json.load(f)
        except FileNotFoundError:
            profiles = {}
            
        profile = profiles.get(self.mbti_type, profiles.get("DEFAULT", {}))
        
        # This is the "Needle" we inject every step
        self.core_mandate = profile.get("core_mandate", "REMINDER: Act according to your personality.")

    def _setup_memory_chain(self):
        """
        Overwrites the StaticAgent chain with one that accepts 'context_refresh'.
        """
        # We modify the prompt template to include a slot for the mandate injection
        # at the VERY END of the user input (Recency Bias).
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "{persona}"),
            ("human", HUMAN_TEMPLATE_MEMORY)
        ])
        self.human_template = HUMAN_TEMPLATE_MEMORY

        self.chain = self.prompt_template.partial(
            persona=self.full_system_prompt,
            format_instructions=self.parser.get_format_instructions()
        ) | self.llm | self.parser

    def prompt_components(self) -> Dict[str, str]:
        return {"system": self.full_system_prompt, "human": self.human_template,
                "format_instructions": self.parser.get_format_instructions(),
                "mandate": render_memory_refresh(self.core_mandate)}

    def decide(self, market_state: Dict[str, Any], portfolio_state: Dict[str, float]) -> TradeDecision:
        """
        Overrides the decision logic to inject memory.
        """
        # 1. Standard Observation and 2. the "Context Refresh" (Pillar I fix) are
        # rendered in agent/render.py (byte-identical to the v1 inline f-strings; see tests).
        input_data = render_memory_input(market_state, portfolio_state)
        context_refresh = render_memory_refresh(self.core_mandate)

        last_error = None
        for attempt in range(3):
            try:
                return self.chain.invoke({
                    "input_data": input_data,
                    "context_refresh": context_refresh
                })
            except Exception as e:
                last_error = e
                print(f"[{self.get_uid()}] Parse error (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(1)
        return TradeDecision(action="HOLD", quantity=0.0, rationale=f"Error after 3 attempts: {str(last_error)}")
