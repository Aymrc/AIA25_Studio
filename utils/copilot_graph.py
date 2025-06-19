from pydantic import BaseModel
from typing import Optional, Dict, Any

class CopilotState(BaseModel):
    user_input: str
    design_data: Dict[str, Any]
    intent: Optional[str] = None
    llm_response: Optional[str] = None



from llm_calls import (
    suggest_change,
    suggest_improvements,
    answer_user_query
)
from utils.embeddings import classify_intent_via_embeddings

def classify_input_fn(state: CopilotState) -> CopilotState:
    intent, _ = classify_intent_via_embeddings(state.user_input)
    state.intent = intent
    return state

def suggest_change_fn(state: CopilotState) -> CopilotState:
    state.llm_response = suggest_change(state.user_input, state.design_data)
    return state

def suggest_improvements_fn(state: CopilotState) -> CopilotState:
    state.llm_response = suggest_improvements(state.user_input, state.design_data)
    return state

def answer_query_fn(state: CopilotState) -> CopilotState:
    state.llm_response = answer_user_query(state.user_input, state.design_data)
    return state



from langgraph.graph import StateGraph

def build_copilot_graph():
    g = StateGraph(CopilotState)

    g.add_node("classify_input", classify_input_fn)
    g.add_node("handle_design_change", suggest_change_fn)
    g.add_node("suggest_improvement", suggest_improvements_fn)
    g.add_node("answer_query", answer_query_fn)

    g.set_entry_point("classify_input")

    g.add_conditional_edges(
        "classify_input",
        lambda state: state.intent,
        {
            "design_change": "handle_design_change",
            "improvement_suggestion": "suggest_improvement",
            "carbon_query": "answer_query",
            "general_query": "answer_query"  # ← AÑADE ESTO
        }
    )


    # Fin del flujo
    g.add_edge("handle_design_change", "__end__")
    g.add_edge("suggest_improvement", "__end__")
    g.add_edge("answer_query", "__end__")

    return g.compile()
