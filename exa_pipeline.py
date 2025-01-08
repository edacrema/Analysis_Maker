import os
from dotenv import load_dotenv
from typing import List, Literal
from langchain_exa import ExaSearchRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

EXA_API_KEY = os.getenv('EXA_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

@tool
def retrieve_web_content(query: str) -> List[str]:
    """Function to retrieve usable documents for AI assistant"""
    # Initialize the Exa Search retriever
    retriever = ExaSearchRetriever(k=20, highlights=True, exa_api_key=EXA_API_KEY, use_autoprompt=True)

    # Define how to extract relevant metadata from the search results
    document_prompt = PromptTemplate.from_template(
        """
    <source>
        <url>{url}</url>
        <highlights>{highlights}</highlights>
    </source>
    """
    )

    # Create a chain to process the retrieved documents
    document_chain = (
        RunnableLambda(
            lambda document: {
                "highlights": document.metadata.get("highlights", "No highlights"),
                "url": document.metadata["url"],
            }
        )
        | document_prompt
    )

    # Execute the retrieval and processing chain
    retrieval_chain = retriever | document_chain.map()

    # Retrieve and return the documents
    documents = retrieval_chain.invoke(query)
    print(documents)
    return documents

model = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0, api_key=ANTHROPIC_API_KEY).bind_tools([retrieve_web_content])

# Determine whether to continue or end
def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    return "tools" if last_message.tool_calls else END

# Function to generate model responses
def call_model(state: MessagesState):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

# Define the workflow graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode([retrieve_web_content]))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# Initialize memory
checkpointer = MemorySaver()

# Compile the workflow into a runnable
app = workflow.compile(checkpointer=checkpointer)