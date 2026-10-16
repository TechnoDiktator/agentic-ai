import os
import sys
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Load the practice project's .env regardless of the directory Streamlit starts in.
project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")

st.set_page_config(page_title="Agentic Chatbot", page_icon="AI", layout="centered")

if not os.getenv("OPENAI_API_KEY"):
	st.error("OPENAI_API_KEY is missing. Add it to the langgraph_practice .env file.")
	st.stop()

# Make the backend import work when this app is launched from another directory.
backend_directory = str(Path(__file__).resolve().parent)
if backend_directory not in sys.path:
	sys.path.insert(0, backend_directory)

from agentic_chatbot_backend import chatbot


if "chat_thread_id" not in st.session_state:
	st.session_state.chat_thread_id = uuid4().hex
if "chat_messages" not in st.session_state:
	st.session_state.chat_messages = []

st.title("Agentic Chatbot")
st.caption("A LangGraph chatbot with conversation memory for this session.")

with st.sidebar:
	st.subheader("Conversation")
	st.caption("This chat is kept in memory and will reset when the app process restarts.")
	if st.button("New chat", type="secondary"):
		st.session_state.chat_thread_id = uuid4().hex
		st.session_state.chat_messages = []
		st.rerun()

if not st.session_state.chat_messages:
	with st.chat_message("assistant"):
		st.markdown("Hi! Ask me a question to start a conversation.")

for message in st.session_state.chat_messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])

user_message = st.chat_input("Message the assistant")
if user_message:
	st.session_state.chat_messages.append({"role": "user", "content": user_message})

	with st.chat_message("user"):
		st.markdown(user_message)

	with st.chat_message("assistant"):
		with st.spinner("Thinking..."):
			try:
				config = {
					"configurable": {"thread_id": st.session_state.chat_thread_id}
				}
				response = chatbot.invoke(
					{"messages": [HumanMessage(content=user_message)]},
					config=config,
				)
				assistant_message = response["messages"][-1].content
				st.markdown(assistant_message)
				st.session_state.chat_messages.append(
					{"role": "assistant", "content": assistant_message}
				)
			except Exception:
				st.error("The chatbot could not complete this request. Check the API configuration and try again.")
