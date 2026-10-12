from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from langchain_core.messages import HumanMessage

def _get_search_sources(messages: list) -> list[dict[str, str | bool]]:
    """Extract titled source links from the web-search tool response."""
    sources = []

    for message in messages:
        if getattr(message, "name", None) != "web_search":
            continue

        for result in str(message.content).split("\n----\n"):
            title = ""
            url = ""
            for line in result.splitlines():
                if line.startswith("Title:"):
                    title = line.removeprefix("Title:").strip()
                elif line.startswith("URL:"):
                    url = line.removeprefix("URL:").strip()

            if url:
                sources.append({
                    "title": title or url,
                    "url": url,
                    "selected_for_scraping": False,
                })

    return sources


def run_research_pipeline(topic : str) -> dict:

    # Accumulate the search text, scraped page text, report, and critique here.
    state = {}

    # Stage 1: ask the search agent to find recent sources for the topic.
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [HumanMessage(
            content=f"Find recent, reliable and detailed information about: {topic}"
        )]
    })
    # Store the agent's final message, including result details.
    state["search_results"] = search_result["messages"][-1].content
    # Preserve the source URLs from the actual web-search tool response.
    state["sources"] = _get_search_sources(search_result["messages"])

    print("\n search result ",state['search_results'])


    # Stage 2: have the reader choose a relevant result and scrape its URL.
    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [HumanMessage(content=(
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            # Limit the search text sent into this prompt to keep the request focused.
            f"Search Results:\n{state['search_results'][:800]}"
        ))]
    })

    # Record which source URL the reader agent selected for scraping.
    selected_url = None
    for message in reader_result["messages"]:
        for tool_call in getattr(message, "tool_calls", []):
            if tool_call.get("name") == "scrape_url":
                selected_url = (tool_call.get("args") or {}).get("url")
                break
        if selected_url:
            break

    if selected_url:
        matching_source = next(
            (source for source in state["sources"] if source["url"] == selected_url),
            None,
        )
        if matching_source:
            matching_source["selected_for_scraping"] = True
        else:
            state["sources"].append({
                "title": selected_url,
                "url": selected_url,
                "selected_for_scraping": True,
            })

    # Store the reader agent's final message for the writer to use as evidence.
    state['scraped_content'] = reader_result["messages"][-1].content

    print("\nscraped content: \n", state['scraped_content'])


    # Stage 3: combine search and scraped text into the writer's research input.

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    # Store the writer's report, based on the topic, search results, and scraped text.
    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    print("\n Final Report\n",state['report'])


    # Stage 4: review the draft and store the critic's score and written feedback.

    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report":state['report']
    })

    print("\n critic report \n", state['feedback'])

    # Return all intermediate results, the draft, and the review to the caller.
    return state