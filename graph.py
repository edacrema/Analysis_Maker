from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from nodes import news_node, research_node, quantum_node, complex_systems_node, entropy_node, recursive_exploration_node, dimensional_trascendence_node, actor_mapping_node, unified_analysis_node, revision_node, AgentState

builder = StateGraph(AgentState)
checkpointer = SqliteSaver("graph.db")

builder.add_node("info", news_node)
builder.add_node("unified_analysis", unified_analysis_node)
builder.add_node("quantum", quantum_node)
builder.add_node("complex_systems", complex_systems_node)
builder.add_node("entropy", entropy_node)
builder.add_node("recursive_exploration", recursive_exploration_node)
builder.add_node("dimensional_trascendence", dimensional_trascendence_node)
builder.add_node("actor_mapping", actor_mapping_node)
builder.add_node("revision", revision_node) 
builder.add_node("research", research_node) # Keep the revision node

builder.add_edge("info", "quantum")
builder.add_edge("quantum", 'complex_systems')
builder.add_edge("complex_systems", 'entropy')
builder.add_edge("entropy", 'recursive_exploration')
builder.add_edge("recursive_exploration", 'dimensional_trascendence')
builder.add_edge("dimensional_trascendence", 'actor_mapping')
builder.add_edge("actor_mapping", "unified_analysis")
builder.add_edge("unified_analysis", "revision") # Analysis goes to revision
# builder.add_edge("revision", "subtopic_identification") # After revision, go to subtopic identification

# Conditional edge for revision
def should_revise(state):
    if state.get("revision_needed"):
        return "research"  # Route to research if revision is needed
    else:
        return "end"

builder.add_conditional_edges(
    "revision",
    should_revise,
    {
        "research": "research",
        "end": END
    }
)
# we need to change the loop to the unified analysis:
builder.add_edge("research", "quantum")

builder.set_entry_point("info")

graph = builder.compile()