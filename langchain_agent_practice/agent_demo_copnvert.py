# Standard-library and package imports used throughout the notebook.
import os
import certifi
import requests

from dotenv import load_dotenv

# LangChain integrations for the chat model, tools, and prompt hub.
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub

from langchain.agents import create_react_agent, AgentExecutor

# =======================
# LOAD ENV VARIABLES
# ======================

# Use certifi's trusted certificate bundle for HTTPS requests.
os.environ["SSL_CERT_FILE"] = certifi.where()

# Read API keys from the .env file into the process environment.
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")

# Configure Tavily to return at most two web-search results per query.
search_tool = TavilySearchResults(max_results=2)

# Expose the Weatherstack request as a tool the agent can call with a city name.
@tool
def get_weather_data(city: str) -> str:
    """Fetch current weather information for a city."""
    url = (
        f"http://api.weatherstack.com/current?"
        f"access_key={WEATHERSTACK_API_KEY}&query={city}"
    )
    response = requests.get(url)
    data = response.json()

    if "current" not in data:
        return f"Could not fetch weather data for {city}"

    return (
        f"City: {city}\n"
        f"Temperature: {data['current']['temperature']}°C\n"
        f"Weather: {data['current']['weather_descriptions'][0]}\n"
        f"Humidity: {data['current']['humidity']}%"
    )

# Test the search tool directly before giving it to the agent.
result = search_tool.invoke("What is the latest news on Ai")

print(result)

# Configure the chat model used by the agent.
llm = ChatOpenAI(
    model = "gpt-4.1-mini" ,
    temperature=0,
    api_key=OPENAI_API_KEY
)

# Make a simple test call to confirm the model connection works.
llm.invoke("What year is it")

# A model's knowledge can be out of date; use web search for current facts.

# Instantiate the same model configuration as a standalone object.
ChatOpenAI(model="gpt-4.1-mini")

# Download the ReAct prompt template from LangSmith for the agent to use.
from langsmith import Client

prompt = Client().pull_prompt("hwchase17/react")

# Give the agent both web search and current-weather tools.
tools = [search_tool, get_weather_data]

# Combine the model, available tools, and prompt into a ReAct agent.
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# Wrap the agent with the executor that runs its tool-call loop.
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

# Run the agent on a question that needs a factual answer and current weather.
response = agent_executor.invoke({
    "input": (
        "Find the capital of India"
        "and then find Meerut's current weather."
    )
})

# Display the final answer returned by the executor.
print("\n========================")
print("FINAL OUTPUT")
print("========================\n")

print(response["output"])
