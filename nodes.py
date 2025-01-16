import os
from datetime import datetime
import re
from typing import List, TypedDict, Dict, Optional  # Import Dict from typing
import google.generativeai as genai
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI

from langchain_community.utilities import GoogleSerperAPIWrapper

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, ValidationError  
from prompts import entropy_prompt, actor_mapping_prompt, game_theory_prompt, complex_systems_prompt, analyst_prompt

from perplexity_pipeline import news_search

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
    entropy_analysis: str
    actor_mapping_analysis: str
    game_theory_analysis: str
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
model_queries = genai.GenerativeModel(model_name='gemini-1.5-pro', generation_config = genai.types.GenerationConfig(temperature=0.0))  # Adjust the temperature as needed

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

    # Extract the final analysis text using the function
    final_analysis = get_second_text_part_from_object(response)
    print(final_analysis)

    return {'entropy_analysis': final_analysis}


def get_second_text_part_from_object(response_obj):
    """
    Extract the second text chunk from the first candidate,
    assuming we have something like:
    
    response_obj.candidates[0].content.parts == [
       {"text": "FIRST PART"},
       {"text": "SECOND PART"}  # what we want
    ]
    """
    # Access the list of candidates (public attribute)
    cands = response_obj.candidates
    if not cands:
        return "No candidates found."
    
    # Each candidate has a .content, which has .parts
    parts = cands[0].content.parts
    if len(parts) < 2:
        # If there's only one part or none, just gracefully handle it
        return parts[0].text if parts else "No parts found."
    
    # Otherwise, return the second part
    return parts[1].text



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

    # Extract the final analysis text using the function
    final_analysis = get_second_text_part_from_object(response)
    print(final_analysis)

    return {'actor_mapping_analysis': final_analysis}

def complex_systems_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    actor_map=state['actor_mapping_analysis']
    prompt = f"""
    {complex_systems_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    This is the background: {background}
    This is the actor mapping: {actor_map}

    """
    response = model_2.generate_content(prompt)

    # Extract the final analysis text using the function
    final_analysis = get_second_text_part_from_object(response)
    print(final_analysis)

    return {'complex_system_analysis': final_analysis}

def game_theory_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    background = state['background']
    actor_map=state['actor_mapping_analysis']
    complex_sys=state['complex_system_analysis']
    prompt = f"""
    {game_theory_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
    This is the background: {background}
    This is the actor mapping: {actor_map}
    This is the complex system analysis: {complex_sys}
    """
    response = model_2.generate_content(prompt)

    # Extract the final analysis text using the function
    final_analysis = get_second_text_part_from_object(response)
    print(final_analysis)

    return {'game_theory_analysis': final_analysis}

def unified_analysis_node(state: AgentState):
    topic = state["topic"]
    today = state["today"]
    article_summary = state["news"]
    previous_analysis = state.get("final_analysis", "")  # Use get() with default value
    areas_for_improvement = state["areas_for_improvement"]
    background = state["background"]
    complex_system_analysis = state["complex_system_analysis"]
    entropy_analysis = state["entropy_analysis"]
    actor_mapping_analysis = state["actor_mapping_analysis"]
    game_theory_analysis = state["game_theory_analysis"]

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

    **Entropy Analysis**:
    {entropy_analysis}

    **Actor Mapping Analysis**:
    {actor_mapping_analysis}

    **Game Theory Analysis**:
    {game_theory_analysis}

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
    MAX_REVISIONS = 2  # Maximum number of revisions allowed
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

    1.  **Clarity and Coherence:** 
        - Is the analysis well-structured, easy to understand, and logically sound?
        - Do paragraphs flow in a logical order, building upon each other without abrupt gaps or leaps?

    2.  **Depth of Analysis:** 
        - Does the analysis go beyond superficial observations and offer substantive insight into the topic?
        - Does it explore underlying causes, implications, and potential contradictions?

    3.  **Integration of Frameworks:** 
        - Does the analysis effectively integrate the different analytical frameworks (e.g., complex systems, game theory, entropy, actor mapping)?
        - Are the frameworks used in a complementary way rather than in isolation?

    4.  **Evidence and Support:** 
        - Are the claims supported by evidence from the provided background, news references, or specialized analyses?
        - Does the analysis demonstrate accurate cross-referencing of sources and data points?
        - Are there any instances where assertions appear unfounded or contradictory?

    5.  **Originality and Insightfulness:** 
        - Does the analysis offer new or unique insights into the situation?
        - Does it highlight any nuanced viewpoints or unexpected connections among actors or factors?

    6.  **Balance and Completeness:** 
        - Does the analysis address all major facets of the situation without obvious omission?
        - Are multiple perspectives (e.g., political, economic, social) represented fairly?

    7.  **Potential Future Scenarios:** 
        - Are the potential future scenarios well-reasoned, plausible, and connected back to the evidence and frameworks presented?
        - Do they meaningfully extend from the current dynamics outlined in the analysis?

    **Based on your evaluation, answer the following questions:**

    1.  **Revision Needed (YES/NO):** 
        - Does this analysis require further revision or refinement to improve its quality and completeness?

    2.  **Areas for Improvement:** 
        - Briefly describe the specific areas where the analysis is lacking or could be improved 
          (e.g., "The analysis lacks depth in integrating game theory," or "The future scenarios are vague and not linked to the actor mapping").

    3.  **Research Queries (Only if You Answered YES Above):** 
        - Generate 2-3 precise and actionable research queries that would help address the identified weaknesses. 
        - Formulate each query so that it is specific enough to yield highly relevant results from a search engine (like Google Serper).

    **Guidelines for Research Query Generation:**

    *   **Specificity:** 
        - Ensure queries are focused and likely to retrieve pertinent information.
    *   **Comprehensiveness:** 
        - Capture various dimensions of the weakness (e.g., historical data, current developments, expert viewpoints).
    *   **Diversity:** 
        - Avoid overlapping queries. Instead, target different angles of the area that needs improvement.
    *   **Actionable:** 
        - Phrase queries such that their answers would directly strengthen the relevant sections of the analysis.

    **Example Research Queries (For Illustration Only):**

    *   **Scenario:** Evaluating the influence of corporate lobbying on climate policy.
        *   **Area for Improvement:** "Insufficient detail on how specific corporate lobbying efforts have shaped legislation."
        *   **Research Queries:**
            - "Case studies of fossil fuel lobby influence on U.S. climate policy in 2022"
            - "Corporate lobbying disclosure data AND climate legislation 2021-2023"
            - "Influence of renewable energy lobby vs fossil fuel lobby in EU climate directives"

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
    entropy_analysis = state.get("entropy_analysis", "")
    actor_mapping_analysis = state.get("actor_mapping_analysis", "")
    game_theory_analysis = state.get("game_theory_analysis", "")

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
    Entropy Analysis: {entropy_analysis}
    Actor Mapping Analysis: {actor_mapping_analysis}
    Game Theory Analysis: {game_theory_analysis}

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
    Entropy Analysis: {entropy_analysis}
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
    
    **Do not add any introductory statement like "Here is the actor mapping analysis...", just output the requested analysis.**
    """

    response = model.generate_content(humanitarian_impact_prompt)
    humanitarian_impact_analysis = response.text

    print(f"Humanitarian impact analysis generated.")

    return {
        "humanitarian_impact_analysis": humanitarian_impact_analysis,
        "news": updated_news,  # Update the news in the state
    }


