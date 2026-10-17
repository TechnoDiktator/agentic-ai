from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
import sqlite3


load_dotenv()

## If you have openAI API key and want to use OpenAI models, uncomment the line below and comment the Gemini LLM initialization

# llm = ChatOpenAI()

## if you want to use Gemini LLM 
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0.7,
    streaming=True,
)


class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]



def chat_node(state: ChatState, config: RunnableConfig):
    response_chunk = None
    for chunk in llm.stream(state["messages"], config=config):
        response_chunk = chunk if response_chunk is None else response_chunk + chunk

    if response_chunk is None:
        raise RuntimeError("The chat model returned no response chunks.")

    return {"messages": [AIMessage(content=response_chunk.content)]}


conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpoint = SqliteSaver(conn)

graph = StateGraph(ChatState)

# add nodes
graph.add_node('chat_node', chat_node)

#add edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


chatbot = graph.compile(checkpointer=checkpoint)


def get_all_threads():
    all_threads = set()
    for ckpt in checkpoint.list(None):
        all_threads.add(ckpt.config['configurable']['thread_id'])

    return list(all_threads)


   
