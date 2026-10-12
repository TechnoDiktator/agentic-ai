from src.tools.tools import web_search ,  scrape_url
from src.pipeline.pipeline import run_research_pipeline


# result = web_search.invoke("Latest research on using AI for tacke;ling climate change")
# print(result)


# print("==================================CONTENT===========================")

# print(scrape_url("https://aiweekly.co"))


topic = "The impact of AI on the job market in 2026"

run_research_pipeline(topic=topic)