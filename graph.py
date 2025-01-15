from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from nodes import news_node, research_node, background_node, quantum_node, complex_systems_node, entropy_node, recursive_exploration_node, dimensional_trascendence_node, actor_mapping_node, unified_analysis_node, revision_node, humanitarian_impact_node, economic_impact_node, AgentState

builder = StateGraph(AgentState)
checkpointer = SqliteSaver("graph.db")

builder.add_node("background_check", background_node)
builder.add_node("info", news_node)
builder.add_node("unified_analysis", unified_analysis_node)
builder.add_node("quantum", quantum_node)
builder.add_node("complex_systems", complex_systems_node)
builder.add_node("entropy", entropy_node)
builder.add_node("recursive_exploration", recursive_exploration_node)
builder.add_node("dimensional_trascendence", dimensional_trascendence_node)
builder.add_node("actor_mapping", actor_mapping_node)
builder.add_node("revision", revision_node)
builder.add_node("research", research_node)
builder.add_node("humanitarian_impact", humanitarian_impact_node)  # New node
builder.add_node("economic_impact", economic_impact_node)  # New node

builder.add_edge("background_check", "info")
builder.add_edge("info", "quantum")
builder.add_edge("quantum", 'complex_systems')
builder.add_edge("complex_systems", 'entropy')
builder.add_edge("entropy", 'recursive_exploration')
builder.add_edge("recursive_exploration", 'dimensional_trascendence')
builder.add_edge("dimensional_trascendence", 'actor_mapping')
builder.add_edge("actor_mapping", "unified_analysis")
builder.add_edge("unified_analysis", "revision")  # Analysis goes to revision

# Conditional edge for revision
def should_revise(state):
    revision_count = state['revision_count']
    if revision_count >= 3:  # Hard stop at 3 revisions
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
builder.add_edge("humanitarian_impact", "economic_impact")  # Connect to economic_impact_node
builder.add_edge("economic_impact", END)  # Terminate the graph

builder.set_entry_point("background_check")

graph = builder.compile()