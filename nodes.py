import os
from datetime import datetime
from typing import List, TypedDict, Dict, Optional  # Import Dict from typing
import google.generativeai as genai
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI

from langchain_community.utilities import GoogleSerperAPIWrapper

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, ValidationError  
from prompts import quantum_prompt, entropy_prompt, \
    recursive_exploration_prompt, dimensional_transcendence_prompt, actor_mapping_prompt, \
    complex_systems_prompt, analyst_prompt

from perplexity_pipeline import news_search, generate_queries_with_perplexity

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# Adjust your typed dictionary as needed
class AgentState(TypedDict):
    topic: str
    question_links: List[str]
    today: str
    background: List[str]
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
    humanitarian_impact_analysis: str  # New field for humanitarian analysis
    economic_impact_analysis: str  # New field for economic analysis

class Queries(BaseModel):
    queries: List[str]
    recency_filter: Optional[str] = "month" 

genai.configure(api_key=GOOGLE_API_KEY)
# Example chat model
model_queries = genai.GenerativeModel(model_name='gemini-1.5-pro', generation_config = genai.types.GenerationConfig(temperature=0.2))  # Adjust the temperature as needed

model = genai.GenerativeModel('gemini-2.0-flash-exp', generation_config = genai.types.GenerationConfig(
    temperature=0.0  # Adjust the temperature as needed
))

model_2 = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
model_3 = ChatOpenAI(model_name='o1-mini')

from datetime import datetime
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
# Assuming you have the news_search function and AgentState defined elsewhere
# from your_other_module import news_search, AgentState

# Define the Pydantic model for the output
class Queries(BaseModel):
    queries: List[str]
    recency_filter: str

def background_node(state: "AgentState"):
    """
    Generates background-related queries for a given topic, then fetches
    historical or foundational context using Perplexity-based news_search.
    Updates 'background' in the agent state.
    """
    topic = state['topic']
    today = datetime.now().strftime("%Y-%m-%d")

    prompt_background = f"""
You are a researcher tasked with providing concise background information on a given topic. 
Your goal is to generate focused search queries that will retrieve relevant historical context 
and foundational knowledge necessary to understand the current situation.

**Topic:** {topic}
Date: {today}

**Instructions:**

1.  **Identify Key Aspects:** Based on the topic, determine the 3-4 most important aspects or subtopics that require background information. Consider:
    *   Historical events leading up to the current situation.
    *   Key actors or organizations that have played a significant role in the past.
    *   Important policies, agreements, or treaties relevant to the topic.
    *   Underlying economic, social, or political factors that shaped the present.
2.  **Formulate Search Queries:** For each key aspect, formulate 1-2 specific and targeted search queries that are likely to yield informative results from a reputable news source or database.
    *   Use clear and unambiguous keywords.
    *   Consider using date ranges or specific event names to narrow down the search.
    *   Focus on queries that provide context and historical background, not just recent news.
    *   **Formulate queries that have minimum overlap in terms of meaning and potential research outcomes to maximize the range of information that is retrieved.**

3.  **Prioritize Foundational Information:**  Prioritize information that is essential for understanding the *origins* and *evolution* of the current issue.

### Instructions
1. Identify the key aspects or subtopics requiring background.
2. Formulate 3-4 search queries for historical/contextual info.
3. Return JSON with two fields:
    - "queries": array of query strings
    - "recency_filter": e.g., "month" or "year"

**Output Format**:
Only return valid JSON with two fields: "queries" (array of strings), and "recency_filter" (string).
Do not include any markdown fences or extra text.

Example:
{{
  "queries": ["query1", "query2"],
  "recency_filter": "month"
}}
"""
    try:
        # 1) Generate queries using your custom model (model_queries).
        response = model_queries.generate_content(
            prompt_background,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3
            ),
        )

        # 2) Attempt to parse the JSON response
        try:
            queries_data = Queries.model_validate_json(response.text)
        except ValidationError as e:
            print(f"Pydantic validation error: {e}")
            # Attempt to fix the JSON string (basic example)
            try:
                fixed_json_str = response.text.strip()
                if fixed_json_str.startswith("```json"):
                  fixed_json_str = fixed_json_str[7:]
                if fixed_json_str.endswith("```"):
                  fixed_json_str = fixed_json_str[:-3]
                
                
                # Attempt to parse the JSON string to a Python dictionary
                data_dict = json.loads(fixed_json_str)

                # Ensure the dictionary has the expected structure
                if not isinstance(data_dict, dict) or "queries" not in data_dict or "recency_filter" not in data_dict:
                    raise ValueError("JSON does not have the expected structure")
                
                queries_data = Queries(**data_dict)

            except Exception as fix_error:
                print(f"Error attempting to fix JSON: {fix_error}")
                print(f"Failed to parse JSON: {response.text}")
                return {'background': [], 'today': today}

        print(f"Generated queries: {queries_data}")

        # 3) Extract the recommended recency filter and queries
        recency_filter = queries_data.recency_filter or "month"
        research_queries = queries_data.queries

        # 4) Use news_search to gather background info
        background = state.get('background', [])
        for q in research_queries:
            try:
                article_summary = news_search(q, recency_filter=recency_filter)
                background.append(article_summary)
                print(f"Fetched background for query: '{q}' (recency='{recency_filter}')")
            except Exception as e:
                print(f"Error fetching background for query '{q}': {e}")

        # 5) Update and return the state
        return {'background': background, 'today': today}

    except Exception as e:
        print(f"Error in background_node: {e}")
        # Gracefully return empty background if there's an error
        return {'background': [], 'today': today}


def news_node(state: "AgentState"):
    """
    Generates news-oriented queries for a given topic, then fetches articles 
    using Perplexity-based news_search. Updates 'news' in the agent state.
    """
    topic = state["topic"]
    today = state.get("today", datetime.now().strftime("%Y-%m-%d"))

    prompt_news = f"""

You are a news query generator. Your task is to create up to 6 search queries to retrieve relevant news articles for a specified macrotopic. These queries should be designed to support the generation of a detailed and structured scenario, incorporating recent and relevant perspectives.

### Key Requirements

#### 1. Final Product Context
The final product will be a scenario structured as follows:
- Title: Summarizes the central theme
- Executive Summary: Provides a high-level overview of key elements and uncertainties
- Narrative: Detailed exploration integrating various analyses ("Quantum," "Entropy," etc.) and wisdom of the crowd insights
- Thematic Analyses: Covers Political, Economic, Security, Legal, and Operational aspects
- Implications and Uncertainties: Examines potential outcomes and critical unknowns

#### 2. Query Objectives
Generate diverse and complementary search queries to ensure comprehensive coverage of the topic.

Capture the following dimensions:
- Recent Developments: Focus on breaking news or major updates
- Long-term analysis of the issue since its beginning
- Diverse Perspectives: Include multiple viewpoints (e.g., geopolitical, economic, social)
- Relevant Stakeholders: Identify actors or entities shaping the topic
- Potential Implications: Explore consequences of key developments

### Guidelines for Query Generation
- Specificity: Ensure queries are precise enough to return highly relevant results
- Comprehensiveness: Design queries to capture multiple aspects of the topic
- Diversity: Avoid overlapping queries; focus on varying dimensions of the topic
- Scalability: The queries should collectively provide sufficient information for all thematic sections of the scenario


Return JSON with two fields:
- "queries": up to 6 query strings
- "recency_filter": e.g., "month" or "year"

Topic: {topic}
Date: {today}

**Output Format**:
Only return valid JSON with two fields: "queries" (array of strings), and "recency_filter" (string).
Do not include any markdown fences or extra text.

Example:
{{
  "queries": ["query1", "query2"],
  "recency_filter": "month"
}}
"""

    try:
        # 1) Generate queries via your custom model
        response = model_queries.generate_content(
            prompt_news,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3
            ),
        )
        # 2) Attempt to parse the JSON response
        try:
            queries_data = Queries.model_validate_json(response.text)
        except ValidationError as e:
            print(f"Pydantic validation error: {e}")
            # Attempt to fix the JSON string (basic example)
            try:
                fixed_json_str = response.text.strip()
                if fixed_json_str.startswith("```json"):
                  fixed_json_str = fixed_json_str[7:]
                if fixed_json_str.endswith("```"):
                  fixed_json_str = fixed_json_str[:-3]

                # Attempt to parse the JSON string to a Python dictionary
                data_dict = json.loads(fixed_json_str)

                # Ensure the dictionary has the expected structure
                if not isinstance(data_dict, dict) or "queries" not in data_dict or "recency_filter" not in data_dict:
                    raise ValueError("JSON does not have the expected structure")

                queries_data = Queries(**data_dict)
            except Exception as fix_error:
                print(f"Error attempting to fix JSON: {fix_error}")
                print(f"Failed to parse JSON: {response.text}")
                return {"news": [], "today": today}

        print(f"Generated queries: {queries_data}")

        # 3) Extract the recommended recency filter
        recency_filter = queries_data.recency_filter or "month"

        # 4) Fetch news articles for each query
        news_queries = queries_data.queries
        news = state.get("news", [])
        for q in news_queries:
            try:
                article_summary = news_search(q, recency_filter=recency_filter)
                news.append(article_summary)
                print(f"Fetched news for query: '{q}' (recency='{recency_filter}')")
            except Exception as e:
                print(f"Error fetching news for query '{q}': {e}")

        return {"news": news, "today": today}

    except Exception as e:
        print(f"Error in news_node: {e}")
        return {"news": [], "today": today}


def quantum_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    prompt=f"""{quantum_prompt} This is the topic: {topic}\n\n This is the article summary: {article_summary    }\n\n This is the background: {background}""" 
    response = model_2.generate_content(prompt)
    quantum_analysis = response.text
    print(quantum_analysis)
    return {'quantum_analysis': quantum_analysis}

def entropy_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    prompt = f"""
    {entropy_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    This is the background: {background}
    """
    response = model_2.generate_content(prompt)
    entropy_analysis = response.text
    print(entropy_analysis)
    return {'entropy_analysis': entropy_analysis}

def recursive_exploration_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    prompt=f"""{recursive_exploration_prompt} This is the topic: {topic}\n\n This is the article summary: {article_summary    }\n\n This is the background: {background}""" 

    response = model_2.generate_content(prompt)
    recursive_exploration = response.text
    print(recursive_exploration)
    return {'recursive_exploration_analysis': recursive_exploration}

def dimensional_trascendence_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    prompt = f"""
    {dimensional_transcendence_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    This is the background: {background}
    """
    response = model_2.generate_content(prompt)
    dimensional_trascendence = response.text
    print(dimensional_trascendence)
    return {'dimensional_trascendence_analysis': dimensional_trascendence}

def actor_mapping_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    prompt = f"""
    {actor_mapping_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    This is the background: {background}
    """
    response = model_2.generate_content(prompt)
    actor_mapping = response.text
    print(actor_mapping)
    return {'actor_mapping_analysis': actor_mapping}

def complex_systems_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    prompt = f"""
    {complex_systems_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    This is the background: {background}
    """
    response = model_2.generate_content(prompt)
    complex_system_analysis = response.text
    print(complex_system_analysis)
    return {'complex_system_analysis': complex_system_analysis}

def analyst_node(state: AgentState):
    # Extract data from the shared state
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    areas_for_improvement = state['areas_for_improvement']
    previous_analysis = state.get('final_analysis', '')
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

    **Background**:
    {background}
    
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

    **Previous Draft Analysis (if any)**:
    {previous_analysis}

    **Critique to the previous draft analysis (if any)**:
    {areas_for_improvement}

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
    previous_analysis = state.get("final_analysis", "")  # Use get() with default value
    areas_for_improvement = state["areas_for_improvement"]
    background = state["background"]
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

    **Background**:
    {background}
    
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

    **Previous Draft Analysis (if any)**:
    {previous_analysis}

    **Critique to the previous draft analysis (if any)**:
    {areas_for_improvement}

    Please produce the final, unified analysis now, integrating all the content above.
    """

    response = model_3.invoke(prompt)
    scenario_text = response.content
    print(f"Generated scenario: {scenario_text[:100]}...")
    unified_analysis = scenario_text
    print(unified_analysis)

    # Get current revision count and set revision_needed to True only on first pass
    revision_count = state['revision_count']
    revision_needed = state.get("revision_needed", False)  # <-- define revision_needed here

    return {
        "final_analysis": unified_analysis,
        "revision_needed": revision_needed,
        "revision_count": revision_count
    }

import json
from typing import Dict
import google.generativeai as genai

def revision_node(state: "AgentState") -> Dict:
    """
    Evaluates the unified analysis, determines if further revisions are needed,
    and generates research queries if necessary.
    """
    MAX_REVISIONS = 3  # Maximum number of revisions allowed
    unified_analysis = state["final_analysis"]
    current_revision_count = state["revision_count"]
    background = state["background"]

    # Check if we've reached the maximum number of revisions
    if current_revision_count >= MAX_REVISIONS:
        print(f"Maximum number of revisions ({MAX_REVISIONS}) reached. Stopping revision process.")
        return {
            "revision_needed": False,
            "areas_for_improvement": "",
            "research_queries": [],
            "final_analysis": unified_analysis,
            "revision_count": current_revision_count
        }

    revision_prompt = f"""
    You are a critical reviewer tasked with evaluating the quality and completeness of the following analysis:

    **Background of the topic:**
    {background}

    **Unified Analysis:**

    {unified_analysis}

    **Evaluation Criteria:**

    1.  **Clarity and Coherence:** Is the analysis well-structured, easy to understand, and logically sound?
    2.  **Depth of Analysis:** Does the analysis demonstrate a deep understanding of the topic, going beyond superficial observations?
    3.  **Integration of Frameworks:** Does the analysis effectively integrate the different analytical frameworks (complex systems, quantum, etc.)?
    4.  **Evidence and Support:** Are claims supported by evidence from the news articles, the background information, and the specialized analyses?
    5.  **Originality:** Does the analysis offer any new or unique insights?
    6.  **Potential Future Scenarios:** Are the potential future scenarios well-reasoned and plausible?

    **Based on your evaluation, answer the following questions:**

    1.  **Revision Needed (YES/NO):** Does this analysis require further revision or refinement to improve its quality and completeness?
    2.  **Areas for Improvement:** Briefly describe the specific areas where the analysis is lacking or could be improved (e.g., "The analysis lacks depth in the actor mapping section," "The potential future scenarios are not well-supported").
    3.  **Research Queries:** If you answered YES to question 1, generate 2-3 specific research queries that could be used to gather more information and address the identified weaknesses.

    **Guidelines for Research Query Generation:**

    *   **Specificity:** Ensure queries are precise enough to return highly relevant results from a search engine (like Google Serper).
    *   **Comprehensiveness:** Design queries to capture multiple aspects of the area for improvement.
    *   **Diversity:** Avoid overlapping queries; focus on varying dimensions of the needed information.
    *   **Actionable:** Formulate queries that are likely to yield concrete and useful information for improving the analysis.

    **Example Research Queries (Illustrative and Diversified):**

    *   **Scenario:** Analysis of the impact of social media on political polarization.
        *   **Area for Improvement:** "The analysis lacks a detailed examination of the role of specific social media platforms."
        *   **Research Queries:**
            *   "Twitter's role in spreading political misinformation 2022-2023"
            *   "Facebook algorithm changes AND political polarization"
            *   "Comparative analysis of social media platform policies on political content"

    *   **Scenario:** Analysis of the future of cryptocurrencies.
        *   **Area for Improvement:** "The analysis doesn't adequately address the potential impact of regulatory changes."
        *   **Research Queries:**
            *   "Proposed cryptocurrency regulations in the US and EU"
            *   "Impact of SEC v. Ripple Labs decision on crypto market"
            *   "Central bank digital currencies AND cryptocurrency adoption"

    *   **Scenario:** Analysis of supply chain disruptions caused by climate change.
        *   **Area for Improvement:** "The analysis needs more specific examples of companies adapting to climate-related supply chain risks."
        *   **Research Queries:**
            *   "Case studies of companies adapting supply chains to climate change"
            *   "Reshoring initiatives AND climate change resilience"
            *   "Impact of extreme weather events on global supply chains 2023"

    **Output Format (JSON)**:
    {{
        "revision_needed": "YES" or "NO",
        "areas_for_improvement": "...",
        "research_queries": [
            "Query 1",
            "Query 2"
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
        assistant_content = response.text  # The raw JSON string

        # Parse the response text as JSON
        response_json = json.loads(assistant_content)
        revision_needed = response_json["revision_needed"] == "YES"
        areas_for_improvement = response_json.get("areas_for_improvement", "")
        research_queries = response_json.get("research_queries", [])

        # Increment revision count only if revision is needed
        new_revision_count = current_revision_count + 1 if revision_needed else current_revision_count

        print(f"Revision {new_revision_count}/{MAX_REVISIONS}")
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
            "revision_count": new_revision_count
        }

    except Exception as e:
        print("Error in revision_node:", e)
        return {
            "revision_needed": False,
            "areas_for_improvement": "",
            "research_queries": [],
            "final_analysis": unified_analysis,
            "revision_count": current_revision_count
        }



def research_node(state: "AgentState") -> Dict:
    """
    Performs online research based on queries generated by the revision_node.
    """
    research_queries = state.get("research_queries", [])
    existing_news = state.get("news", [])
    revision_count = state["revision_count"]

    new_research_results = []
    # If you want to set a default recency to 'month' or 'year', do so here:
    default_recency = "month"

    for query in research_queries:
        try:
            # You might pass default_recency or let the function handle it:
            response_text = news_search(query, recency_filter=default_recency)
            new_research_results.append(response_text)
            print(f"Performed research for query: '{query}'")
        except Exception as e:
            print(f"Error fetching news for query '{query}': {e}")

    # Combine new research with existing news
    updated_news = existing_news + new_research_results

    return {
        "news": updated_news,
        "revision_count": revision_count  # Preserve the revision count
    }

def humanitarian_impact_node(state: AgentState) -> Dict:
    """
    Performs research on and analyzes the potential humanitarian impact of the issue,
    with a focus on vulnerable populations, potential spillover effects to other countries,
    estimates of the number of people in need, and a particular emphasis on food security.
    """
    topic = state["topic"]
    final_analysis = state["final_analysis"]
    background = state["background"]
    today = state["today"]
    complex_system_analysis = state.get("complex_system_analysis", "")
    quantum_analysis = state.get("quantum_analysis", "")
    entropy_analysis = state.get("entropy_analysis", "")
    recursive_exploration_analysis = state.get("recursive_exploration_analysis", "")
    dimensional_trascendence_analysis = state.get("dimensional_trascendence_analysis", "")
    actor_mapping_analysis = state.get("actor_mapping_analysis", "")

    # --- Generate research queries ---
    research_query_prompt = f"""
    You are an expert on humanitarian crises with extensive knowledge of vulnerable populations, 
    displacement, migration, food security, and healthcare access in crisis situations. You are 
    tasked with analyzing the potential humanitarian impact of the following issue, paying 
    **particular attention to food security concerns**:

    **Topic:** {topic}

    **Current Analysis:**
    {final_analysis}

    **Background:**
    {background}

    **Analytical Frameworks:**
    (Consider the insights from these frameworks when formulating your queries)
    Complex Systems Analysis: {complex_system_analysis}
    Quantum Analysis: {quantum_analysis}
    Entropy Analysis: {entropy_analysis}
    Recursive Exploration Analysis: {recursive_exploration_analysis}
    Dimensional Transcendence Analysis: {dimensional_trascendence_analysis}
    Actor Mapping Analysis: {actor_mapping_analysis}

    **Instructions:**

    1.  **Identify Key Humanitarian Aspects:** Based on the topic and the provided analyses, identify 3-4 key aspects of the issue that are most likely to have significant humanitarian ramifications, **with a strong focus on food security**. Consider factors such as:
        *   **Vulnerable Populations:** Which groups are likely to be disproportionately affected (e.g., children, elderly, displaced persons, marginalized communities)?
        *   **Specific Regions:** Which geographic regions are likely to experience the most severe humanitarian impacts, particularly regarding food insecurity?
        *   **Spillover Effects:**  Could the crisis lead to humanitarian challenges in neighboring countries or regions (e.g., through refugee flows, economic impacts)?
        *   **Food Security:** How might the crisis affect food production, distribution, access, and prices?
        *   **Basic Needs:** How might the crisis affect access to water, shelter, healthcare, and other essential services?
        *   **Protection Risks:**  Are there potential risks of violence, exploitation, or human rights abuses?
        *   **Number of People in Need:** What is the current or estimated number of people potentially affected and requiring humanitarian assistance, especially regarding food security?

    2.  **Formulate Research Queries:** Formulate up to 4 specific and targeted research queries that will help gather in-depth information. **At least 2 of these queries should directly address food security concerns.**
        *   Use precise terminology related to humanitarian crises, vulnerable populations, and food security.
        *   Specify relevant geographic regions, especially vulnerable areas.
        *   **Explicitly include queries that seek data on the actual or potential number of people in need, particularly concerning food insecurity** (e.g., "Estimated number of people facing food shortages in...", "Projected malnutrition rates in...").
        *   Focus on queries that are likely to yield credible sources, data, and expert analyses from humanitarian organizations (e.g., WFP, FAO, FEWS NET).

    **Output Format**:
Only return valid JSON with two fields: "queries" (array of strings), and "recency_filter" (string).
Do not include any markdown fences or extra text.

Example:
{{
  "queries": ["query1", "query2"],
  "recency_filter": "month"
}}
    """

    try:
        response = model_queries.generate_content(
            research_query_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )

        # Attempt to parse the JSON response
        try:
            queries_data = Queries.model_validate_json(response.text)
        except ValidationError as e:
            print(f"Pydantic validation error: {e}")
            # Attempt to fix the JSON string
            try:
                fixed_json_str = response.text.strip()
                if fixed_json_str.startswith("```json"):
                    fixed_json_str = fixed_json_str[7:]
                if fixed_json_str.endswith("```"):
                    fixed_json_str = fixed_json_str[:-3]
                
                # Attempt to parse the JSON string to a Python dictionary
                data_dict = json.loads(fixed_json_str)

                # Ensure the dictionary has the expected structure
                if not isinstance(data_dict, dict) or "queries" not in data_dict or "recency_filter" not in data_dict:
                    raise ValueError("JSON does not have the expected structure")
                
                queries_data = Queries(**data_dict)

            except Exception as fix_error:
                print(f"Error attempting to fix JSON: {fix_error}")
                print(f"Failed to parse JSON: {response.text}")
                return {
                    "humanitarian_impact_analysis": "",
                    "news": state.get("news", [])
                }

        research_queries = queries_data.queries
        recency_filter = queries_data.recency_filter or "month"
        print(f"Research queries for humanitarian impact: {research_queries}")

    except Exception as e:
        print(f"Error generating research queries: {e}")
        research_queries = []
        recency_filter = "month"

    # --- Perform research ---
    humanitarian_news = []
    for query in research_queries:
        try:
            response_text = news_search(query, recency_filter=recency_filter)
            humanitarian_news.append(response_text)
        except Exception as e:
            print(f"Error fetching news for query '{query}': {e}")

    # Update the news in the state
    news = state.get("news", [])
    updated_news = news + humanitarian_news

    # --- Analyze the humanitarian impact ---
    humanitarian_impact_prompt = f"""
    You are an expert on humanitarian crises with extensive knowledge of vulnerable populations, 
    displacement, migration, food security, and healthcare access in crisis situations. Analyze 
    the potential humanitarian impact of the following issue, integrating the provided 
    background information, specialized analyses, and research findings. **Pay particular 
    attention to food security concerns and provide a detailed assessment of the potential 
    impacts on food production, distribution, access, and prices.**

    **Topic:** {topic}

    **Current Analysis:**
    {final_analysis}

    **Background:**
    {background}

    **Specialized Analyses:**
    Complex Systems Analysis: {complex_system_analysis}
    Quantum Analysis: {quantum_analysis}
    Entropy Analysis: {entropy_analysis}
    Recursive Exploration Analysis: {recursive_exploration_analysis}
    Dimensional Transcendence Analysis: {dimensional_trascendence_analysis}
    Actor Mapping Analysis: {actor_mapping_analysis}

    **Research:**
    {updated_news}

    **Today's Date:** {today}

    **Instructions:**

    1.  **Impacts on Vulnerable Populations:**
        *   Analyze the potential impacts on specific vulnerable groups (e.g., children, elderly, persons with disabilities, marginalized communities).
        *   Consider factors such as pre-existing vulnerabilities, coping mechanisms, and access to support.

    2.  **Regions Most Impacted:**
        *   Identify the geographic regions likely to experience the most severe humanitarian consequences, **with a focus on regions facing potential food insecurity**.
        *   Provide a rationale for your assessment, considering factors such as proximity to the conflict zone, dependence on affected resources, and existing humanitarian needs.

    3.  **Displacement and Migration:**
        *   Analyze the potential for the issue to cause displacement of populations within the affected country or region.
        *   Assess the likelihood of refugee flows to neighboring countries and the potential impact on those countries.

    4.  **Food Security:**
        *   **Analyze in detail the potential impacts on food production, distribution, and access.**
        *   **Consider factors such as disruptions to agriculture, supply chain interruptions, price increases, and impacts on livelihoods.**
        *   **Assess the potential for food shortages, malnutrition, and increased food insecurity.**
        *   **Identify specific populations or regions most at risk of food insecurity.**

    5.  **Healthcare Access:**
        *   Analyze the potential impacts on healthcare systems and access to essential medical services.
        *   Consider factors such as damage to healthcare infrastructure, shortages of medical supplies, and increased demand due to displacement or injuries.

    6.  **Spillover Effects to Other Countries:**
        *   Analyze how the humanitarian crisis might affect neighboring countries or the broader region.
        *   Consider factors such as refugee flows, economic impacts, political instability, and the potential for the crisis to spread.

    7. **Number of People in Need:**
        *   **Provide an estimate (or range of estimates) for the number of people who are currently or potentially in need of humanitarian assistance as a result of this issue, paying particular attention to those facing food insecurity.**
        *   **Clearly state the basis for your estimate,** citing specific data from your research or using a logical chain of reasoning based on the available information. If precise data is unavailable, explain the factors that make an exact number difficult to determine.

    **Structure your analysis into clearly defined sections with headings.**

    **Your analysis should be insightful, well-structured, evidence-based, and approximately 800-1000 words.**
    """

    response = model.generate_content(humanitarian_impact_prompt)
    humanitarian_impact_analysis = response.text

    print(f"Humanitarian impact analysis generated.")

    return {
        "humanitarian_impact_analysis": humanitarian_impact_analysis,
        "news": updated_news,  # Update the news in the state
    }


def economic_impact_node(state: "AgentState") -> Dict:
    """
    Performs research on and analyzes the microeconomic and macroeconomic impacts,
    focusing on the local economy, vulnerable regions, and overall macroeconomic situation.
    """
    topic = state["topic"]
    final_analysis = state["final_analysis"]
    background = state["background"]
    today = state["today"]

    complex_system_analysis = state.get("complex_system_analysis", "")
    quantum_analysis = state.get("quantum_analysis", "")
    entropy_analysis = state.get("entropy_analysis", "")
    recursive_exploration_analysis = state.get("recursive_exploration_analysis", "")
    dimensional_trascendence_analysis = state.get("dimensional_trascendence_analysis", "")
    actor_mapping_analysis = state.get("actor_mapping_analysis", "")

    research_query_prompt = f"""
    You are an expert economist with extensive knowledge of both microeconomic and macroeconomic analysis. 
    You are tasked with analyzing the economic impact of the following issue:

    **Topic:** {topic}

    **Current Analysis:**
    {final_analysis}

    **Background:**
    {background}

    **Analytical Frameworks:**
    (Consider the insights from these frameworks when formulating your queries)
    Complex Systems Analysis: {complex_system_analysis}
    Quantum Analysis: {quantum_analysis}
    Entropy Analysis: {entropy_analysis}
    Recursive Exploration Analysis: {recursive_exploration_analysis}
    Dimensional Transcendence Analysis: {dimensional_trascendence_analysis}
    Actor Mapping Analysis: {actor_mapping_analysis}

    **Instructions:**

    1.  **Identify Key Economic Aspects:** Based on the topic and provided analyses, identify 3-4 key aspects that are most likely to have significant economic ramifications. Consider:
        *   **Local Economic Impact:** How might local businesses, employment, and consumer behavior be affected?
        *   **Vulnerable Sectors:** Which economic sectors are likely to be most impacted?
        *   **Regional Effects:** Are there specific geographic regions that may experience more severe economic consequences?
        *   **Trade and Investment:** How might international trade flows and investment patterns be affected?
        *   **Market Dynamics:** What are the potential effects on prices, supply chains, and market competition?
        *   **Policy Implications:** What economic policy responses might be necessary or likely?

    2.  **Formulate Research Queries:** Formulate up to 4 specific and targeted research queries that will help gather comprehensive economic data and analysis.
        *   Use precise economic terminology and metrics.
        *   Specify relevant geographic regions, especially vulnerable areas.
        *   Focus on queries that are likely to yield concrete data, expert analyses, and diverse perspectives, particularly regarding the local and regional economic impacts.

    **Output Format**:
Only return valid JSON with two fields: "queries" (array of strings), and "recency_filter" (string).
Do not include any markdown fences or extra text.

Example:
{{
  "queries": ["query1", "query2"],
  "recency_filter": "month"
}}
    """

    try:
        response = model_queries.generate_content(
            research_query_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )

        # Attempt to parse the JSON response
        try:
            queries_data = Queries.model_validate_json(response.text)
        except ValidationError as e:
            print(f"Pydantic validation error: {e}")
            # Attempt to fix the JSON string
            try:
                fixed_json_str = response.text.strip()
                if fixed_json_str.startswith("```json"):
                    fixed_json_str = fixed_json_str[7:]
                if fixed_json_str.endswith("```"):
                    fixed_json_str = fixed_json_str[:-3]
                
                # Attempt to parse the JSON string to a Python dictionary
                data_dict = json.loads(fixed_json_str)

                # Ensure the dictionary has the expected structure
                if not isinstance(data_dict, dict) or "queries" not in data_dict or "recency_filter" not in data_dict:
                    raise ValueError("JSON does not have the expected structure")
                
                queries_data = Queries(**data_dict)

            except Exception as fix_error:
                print(f"Error attempting to fix JSON: {fix_error}")
                print(f"Failed to parse JSON: {response.text}")
                return {
                    "economic_impact_analysis": "",
                    "news": state.get("news", [])
                }

        research_queries = queries_data.queries
        recency_filter = queries_data.recency_filter or "month"
        print(f"Research queries for economic impact: {research_queries}")

    except Exception as e:
        print(f"Error generating research queries: {e}")
        research_queries = []
        recency_filter = "month"

    # --- Perform research ---
    economic_news = []
    for query in research_queries:
        try:
            response_text = news_search(query, recency_filter=recency_filter)
            economic_news.append(response_text)
        except Exception as e:
            print(f"Error fetching news for query '{query}': {e}")

    # Update the news in the state
    news = state.get("news", [])
    updated_news = news + economic_news

    # --- Analyze the economic impact ---
    economic_impact_prompt = f"""
    You are an expert economist with extensive knowledge of both microeconomic and macroeconomic analysis. 
    Analyze the economic impact of the following issue, integrating the provided 
    background information, specialized analyses, and research findings.

    **Topic:** {topic}

    **Current Analysis:**
    {final_analysis}

    **Background:**
    {background}

    **Specialized Analyses:**
    Complex Systems Analysis: {complex_system_analysis}
    Quantum Analysis: {quantum_analysis}
    Entropy Analysis: {entropy_analysis}
    Recursive Exploration Analysis: {recursive_exploration_analysis}
    Dimensional Transcendence Analysis: {dimensional_trascendence_analysis}
    Actor Mapping Analysis: {actor_mapping_analysis}

    **Research:**
    {updated_news}

    **Today's Date:** {today}

    **Instructions:**

    1.  **Local Economic Impacts:**
        *   Analyze the potential impacts on local businesses, employment, and consumer behavior.
        *   Consider factors such as local industries, employment rates, housing markets, and local government finances.
        *   Identify any regions that might be particularly vulnerable to negative impacts.

    2.  **Impacts on Vulnerable Sectors:**
        *   Assess how the issue might disproportionately affect economically disadvantaged or vulnerable sectors.
        *   Consider factors such as pre-existing economic disparities, dependence on specific industries, and limited access to resources.

    3.  **Microeconomic Analysis:**
        *   Analyze the potential impacts on specific industries, businesses, and consumers.
        *   Consider factors such as supply chain disruptions, changes in production costs, price fluctuations, shifts in consumer demand, and impacts on employment.
        *   Provide specific examples and, where possible, quantify the potential impacts using data or estimates.

    4.  **Macroeconomic Analysis:**
        *   Analyze the potential impacts on the broader economy, including GDP growth, inflation, unemployment, and trade.
        *   Consider the implications for financial markets (e.g., stock markets, bond markets, exchange rates).
        *   Evaluate potential government policy responses (e.g., fiscal stimulus, monetary policy adjustments, trade policies) and their likely consequences.

    5.  **International Economic Implications:**
        *   Analyze the potential impacts on international trade flows, global supply chains, and international financial stability.
        *   Consider the implications for other countries or regions.

    6.  **Long-Term Economic Consequences:**
        *   Assess the potential long-term effects of the issue on economic growth, development, and structural changes in the economy (both globally and regionally).
        *   Consider factors such as investment, innovation, technological advancements, and shifts in economic power.

    **Structure your analysis into clearly defined sections with headings.**

    **Do not add any introductory statement like "Okay, here's a detailed economic analysis...", just output the requested analysis.**

    **Your analysis should be insightful, well-structured, evidence-based, and approximately 800-1000 words.**
    """

    response = model.generate_content(economic_impact_prompt)
    economic_impact_analysis = response.text

    print("Economic impact analysis generated.")

    return {
        "economic_impact_analysis": economic_impact_analysis,
        "news": updated_news
    }
