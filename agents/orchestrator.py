from typing import Annotated, TypedDict, Sequence, List
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from config import settings
from safety.triage import check_red_flags
from agents.socrates_agent import run_socrates
from agents.ddx_agent import run_ddx
from agents.rxnav_agent import run_rxnav
from agents.evidence_agent import run_evidence
from agents.mental_health_agent import run_mental_health
from agents.translator_agent import run_translator
from db.timeline import add_symptom

# 1. Define State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    answer: str
    citations: List[dict]
    mode: str

# 2. Define the LLM
llm = ChatOpenAI(
    base_url=settings.zen_base_url,
    api_key=settings.zen_api_key,
    model=settings.zen_model,
    temperature=0.2,
)

# 3. Define the router (Basic Chat Abstraction)
async def router_node(state: AgentState):
    prompt = """You are a medical orchestrator. Look at the conversation history.
    Decide which of the following agents should handle the user's latest query:
    - "off_topic": If the query is completely unrelated to healthcare, medicine, wellness, or biology (e.g. web security, coding, general trivia).
    - "mental_health": If the user discusses depression, anxiety, stress, or emotional struggles.
    - "socrates": If the user is describing their own physical symptoms and we need to interview them or diagnose them.
    - "rxnav": If the user is asking specifically about drug interactions between medications.
    - "evidence": If the user is asking a general medical knowledge question (e.g., guidelines, treatments).

    Respond with exactly ONE word: "off_topic", "mental_health", "socrates", "rxnav", or "evidence"."""
    
    messages = list(state["messages"]) + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(messages)
    decision = response.content.strip().lower()
    
    if "off_topic" in decision or "security" in decision or "coding" in decision:
        return {"mode": "off_topic"}
    elif "mental_health" in decision or "depress" in decision or "anxi" in decision:
        return {"mode": "mental_health"}
    elif "socrates" in decision or "diagnos" in decision or "symptom" in decision:
        return {"mode": "socrates"}
    elif "rxnav" in decision or "drug" in decision or "interact" in decision:
        return {"mode": "rxnav"}
    else:
        return {"mode": "evidence"}

# 4. Define Nodes
async def triage_node(state: AgentState):
    latest_msg = state["messages"][-1].content
    triage_result = check_red_flags(latest_msg)
    if triage_result:
        return {"answer": triage_result, "mode": "emergency"}
    return None

async def off_topic_node(state: AgentState):
    return {
        "answer": "I am a medical assistant and can only answer questions related to healthcare, medicine, and wellness. Please ask a health-related question.",
        "messages": [AIMessage(content="I am a medical assistant and can only answer questions related to healthcare, medicine, and wellness. Please ask a health-related question.")],
        "citations": [],
        "mode": "off_topic"
    }

async def socrates_node(state: AgentState):
    result = await run_socrates(state["messages"], llm)
    if result.get("ready_for_ddx"):
        return {"mode": "ddx"}
    return {"answer": result["answer"], "messages": [AIMessage(content=result["answer"])], "citations": []}

async def ddx_node(state: AgentState):
    result = await run_ddx(state["messages"], llm)
    return {"answer": result["answer"], "messages": [AIMessage(content=result["answer"])], "citations": []}

async def rxnav_node(state: AgentState):
    result = await run_rxnav(state["messages"], llm)
    return {"answer": result["answer"], "messages": [AIMessage(content=result["answer"])], "citations": []}

async def evidence_node(state: AgentState):
    result = await run_evidence(state["messages"][-1].content)
    return {"answer": result["answer"], "messages": [AIMessage(content=result["answer"])], "citations": result["citations"]}

async def mental_health_node(state: AgentState):
    result = await run_mental_health(state["messages"], llm)
    return {"answer": result["answer"], "messages": [AIMessage(content=result["answer"])], "citations": [], "mode": "mental_health"}

# 5. Build Graph
graph = StateGraph(AgentState)

graph.add_node("router", router_node)
graph.add_node("off_topic", off_topic_node)
graph.add_node("socrates", socrates_node)
graph.add_node("ddx", ddx_node)
graph.add_node("rxnav", rxnav_node)
graph.add_node("evidence", evidence_node)
graph.add_node("mental_health", mental_health_node)

graph.set_entry_point("router")

def route_next(state: AgentState):
    return state.get("mode", "evidence")

graph.add_conditional_edges(
    "router",
    route_next,
    {
        "off_topic": "off_topic",
        "mental_health": "mental_health",
        "socrates": "socrates",
        "rxnav": "rxnav",
        "evidence": "evidence"
    }
)

def route_after_socrates(state: AgentState):
    return "ddx" if state.get("mode") == "ddx" else END

graph.add_conditional_edges("socrates", route_after_socrates, {"ddx": "ddx", END: END})
graph.add_edge("ddx", END)
graph.add_edge("rxnav", END)
graph.add_edge("evidence", END)
graph.add_edge("mental_health", END)
graph.add_edge("off_topic", END)

from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
orchestrator_app = graph.compile(checkpointer=memory)

async def run_chat(message: str, thread_id: str, language: str = "English"):
    # 1. Triage Check
    triage_msg = check_red_flags(message)
    if triage_msg:
        return triage_msg, [], "emergency"

    # 2. Run graph with state memory
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=message)], "mode": "", "answer": "", "citations": []}
    result = await orchestrator_app.ainvoke(inputs, config=config)
    
    answer = result.get("answer", "No answer generated.")
    mode = result.get("mode", "unknown")
    citations = result.get("citations", [])
    
    # Track symptom if applicable
    if mode in ["socrates", "ddx"]:
        add_symptom(thread_id, message)
    
    # 3. Post-process translation (plain language + multilingual)
    translated_answer = await run_translator(answer, language, llm)
    
    return translated_answer, citations, mode
