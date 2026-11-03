"""Run Faro's local conversation demo."""
import argparse
import os

import httpx

from console.services import DEMO, running_services


def show_test_details(result):
    from compass.data_collection import DataCollection

    store = DataCollection(os.getenv("FARO_COLLECTION_PATH", DEMO / "local_data/data_collection"))
    doc = store.read_conversation(result["access"]["company_id"], result["conversation_id"])
    turn = next(t for t in doc["turns"] if t["_id"] == result["turn_id"])
    reused = [e["service"] for e in turn["cache"] if e["result_source"] == "cache"]
    print(f'Test: {turn["elapsed_ms"]} ms | Result: {turn["status"]} | Reused: {", ".join(reused) or "none"}')
    if turn["model_attempts"] is not None:
        for service, stats in turn["model_attempts"].items():
            calls = "; ".join(" → ".join(call) for call in stats["calls"])
            print(f'{service}: {stats["attempts"]} model attempts ({calls})')
    print(f'Full question: {result["rewrite"]["question"]}')


def login(client, urls):
    print("Demo login: enter an active user ID (for example maria, sam, hospital_ops or hotel_hq).")
    while True:
        user = input("User ID (/quit to exit): ").strip()
        if user == "/quit":
            return None
        if not user:
            continue
        response = client.post(urls["gate"] + "/v1/access", json={"user_id": user})
        if response.status_code == 403:
            print(response.json()["detail"])
            continue
        response.raise_for_status()
        account = response.json()
        print(f'Using {account["user_id"]} at {account["company_id"]}. /new: new conversation; /logout: switch user; /quit: exit.')
        return account["user_id"]


def chat(client, urls, test):
    user = login(client, urls)
    cid = previous = None
    while user:
        message = input("You: ").strip()
        if message == "/quit":
            return
        if message == "/logout":
            cid = previous = None
            user = login(client, urls)
            continue
        if message == "/new":
            cid = previous = None
            print("New conversation.")
            continue
        if not message:
            continue
        response = client.post(urls["compass"] + "/v1/questions", json={
            "user_id": user, "question": message, "conversation_id": cid, "previous_answer_id": previous if not cid else None})
        if not response.is_success:
            print(f'Faro: {response.json()["detail"]}')
            continue
        result = response.json()
        cid = result["conversation_id"] if result["followup"] else None
        previous = result["conversation_id"] if (result.get("verification") or {}).get("status") == "verified" else None
        followup = result["followup"]
        answer = result["answer"]
        if followup:
            print("Faro:", followup["followup_text"])
        elif answer:
            print("Faro:", answer["text"])
            for document in answer.get("documents", []):
                print("Document:", document["name"])
                print("Open:", document["uri"])
        else:
            print("Faro: I can’t answer that question from the company information available to you.")
        if test:
            show_test_details(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="show saved timing and reused work after each turn")
    args = parser.parse_args()
    print("Starting Faro's ten local APIs…", flush=True)
    try:
        with running_services() as urls, httpx.Client(timeout=180, trust_env=False) as client:
            print("All ten APIs are ready.", flush=True)
            chat(client, urls, args.test)
    except (EOFError, KeyboardInterrupt):
        print()
    except httpx.HTTPStatusError as error:
        raise SystemExit(error.response.json()["detail"])
