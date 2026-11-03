# Compass — coordinates a data question

Gate reads the selected account and permissions. Compass asks Connector for the permitted sources, then calls Thread when there is a clarification reply, Scout for search, and Signal for classification. Guide asks for a missing user choice. Bridge reads connected data, Shield checks the evidence, and Voice returns the supported answer and documents.

POST /v1/questions accepts user_id, question and, for a clarification reply, conversation_id. Sources come from Connector; the caller cannot provide another company's access. There is no company-information service, glossary or supported-task list.

Compass saves turns and model-call summaries in the company data collection. Only opening questions can reuse matching successful calls; Shield rechecks reused evidence. An unavailable required API returns a failure, not a partial answer.

Run the console from demo/ with `python console.py --test`. It starts all ten services. See the root README for installation and tests.
