import httpx
import streamlit as st

from client import download, saved_turn


def render_result(result, user_id):
    text = (result.get("followup") or {}).get("followup_text") or (result.get("answer") or {}).get("text")
    st.markdown(text or "Faro could not produce an answer.")
    documents = (result.get("answer") or {}).get("documents", [])
    if documents:
        with st.expander("Source documents"):
            for index, document in enumerate(documents):
                st.write(document["name"])
                with st.expander(f"References — {document['name']}"):
                    st.text("\n".join(document["references"]))
                try:
                    data = download(user_id, result, index)
                    st.download_button("Download document", data, file_name=document["name"],
                                       key=f"{result['turn_id']}-{index}", on_click="ignore")
                except httpx.HTTPError:
                    st.warning("This document is not available under your current access.")
    with st.expander("Checked evidence"):
        if result.get("verification"):
            st.json(result["verification"])
        elif result.get("followup"):
            st.write("Waiting for your clarification before checking an answer.")
        else:
            st.write("No answer was produced from the available data.")
    with st.expander("Demo details"):
        st.write("Question understood:", result["rewrite"]["question"])
        try:
            turn = saved_turn(user_id, result)
            st.write(f"Time: {turn['elapsed_ms'] / 1000:.1f} seconds")
            attempts = turn["model_attempts"] or {}
            if attempts:
                st.table([{"Service": service, "Model attempts": details["attempts"],
                           "Results": ", ".join(outcome for call in details["calls"] for outcome in call)}
                          for service, details in attempts.items()])
            reused = [event["service"] for event in turn["cache"] if event["result_source"] == "cache"]
            st.write("Reused saved work: " + (", ".join(reused) or "none"))
        except httpx.HTTPError:
            st.caption("Saved details are unavailable.")


def render_messages(user_id):
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_result(message["result"], user_id)
