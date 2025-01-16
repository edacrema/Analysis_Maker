import os
from dotenv import load_dotenv
import gradio as gr
from datetime import datetime
from graph import graph
from nodes import AgentState
from pdf_generator import generate_analysis_pdf

# Load environment variables at the start
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def format_main_analysis(final_state, topic):
    return f"""
# Analysis of {topic}

{final_state['final_analysis']}
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

def format_actor_analysis(final_state):
    return f"""
# Actor Mapping Analysis

{final_state['actor_mapping_analysis']}
"""

def format_game_theory_analysis(final_state):
    return f"""
# Game Theory Analysis

{final_state['game_theory_analysis']}
"""

def format_humanitarian_analysis(final_state):
    return f"""
# Humanitarian Impact Analysis

{final_state['humanitarian_impact_analysis']}
"""

def generate_analysis(topic: str, progress=gr.Progress()):
    if not topic:
        return ["Please enter a topic to analyze"] * 6

    progress(0, desc="Initializing analysis...")

    # Initialize the state
    initial_state = {
        "topic": str(topic),
        "question_links": [],
        "today": datetime.now().strftime("%Y-%m-%d"),
        "background": [""],
        "news": [""],
        "complex_system_analysis": "",
        "entropy_analysis": "",
        "actor_mapping_analysis": "",
        "game_theory_analysis": "",
        "final_analysis": "",
        "revision_needed": False,
        "areas_for_improvement": "",
        "research_queries": [],
        "humanitarian_impact_analysis": "",
        "revision_count": 0
    }

    progress(0.1, desc="Gathering news and data...")
    final_state = graph.invoke(initial_state, config={"recursion_limit": 50})

    progress(0.7, desc="Synthesizing analysis...")

    # Generate PDF after analysis is complete
    try:
        pdf_path = generate_analysis_pdf(final_state)
        print(f"PDF report generated and saved to: {pdf_path}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        print("Analysis will continue without PDF generation")

    # Generate all analyses
    main_analysis = format_main_analysis(final_state, topic)
    complex_systems = format_complex_systems_analysis(final_state)
    entropy = format_entropy_analysis(final_state)
    actor = format_actor_analysis(final_state)
    game_theory = format_game_theory_analysis(final_state)
    humanitarian = format_humanitarian_analysis(final_state)

    progress(1.0, desc="Analysis complete!")

    return [
        main_analysis,
        complex_systems,
        entropy,
        actor,
        game_theory,
        humanitarian
    ]

with gr.Blocks(theme=gr.themes.Soft()) as iface:
    gr.Markdown(
        """
        # Advanced Topic Analysis System
        Enter a topic to receive a comprehensive analysis using our advanced analytical frameworks.
        A PDF report will be automatically generated in the Reports directory.
        """
    )

    with gr.Row():
        topic_input = gr.Textbox(
            label="Enter Topic for Analysis",
            placeholder="Enter your topic here..."
        )

    with gr.Row():
        analyze_btn = gr.Button("Analyze", variant="primary")

    with gr.Tabs() as tabs:
        with gr.TabItem("Main Analysis"):
            main_output = gr.Markdown()
        with gr.TabItem("Complex Systems Analysis"):
            complex_systems_output = gr.Markdown()
        with gr.TabItem("Entropy Analysis"):
            entropy_output = gr.Markdown()
        with gr.TabItem("Actor Analysis"):
            actor_output = gr.Markdown()
        with gr.TabItem("Game Theory Analysis"):
            game_theory_output = gr.Markdown()
        with gr.TabItem("Humanitarian Impact"):
            humanitarian_output = gr.Markdown()

    analyze_btn.click(
        generate_analysis,
        inputs=[topic_input],
        outputs=[
            main_output,
            complex_systems_output,
            entropy_output,
            actor_output,
            game_theory_output,
            humanitarian_output
        ]
    )

    # Add examples without caching
    gr.Examples(
        examples=[
            ["The impact of artificial intelligence on global education"],
            ["The future of renewable energy in developing countries"],
            ["The role of quantum computing in cybersecurity"],
        ],
        inputs=[topic_input],
        outputs=[
            main_output,
            complex_systems_output,
            entropy_output,
            actor_output,
            game_theory_output,
            humanitarian_output
        ],
        fn=generate_analysis,
        cache_examples=False
    )

if __name__ == "__main__":
    iface.launch()
