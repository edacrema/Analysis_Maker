from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from nodes import news_node, research_node, background_node, complex_systems_node, entropy_node, actor_mapping_node, unified_analysis_node, revision_node, humanitarian_impact_node, game_theory_node, AgentState

builder = StateGraph(AgentState)
checkpointer = SqliteSaver("graph.db")

builder.add_node("background_check", background_node)
builder.add_node("info", news_node)
builder.add_node("unified_analysis", unified_analysis_node)
builder.add_node("complex_systems", complex_systems_node)
builder.add_node("entropy", entropy_node)
builder.add_node("actor_mapping", actor_mapping_node)
builder.add_node("game_theory", game_theory_node)
builder.add_node("revision", revision_node)
builder.add_node("research", research_node)
builder.add_node("humanitarian_impact", humanitarian_impact_node)  

builder.add_edge("background_check", "info")
builder.add_edge("info", "actor_mapping")
builder.add_edge("actor_mapping", 'complex_systems')
builder.add_edge("complex_systems", 'entropy')
builder.add_edge("entropy", 'game_theory')
builder.add_edge("game_theory", "unified_analysis")
builder.add_edge("unified_analysis", "revision")  # Analysis goes to revision

# Conditional edge for revision
def should_revise(state):
    revision_count = state['revision_count']
    if revision_count >= 2:  # Hard stop at 3 revisions
        return "no_revision"
    if state.get("revision_needed", False):
        return "research"
    return "no_revision"

builder.add_conditional_edges(
    "revision",
    should_revise,
    {
        "research": "research",
        "no_revision": "humanitarian_impact"
    }
)

builder.add_edge("research", "unified_analysis") # Loop back to unified analysis after research


builder.set_entry_point("background_check")

graph = builder.compile()