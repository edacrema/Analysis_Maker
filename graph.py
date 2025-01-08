from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from nodes import news_node, quantum_node, complex_systems_node, entropy_node, recursive_exploration_node, dimensional_trascendence_node, actor_mapping_node, analyst_node, AgentState

builder = StateGraph(AgentState)
checkpointer = SqliteSaver("graph.db")

builder.add_node("info", news_node)
builder.add_node("analysis", analyst_node)
builder.add_node("quantum", quantum_node)
builder.add_node("complex_systems", complex_systems_node)
builder.add_node("entropy", entropy_node)
builder.add_node("recursive_exploration", recursive_exploration_node)
builder.add_node("dimensional_trascendence", dimensional_trascendence_node)
builder.add_node("actor_mapping", actor_mapping_node)

builder.add_edge("info", "quantum")
builder.add_edge("quantum", 'complex_systems')
builder.add_edge("complex_systems", 'entropy')
builder.add_edge("entropy", 'recursive_exploration')
builder.add_edge("recursive_exploration", 'dimensional_trascendence')
builder.add_edge("dimensional_trascendence", 'actor_mapping')
builder.add_edge("actor_mapping","analysis")
builder.set_entry_point("info")


graph = builder.compile()