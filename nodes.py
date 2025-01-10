import os
from datetime import datetime
from typing import List, TypedDict, Dict  # Import Dict from typing
import google.generativeai as genai
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional

from langchain_community.utilities import GoogleSerperAPIWrapper

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, ValidationError  
from prompts import prompt_news, quantum_prompt, entropy_prompt, \
    recursive_exploration_prompt, dimensional_transcendence_prompt, actor_mapping_prompt, \
    complex_systems_prompt, analyst_prompt

from gemini_search import news_search

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# Adjust your typed dictionary as needed
class AgentState(TypedDict):
    topic: str
    question_links: List[str]
    today: str
    news: List[str]  # Updated to store all research
    complex_system_analysis: str
    quantum_analysis: str
    entropy_analysis: str
    recursive_exploration_analysis: str
    dimensional_trascendence_analysis: str
    actor_mapping_analysis: str
    final_analysis: str  # This is the unified analysis
    revision_needed: bool
    areas_for_improvement: str
    research_queries: List[str]
    revision_count: int

class Queries(BaseModel):
    queries: List[str]

genai.configure(api_key=GOOGLE_API_KEY)
# Example chat model
model_queries = genai.GenerativeModel(model_name='gemini-1.5-pro', generation_config = genai.types.GenerationConfig(temperature=0.2))  # Adjust the temperature as needed

model = genai.GenerativeModel('gemini-2.0-flash-exp', generation_config = genai.types.GenerationConfig(
    temperature=0.0  # Adjust the temperature as needed
))

model_2 = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
model_commentaries = genai.GenerativeModel('gemini-2.0-flash-exp', generation_config = genai.types.GenerationConfig(temperature=0.9))    


from datetime import datetime
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
# Assuming you have the news_search function and AgentState defined elsewhere
# from your_other_module import news_search, AgentState

# Define the Pydantic model for the output
class Queries(BaseModel):
    queries: List[str]

def news_node(state: "AgentState"):
    """
    Generates news search queries for a given topic, fetches news articles, 
    and updates the agent state.

    Args:
        state: The current state of the agent, containing at least the 'topic'.

    Returns:
        A dictionary containing the updated 'news' list and 'today' date.
    """
    topic = state['topic']
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
    {prompt_news}
    This is the topic: {topic}
    This is today's date: {today}
    """

    try:
        # Generate queries using Gemini
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=Queries
            ),
        )

        # Parse the response into the Queries model
        queries_data = Queries.model_validate_json(response.text)
        print(f"Generated queries: {queries_data}")  # Print the parsed queries

        # Fetch news articles for each query
        news = state.get('news', [])  # Get existing news or initialize an empty list
        for q in queries_data.queries:
            try:
                response_text = news_search(q)
                news.append(response_text)
                print(f"Fetched news for query: '{q}'")
            except Exception as e:
                print(f"Error fetching news for query '{q}': {e}")

        print(f"Collected news: {news}")  # Print the collected news
        return {'news': news, 'today': today}

    except Exception as e:
        print(f"Error in news_node: {e}")
        return {'news': [], 'today': today}

def quantum_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    prompt=f"""{quantum_prompt} This is the topic: {topic} This is the article summary: {article_summary}""" 
    response = model.generate_content(prompt)
    quantum_analysis = response.text
    print(quantum_analysis)
    return {'quantum_analysis': quantum_analysis}

def entropy_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    prompt = f"""
    {entropy_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    """
    response = model.generate_content(prompt)
    entropy_analysis = response.text
    print(entropy_analysis)
    return {'entropy_analysis': entropy_analysis}

def recursive_exploration_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    prompt = f"""
    {recursive_exploration_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    """ 
    response = model.generate_content(prompt)
    recursive_exploration = response.text
    print(recursive_exploration)
    return {'recursive_exploration_analysis': recursive_exploration}

def dimensional_trascendence_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    prompt = f"""
    {dimensional_transcendence_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    """
    response = model.generate_content(prompt)
    dimensional_trascendence = response.text
    print(dimensional_trascendence)
    return {'dimensional_trascendence_analysis': dimensional_trascendence}

def actor_mapping_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    prompt = f"""
    {actor_mapping_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    """
    response = model.generate_content(prompt)
    actor_mapping = response.text
    print(actor_mapping)
    return {'actor_mapping_analysis': actor_mapping}

def complex_systems_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    prompt = f"""
    {complex_systems_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    """
    response = model.generate_content(prompt)
    complex_system_analysis = response.text
    print(complex_system_analysis)
    return {'complex_system_analysis': complex_system_analysis}

def analyst_node(state: AgentState):
    # Extract data from the shared state
    topic = state['topic']
    article_summary = state['news']
    today = state['today']
    complex_system_analysis = state['complex_system_analysis']
    quantum_analysis = state['quantum_analysis']
    entropy_analysis = state['entropy_analysis']
    recursive_exploration_analysis = state['recursive_exploration_analysis']
    dimensional_trascendence_analysis = state['dimensional_trascendence_analysis']
    actor_mapping_analysis = state['actor_mapping_analysis']

    prompt = f"""
    {analyst_prompt}
    **Topic**:
    {topic}
    
    **Today's date**
    {today}
    
    **News / Article Summaries**:
    {article_summary}

    **Complex Systems Analysis**:
    {complex_system_analysis}

    **Quantum Analysis**:
    {quantum_analysis}

    **Entropy Analysis**:
    {entropy_analysis}

    **Recursive Exploration Analysis**:
    {recursive_exploration_analysis}

    **Dimensional Transcendence Analysis**:
    {dimensional_trascendence_analysis}

    **Actor Mapping Analysis**:
    {actor_mapping_analysis}

    Please produce the final, unified analysis now, integrating all the content above.
    """
    response = model.generate_content(prompt)
    final_analysis = response.text
    print(final_analysis)

    return {'final_analysis': final_analysis}

def unified_analysis_node(state: AgentState):
    topic = state["topic"]
    today = state["today"]
    article_summary = state["news"]
    complex_system_analysis = state["complex_system_analysis"]
    quantum_analysis = state["quantum_analysis"]
    entropy_analysis = state["entropy_analysis"]
    recursive_exploration_analysis = state["recursive_exploration_analysis"]
    dimensional_trascendence_analysis = state["dimensional_trascendence_analysis"]
    actor_mapping_analysis = state["actor_mapping_analysis"]

    prompt = f"""
    {analyst_prompt}
    
    **Topic**:
    {topic}
    
    **Today's date**
    {today}
    
    **News / Article Summaries**:
    {article_summary}

    **Complex Systems Analysis**:
    {complex_system_analysis}

    **Quantum Analysis**:
    {quantum_analysis}

    **Entropy Analysis**:
    {entropy_analysis}

    **Recursive Exploration Analysis**:
    {recursive_exploration_analysis}

    **Dimensional Transcendence Analysis**:
    {dimensional_trascendence_analysis}

    **Actor Mapping Analysis**:
    {actor_mapping_analysis}

    Please produce the final, unified analysis now, integrating all the content above.
    """

    response = model_2.generate_content(prompt)
    unified_analysis = response.text
    print(unified_analysis)

    return {"final_analysis": unified_analysis, "revision_needed": True} #Now it goes to revision node

import json
from typing import Dict
import google.generativeai as genai

def revision_node(state: AgentState) -> Dict:
    """
    Evaluates the unified analysis, determines if further revisions are needed,
    and generates research queries if necessary.
    """
    MAX_REVISIONS = 3  # Maximum number of revisions allowed
    unified_analysis = state["final_analysis"]
    current_revision_count = state.get("revision_count", 0)

    # Check if we've reached the maximum number of revisions
    if current_revision_count >= MAX_REVISIONS:
        print(f"Maximum number of revisions ({MAX_REVISIONS}) reached. Stopping revision process.")
        return {
            "revision_needed": False,
            "areas_for_improvement": None,
            "research_queries": [],
            "final_analysis": unified_analysis,
            "revision_count": current_revision_count
        }

    revision_prompt = f"""
    You are a critical reviewer tasked with evaluating the quality and completeness of the following analysis:

    **Unified Analysis:**

    {unified_analysis}

    **Evaluation Criteria:**

    1.  **Clarity and Coherence:** Is the analysis well-structured, easy to understand, and logically sound?
    2.  **Depth of Analysis:** Does the analysis demonstrate a deep understanding of the topic, going beyond superficial observations?
    3.  **Integration of Frameworks:** Does the analysis effectively integrate the different analytical frameworks (complex systems, quantum, etc.)?
    4.  **Evidence and Support:** Are claims supported by evidence from the news articles and the specialized analyses?
    5.  **Originality:** Does the analysis offer any new or unique insights?
    6.  **Potential Future Scenarios:** Are the potential future scenarios well-reasoned and plausible?

    **Based on your evaluation, answer the following questions:**

    1.  **Revision Needed (YES/NO):** Does this analysis require further revision or refinement to improve its quality and completeness?
    2.  **Areas for Improvement:** Briefly describe the specific areas where the analysis is lacking or could be improved 
        (e.g., "The analysis lacks depth in the actor mapping section," "The potential future scenarios are not well-supported").
    3.  **Research Queries:** If you answered YES to question 1, generate 2-3 specific research queries that could be used
        to gather more information and address the identified weaknesses.

    **Output Format:**
    
    Respond in JSON format with the following keys:
    - revision_needed (str): either "YES" or "NO"
    - areas_for_improvement (str or null): a brief description of areas needing improvement or null
    - research_queries (array or null): a list of 2-3 research queries or null

    Example:
    {{
        "revision_needed": "YES",
        "areas_for_improvement": "The analysis lacks depth in the actor mapping section.",
        "research_queries": [
            "What are the key interests and motivations of actor X in the context of this topic?",
            "What are the potential economic consequences of scenario Y?"
        ]
    }}
    """

    try:
        response = model.generate_content(
            revision_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        # Parse the response text as JSON
        response_json = json.loads(response.text)
        revision_needed = response_json["revision_needed"] == "YES"
        areas_for_improvement = response_json.get("areas_for_improvement")
        research_queries = response_json.get("research_queries", [])

        print(f"Revision {current_revision_count + 1}/{MAX_REVISIONS}")
        print(f"Revision Decision: {revision_needed}")
        if areas_for_improvement:
            print(f"Areas for Improvement: {areas_for_improvement}")
        if research_queries:
            print(f"Research Queries: {research_queries}")

        return {
            "revision_needed": revision_needed,
            "areas_for_improvement": areas_for_improvement,
            "research_queries": research_queries,
            "final_analysis": unified_analysis,
            "revision_count": current_revision_count + 1
        }
    except Exception as e:
        print("Error in revision_node:", e)
        
        return {
            "revision_needed": False,
            "areas_for_improvement": None,
            "research_queries": [],
            "final_analysis": unified_analysis,
            "revision_count": current_revision_count
        }


def research_node(state: AgentState) -> Dict:
    """
    Performs online research based on queries generated by the revision_node.
    """
    research_queries = state.get("research_queries", [])
    existing_news = state.get("news", [])

    new_research_results = []
    for query in research_queries:
        try:
            response_text = news_search(query)  # Use your existing news_search function
            new_research_results.append(response_text)
            print(f"Performed research for query: '{query}'")
        except Exception as e:
            print(f"Error fetching news for query '{query}': {e}")

    # Combine new research with existing news
    updated_news = existing_news + new_research_results

    return {"news": updated_news}