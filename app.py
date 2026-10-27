
import streamlit as st

from conversation_processor import compress_conversation, to_json
from correction_detector import find_corrections


st.set_page_config(
    page_title="Local Conversation Processor",
    page_icon="💬",
    layout="wide",
)

SAMPLE = """The meeting is scheduled for Thursday.
I checked the official calendar.
The meeting is scheduled for Friday, not Thursday.
We need to finish the presentation slides by Monday.
The meeting is scheduled for Thursday."""


if "raw_text" not in st.session_state:
    st.session_state.raw_text = SAMPLE

st.title("Local Conversation Processing and Compression")
st.write(
    "Clean, organize and compress conversations using local "
    "rule-based processing. No external AI API is required."
)

if st.button("Load Sample Conversation"):
    st.session_state.raw_text = SAMPLE
    st.session_state.pop("processing_result", None)

raw_text = st.text_area(
    "Enter your conversation",
    key="raw_text",
    height=220,
    placeholder="Paste a conversation here...",
)

max_chunk_words = st.number_input(
    "Maximum words per chunk",
    min_value=10,
    max_value=1000,
    value=100,
    step=10,
)

if st.button("Process Conversation", type="primary"):
    if not raw_text.strip():
        st.warning("Please enter a conversation first.")
        st.session_state.pop("processing_result", None)
    else:
        try:
            corrections = find_corrections(raw_text)

            result = compress_conversation(
                raw_text,
                max_chunk_words=int(max_chunk_words),
                correction_events=corrections,
            )

            st.session_state.processing_result = result

        except Exception as error:
            st.error(f"Processing failed: {error}")
            st.session_state.pop("processing_result", None)


result = st.session_state.get("processing_result")

if result:
    st.divider()
    st.header("Processing Metrics")

    cols = st.columns(4)

    cols[0].metric("Original words", result["original_words"])
    cols[1].metric("Summary words", result["summary_words"])
    cols[2].metric("Duplicates removed", result["duplicates_removed"])
    cols[3].metric("Topics identified", result["topic_count"])

    cols = st.columns(4)

    cols[0].metric(
        "Summary reduction",
        f'{result["summary_reduction_percentage"]}%',
    )
    cols[1].metric("Final output words", result["final_output_words"])
    cols[2].metric("Chunks created", result["chunk_count"])
    cols[3].metric("Possible corrections", result["correction_count"])

    st.caption(result["metrics_note"])

    st.subheader("Estimated Token Usage")

    cols = st.columns(3)

    cols[0].metric(
        "Original",
        result["original_estimated_tokens"],
    )
    cols[1].metric(
        "Summary",
        result["summary_estimated_tokens"],
    )
    cols[2].metric(
        "Final output",
        result["final_estimated_tokens"],
    )

    st.caption(
        "Token values are rough estimates, not exact tokenizer results."
    )

    st.divider()
    st.header("Compressed Conversation")

    st.text_area(
        "Summary and correction history",
        value=result["compressed_text"],
        height=300,
        disabled=True,
    )

    st.download_button(
        "Download compressed text",
        data=result["compressed_text"],
        file_name="compressed_conversation.txt",
        mime="text/plain",
    )

    st.download_button(
        "Export complete results as JSON",
        data=to_json(result),
        file_name="conversation_results.json",
        mime="application/json",
    )

    st.divider()
    st.header("Topic Groups")

    for topic, statements in result["topics"].items():
        with st.expander(topic, expanded=True):
            for statement in statements:
                st.markdown(f"- {statement}")

    st.divider()
    st.header("Important Context")

    if result["important_statements"]:
        for statement in result["important_statements"]:
            st.markdown(f"- {statement}")
    else:
        st.write("No statements matched the importance rules.")

    st.divider()
    st.header("Correction History")

    if result["correction_history"]:
        for index, event in enumerate(
            result["correction_history"], start=1
        ):
            with st.expander(f"Correction {index}"):
                st.write(
                    "**Earlier statement:**",
                    event["original"] or "Not identified",
                )
                st.write(
                    "**Latest statement:**",
                    event["correction"] or "Not identified",
                )
                st.write("**Status:**", event["status"])

        st.info(
            "Correction detection uses keyword and word-overlap rules. "
            "Review flagged items because they may not always be "
            "genuine corrections."
        )
    else:
        st.write("No possible corrections detected.")

    st.divider()
    st.header("Conversation Chunks")

    for chunk in result["chunks"]:
        with st.expander(
            f'Chunk {chunk["chunk_number"]} '
            f'({chunk["word_count"]} words)'
        ):
            for statement in chunk["statements"]:
                st.markdown(f"- {statement}")

    st.caption(
        "Processing time: "
        f'{result["processing_time_seconds"]} seconds'
    )
