"""The screen calls Faro; it never calls a model directly."""
import os

import httpx


def call(service, path, payload=None, params=None):
    url = os.environ[f"FARO_{service.upper()}_URL"] + path
    with httpx.Client(timeout=180, trust_env=False) as client:
        response = client.post(url, json=payload) if payload is not None else client.get(url, params=params)
        response.raise_for_status()
        return response


def sign_in(user_id):
    return call("gate", "/v1/access", {"user_id": user_id}).json()


def ask(user_id, question, conversation_id, previous_answer_id):
    return call("compass", "/v1/questions", {
        "user_id": user_id, "question": question, "conversation_id": conversation_id,
        "previous_answer_id": previous_answer_id if not conversation_id else None,
    }).json()


def saved_turn(user_id, result):
    path = f"/v1/conversations/{result['conversation_id']}/turns/{result['turn_id']}"
    return call("compass", path, params={"user_id": user_id}).json()


def download(user_id, result, index):
    path = f"/v1/conversations/{result['conversation_id']}/turns/{result['turn_id']}/documents/{index}"
    return call("compass", path, params={"user_id": user_id}).content
