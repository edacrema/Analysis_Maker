import os
from datetime import datetime
from typing import List, TypedDict
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from langchain_community.utilities import GoogleSerperAPIWrapper

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from prompts import  prompt_news, quantum_prompt, entropy_prompt, \
    recursive_exploration_prompt, complex_systems_prompt, dimensional_trascendence_prompt, actor_mapping_prompt, analyst_prompt

from exa_pipeline import app

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

openai_api_key = os.getenv('OPENAI_API_KEY')

# Adjust your typed dictionary as needed
class AgentState(TypedDict):
    topic: str
    question_links: List[str]
    today: str
    news: List[str]
    complex_system_analysis: str
    quantum_analysis: str
    entropy_analysis: str
    recursive_exploration_analysis: str
    dimensional_trascendence_analysis: str
    actor_mapping_analysis: str
    final_analysis: str

class Queries(BaseModel):
    queries: List[str]


# Example chat model
model = ChatOpenAI(
    model_name='gpt-4o-mini-2024-07-18',
    temperature=0.1
)

model_2 = ChatOpenAI(model_name='gpt-4o', temperature=0.1)

model_3 = ChatOpenAI(model_name='o1-preview-2024-09-12')

model_4 = ChatOpenAI(model_name='o1-mini')


def news_node(state: AgentState):
    topic = state['topic']
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        queries = model.with_structured_output(Queries).invoke([
            SystemMessage(content=prompt_news),
            HumanMessage(content=f"This is the topic: {topic}\n\nHere is today's date: {today}")
        ])
        news = state.get('news', [])
        for q in queries.queries:
            response = app.invoke({"messages": [HumanMessage(content=f'{q}')]},
                                  config={"configurable": {"thread_id": 44}}, )
            news.append(response["messages"][-1].content)
        print(news)
        return {'news': news, 'today': today}
    except Exception as e:
        print(f"Error in news_node: {str(e)}")
        return {'news': [], 'today': today}

def quantum_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    messages = [HumanMessage(f"""
    {quantum_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}""")]
    response = model_4.invoke(messages)
    quantum_analysis = response.content.strip()
    print(quantum_analysis)
    return {'quantum_analysis': quantum_analysis}

def entropy_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    messages = [HumanMessage(f"""
    {entropy_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}""")]
    response = model_3.invoke(messages)
    entropy_analysis = response.content.strip()
    print(entropy_analysis)
    return {'entropy_analysis': entropy_analysis}

def recursive_exploration_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    messages = [HumanMessage(f"""
    {recursive_exploration_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}"""),]
    response = model_4.invoke(messages)
    recursive_exploration = response.content.strip()
    print(recursive_exploration)
    return {'recursive_exploration_analysis': recursive_exploration}

def dimensional_trascendence_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']

    messages = [HumanMessage(f"""
    {dimensional_trascendence_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}"""
    )]
    response = model_4.invoke(messages)
    dimensional_trascendence = response.content.strip()
    print(dimensional_trascendence)
    return {'dimensional_trascendence_analysis': dimensional_trascendence}

def actor_mapping_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    messages = [HumanMessage(f"""
    {actor_mapping_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
""")]
    response = model_4.invoke(messages)
    actor_mapping = response.content.strip()
    print(actor_mapping)
    return {'actor_mapping_analysis': actor_mapping}

def complex_systems_node(state: AgentState):
    topic = state['topic']
    article_summary = state['news']
    messages = [HumanMessage(f"""
    {complex_systems_prompt}
    This is the topic: {topic}
    This is the article summary: {article_summary}
""")]
    response = model_4.invoke(messages)
    complex_system_analysis = response.content.strip()
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

    human_content = f"""
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

    # Invoke the model with our system and human messages
    messages = [
        HumanMessage(content=human_content),
    ]

    response = model_3.invoke(messages)
    final_analysis = response.content.strip()
    print(final_analysis)

    return {'final_analysis': final_analysis}