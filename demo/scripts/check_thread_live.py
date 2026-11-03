"""Calls the real Thread API and OpenAI. Small paid check; no mocked predictions."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx


ROOT = Path(__file__).resolve().parents[1]
QUESTION = 'Which cranes performed badly last month?'


def message(role, content):
    return {'role': role, 'content': content}


def main():
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
        port = connection.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'thread_api.infer:app',
                               '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'])
    results = []
    try:
        with httpx.Client(timeout=40) as client:
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError('Thread server failed to start')
                try:
                    if client.get(f'{url}/openapi.json').status_code == 200:
                        break
                except httpx.RequestError:
                    pass
                time.sleep(0.05)
            else:
                raise RuntimeError('Thread server did not become ready')

            history = [message('user', QUESTION), message('assistant', 'Which terminal?')]
            cases = [
                ('first_question', QUESTION, [], ['cranes', 'badly', 'last month'], [], False),
                ('terminal_reply', 'North Terminal.', history,
                 ['cranes', 'badly', 'north terminal', 'last month'], ['moves per hour'], True),
                ('indicator_reply', 'Moves per hour, lowest first.', history + [
                    message('user', 'North Terminal.'),
                    message('assistant', 'Which performance indicator and comparison?')],
                 ['cranes', 'north terminal', 'moves per hour', 'lowest', 'last month'], [], True),
                ('topic_change', 'How many trucks arrived yesterday?', history + [message('user', 'North Terminal.')],
                 ['trucks', 'yesterday'], ['cranes', 'north terminal', 'last month'], True),
                ('terminal_correction', 'Actually South Terminal, not North.', history + [message('user', 'North Terminal.')],
                 ['cranes', 'badly', 'south terminal', 'last month'], [], True),
                ('retail_region_reply', 'West region.', [
                    message('user', 'Which stores had disappointing results last quarter?'),
                    message('assistant', 'Which region?')],
                 ['stores', 'disappointing', 'west', 'last quarter'], ['cranes', 'terminal', 'revenue', 'profit'], True),
                ('software_error_reply', 'APP-42 says "Connection refused".', [
                    message('user', 'Why can I not open the application?'),
                    message('assistant', 'Which application and what error do you see?')],
                 ['app-42', 'connection refused'], ['cranes', 'terminal', 'firewall'], True),
            ]
            for name, question, conversation, expected, excluded, uses_ai in cases:
                response = client.post(f'{url}/v1/rewrite', json={'question': question, 'conversation': conversation})
                response.raise_for_status()
                output = response.json()
                text = output['question'].lower()
                passed = (all(value in text for value in expected)
                          and all(value not in text for value in excluded)
                          and output['used_ai'] == uses_ai)
                results.append({'case': name, 'passed': passed, 'input': {
                    'question': question, 'conversation': conversation}, 'output': output})
                print(f'{name}: {"PASS" if passed else "FAIL"} — {output["question"]}')
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
        path = ROOT / 'local_data/thread_live_check.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'evidence': 'Real HTTP and OpenAI responses; bounded smoke check, not a full evaluation',
                                    'results': results}, indent=2) + '\n')
    if not all(result['passed'] for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
