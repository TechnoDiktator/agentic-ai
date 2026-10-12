import os

import certifi
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv

# Load model credentials and other settings from the project's .env file.
load_dotenv()

# Git Bash may provide a POSIX certificate path that Windows Python cannot open.
ssl_cert_file = os.getenv("SSL_CERT_FILE")
if not ssl_cert_file or not os.path.isfile(ssl_cert_file):
    os.environ["SSL_CERT_FILE"] = certifi.where()

# Both agents and chains share this chat model.
llm = ChatOpenAI(model = "gpt-4.1-mini",temperature=0)

# Build an agent that searches the web and returns research sources/results.
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
    )

# Build an agent that opens URLs and extracts readable page content.
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
    )


# This prompt tells the writer what report sections and source details to include.
# It expects a topic and gathered research to be supplied when the chain runs.

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Write the report in Markdown. Format inline equations with $...$ and standalone
equations on separate lines with $$...$$. Do not wrap equations in plain square
brackets.

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()




# The critic prompt asks for a consistent score, strengths, improvements, and verdict.
# It expects the completed report as its `report` input.

critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
