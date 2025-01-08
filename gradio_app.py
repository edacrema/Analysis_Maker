import os
from dotenv import load_dotenv
import gradio as gr
from datetime import datetime
from graph import graph
from nodes import AgentState
import time

# Load environment variables at the start
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def format_main_analysis(final_state, topic):
    return f"""
# Analysis Report: {topic}

## Executive Summary
{final_state['final_analysis']}

---
*Analysis generated on {final_state['today']}*
"""

def format_quantum_analysis(final_state):
    return f"""
# Quantum Analysis
{final_state['quantum_analysis']}
"""

def format_complex_systems_analysis(final_state):
    return f"""
# Complex Systems Analysis
{final_state['complex_system_analysis']}
"""

def format_entropy_analysis(final_state):
    return f"""
# Entropy Analysis
{final_state['entropy_analysis']}
"""

def format_recursive_analysis(final_state):
    return f"""
# Recursive Exploration Analysis
{final_state['recursive_exploration_analysis']}
"""

def format_dimensional_analysis(final_state):
    return f"""
# Dimensional Transcendence Analysis
{final_state['dimensional_trascendence_analysis']}
"""

def format_actor_analysis(final_state):
    return f"""
# Actor Mapping Analysis
{final_state['actor_mapping_analysis']}
"""

def generate_analysis(topic: str, progress=gr.Progress()):
    if not topic:
        return ["Please enter a topic to analyze"] * 7
        
    progress(0, desc="Initializing analysis...")
    
    # Initialize the state
    initial_state = AgentState(
        topic=topic,
        question_links=[],
        today=datetime.now().strftime("%Y-%m-%d"),
        news=[],
        quantum_analysis="",
        complex_system_analysis="",
        entropy_analysis="",
        recursive_exploration_analysis="",
        dimensional_trascendence_analysis="",
        actor_mapping_analysis="",
        final_analysis=""
    )
    
    progress(0.2, desc="Gathering news and data...")
    
    # Run the analysis graph
    final_state = graph.invoke(initial_state)
    
    progress(0.8, desc="Synthesizing analysis...")
    
    # Generate all analyses
    main_analysis = format_main_analysis(final_state, topic)
    quantum = format_quantum_analysis(final_state)
    complex_systems = format_complex_systems_analysis(final_state)
    entropy = format_entropy_analysis(final_state)
    recursive = format_recursive_analysis(final_state)
    dimensional = format_dimensional_analysis(final_state)
    actor = format_actor_analysis(final_state)
    
    progress(1.0, desc="Analysis complete!")
    
    return [
        main_analysis,
        quantum,
        complex_systems,
        entropy,
        recursive,
        dimensional,
        actor
    ]

with gr.Blocks(theme=gr.themes.Soft()) as iface:
    gr.Markdown(
        """
        # Advanced Topic Analysis System
        Enter a topic to receive a comprehensive analysis using our advanced analytical frameworks.
        """
    )
    
    with gr.Row():
        topic_input = gr.Textbox(
            label="Enter Topic for Analysis",
            placeholder="e.g., Impact of AI on Global Labor Markets"
        )
    
    with gr.Row():
        analyze_btn = gr.Button("Analyze", variant="primary")
    
    with gr.Tabs() as tabs:
        with gr.TabItem("Main Analysis"):
            main_output = gr.Markdown()
        with gr.TabItem("Complex Systems Analysis"):
            complex_systems_output = gr.Markdown()
        with gr.TabItem("Quantum Analysis"):
            quantum_output = gr.Markdown()
        with gr.TabItem("Entropy Analysis"):
            entropy_output = gr.Markdown()
        with gr.TabItem("Recursive Analysis"):
            recursive_output = gr.Markdown()
        with gr.TabItem("Dimensional Analysis"):
            dimensional_output = gr.Markdown()
        with gr.TabItem("Actor Analysis"):
            actor_output = gr.Markdown()
    
    analyze_btn.click(
        generate_analysis,
        inputs=[topic_input],
        outputs=[
            main_output,
            quantum_output,
            complex_systems_output,
            entropy_output,
            recursive_output,
            dimensional_output,
            actor_output
        ]
    )
    
    # Add examples without caching
    gr.Examples(
        examples=[
            ["Impact of Climate Change on Global Food Security"],
            ["Future of Cryptocurrency Adoption"],
            ["Geopolitical Implications of Space Mining"]
        ],
        inputs=topic_input,
        outputs=[
            main_output,
            quantum_output,
            complex_systems_output,
            entropy_output,
            recursive_output,
            dimensional_output,
            actor_output
        ],
        fn=generate_analysis,
        cache_examples=False  # Disable caching to prevent automatic execution
    )

if __name__ == "__main__":
    iface.launch()
