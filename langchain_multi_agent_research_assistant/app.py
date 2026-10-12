import re
import time

import streamlit as st

st.set_page_config(
	page_title="Research Desk",
	page_icon="R",
	layout="wide",
)

from src.pipeline.pipeline import run_research_pipeline


def _format_display_math(markdown: str) -> str:
	"""Wrap standalone bracketed LaTeX equations in Streamlit math delimiters."""
	return re.sub(
		r"(?m)^\s*\[\s*(\\.+?)\s*\]\s*$",
		lambda match: f"$$\n{match.group(1)}\n$$",
		markdown,
	)


st.title("Research Desk")
st.caption(
	"Search current sources, read a relevant page, draft a report, and review it."
)

with st.sidebar:
	st.subheader("Pipeline")
	st.markdown(
		"1. Search the web\n"
		"2. Read a relevant source\n"
		"3. Draft a research report\n"
		"4. Critique the report"
	)
	st.caption("Results are generated when you submit a topic.")

with st.form("research_form"):
	topic = st.text_input(
		"Research topic",
		placeholder="For example: How is AI changing entry-level jobs?",
	)
	submitted = st.form_submit_button("Run research", type="primary")

if submitted:
	if not topic.strip():
		st.warning("Enter a topic to start the research pipeline.")
	else:
		try:
			with st.spinner("Searching, reading, drafting, and reviewing..."):
				started_at = time.perf_counter()
				result = run_research_pipeline(topic.strip())
				elapsed = time.perf_counter() - started_at

			st.session_state["research_topic"] = topic.strip()
			st.session_state["research_result"] = result
			st.session_state["research_elapsed"] = elapsed
		except Exception as error:
			st.error("The research pipeline could not complete.")
			st.caption(str(error))

if "research_result" in st.session_state:
	result = st.session_state["research_result"]

	st.divider()
	st.subheader(st.session_state["research_topic"])
	st.caption(f"Completed in {st.session_state['research_elapsed']:.1f} seconds")

	report_tab, critique_tab, sources_tab, search_tab, scraped_tab = st.tabs(
		["Report", "Critique", "Sources", "Search results", "Scraped content"]
	)

	with report_tab:
		report = result.get("report", "")
		if report:
			display_report = _format_display_math(report)
			topic_slug = re.sub(r"[^a-z0-9]+", "-", st.session_state["research_topic"].lower()).strip("-")
			st.download_button(
				"Download report (.md)",
				data=display_report,
				file_name=f"{topic_slug or 'research-report'}.md",
				mime="text/markdown",
			)
			st.markdown(display_report)
		else:
			st.info("No report was returned.")

	with critique_tab:
		st.markdown(_format_display_math(result.get("feedback", "No critique was returned.")))

	with sources_tab:
		sources = result.get("sources", [])
		if sources:
			for index, source in enumerate(sources):
				st.markdown(f"**{source['title']}**")
				if source.get("selected_for_scraping"):
					st.caption("Selected by the reader agent; scraping was attempted.")
				else:
					st.caption("Found by web search.")
				st.link_button(
					f"Open {source['url'].split('/')[2]}",
					source["url"],
					key=f"source-{index}",
				)
				st.divider()
		else:
			st.info("No source URLs were captured from this run.")

	with search_tab:
		st.text(result.get("search_results", "No search results were returned."))

	with scraped_tab:
		st.text_area(
			"Extracted page text",
			value=result.get("scraped_content", "No page content was returned."),
			height=420,
			disabled=True,
			label_visibility="collapsed",
		)
