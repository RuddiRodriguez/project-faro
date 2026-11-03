"""A local question-and-answer screen over Faro's existing services."""
import json
from pathlib import Path

import httpx
import streamlit as st

from client import ask, sign_in
from views import render_messages


DEMO = Path(__file__).resolve().parents[1]


def reset_question():
    st.session_state.messages = []
    st.session_state.conversation_id = None
    st.session_state.previous_answer_id = None


def initialize_state():
    if "messages" not in st.session_state:
        reset_question()
    st.session_state.setdefault("access", None)


def render_sidebar():
    with st.sidebar:
        st.header("Demo account")
        st.caption("Choose a test account. This is not a password sign-in.")
        if st.session_state.access is None:
            users = json.loads((DEMO / "local_data/demo_dataset/users.json").read_text())
            with st.form("login"):
                user_id = st.selectbox("User", [u["user_id"] for u in users if u["status"] == "active"])
                submitted = st.form_submit_button("Enter demo")
            if submitted:
                try:
                    st.session_state.access = sign_in(user_id)
                    reset_question()
                    st.rerun()
                except httpx.HTTPError:
                    st.error("This account could not be verified. Check that the local APIs are running.")
        else:
            access = st.session_state.access
            st.write("User:", access["user_id"])
            st.write("Company:", access["company_id"])
            st.caption("Allowed data: " + ", ".join(access["permitted_scope_ids"]))
            if st.button("New question"):
                reset_question()
                st.rerun()
            if st.button("Switch account"):
                reset_question()
                st.session_state.access = None
                st.rerun()


def main():
    st.set_page_config(page_title="Faro", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")
    st.html("<style>" + (Path(__file__).parent / "style.css").read_text() + "</style>")
    st.title("Faro")
    st.caption("Ask about your company data. Read the answer and the documents behind it.")
    initialize_state()
    render_sidebar()
    if st.session_state.access is None:
        st.info("Choose a demo account to begin. Data and replies are in English.")
        return
    access = st.session_state.access
    render_messages(access["user_id"])
    question = st.chat_input("Ask about your data, or reply to Faro’s clarification")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.spinner("Reading your data and checking the answer…"):
                result = ask(access["user_id"], question, st.session_state.conversation_id,
                             st.session_state.previous_answer_id)
            st.session_state.messages.extend([
                {"role": "user", "content": question}, {"role": "assistant", "result": result}])
            st.session_state.conversation_id = result["conversation_id"] if result["followup"] else None
            st.session_state.previous_answer_id = (result["conversation_id"]
                if (result.get("verification") or {}).get("status") == "verified" else None)
            st.rerun()
        except httpx.HTTPError as error:
            st.error("The request did not finish. Your previous conversation is still shown.")
            if isinstance(error, httpx.HTTPStatusError):
                st.caption(error.response.json().get("detail", "A service returned an error."))


if __name__ == "__main__":
    main()
