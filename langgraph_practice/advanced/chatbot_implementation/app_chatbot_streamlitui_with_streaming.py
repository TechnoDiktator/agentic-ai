
user_message = st.chat_input("Message the assistant")

if user_message:
    st.session_state.chat_messages.append(
        {"role": "user", "content": user_message}
    )

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        try:
            config = {
                "configurable": {
                    "thread_id": st.session_state.chat_thread_id
                }
            }

            def stream_response():
                for chunk, metadata in chatbot.stream(
                    {"messages": [HumanMessage(content=user_message)]},
                    config=config,
                    stream_mode="messages",
                ):
                    # Only display actual text content.
                    content = chunk.content

                    if isinstance(content, str) and content:
                        yield content

                    elif isinstance(content, list):
                        for block in content:
                            if (
                                isinstance(block, dict)
                                and block.get("type") == "text"
                            ):
                                text = block.get("text", "")
                                if text:
                                    yield text

            # Stream chunks directly into the assistant's chat bubble.
            assistant_message = st.write_stream(stream_response())

            # Save the completed response for subsequent reruns.
            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message,
                }
            )

        except Exception:
            st.error(
                "The chatbot could not complete this request. "
                "Check the API configuration and try again."
            )
