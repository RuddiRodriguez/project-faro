"""Export a saved Parquet conversation as readable JSON, without changing the tables."""
import argparse
import json
from pathlib import Path
from uuid import UUID

from compass.data_collection import DataCollection

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("company")
    parser.add_argument("conversation_id", type=UUID)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1]/"local_data/data_collection")
    args = parser.parse_args()
    doc = DataCollection(args.root).read_conversation(args.company,args.conversation_id)
    if doc is None:
        parser.error("Conversation not found in this company")
    print(json.dumps(doc,ensure_ascii=False,indent=2,allow_nan=False))
