#!/bin/sh
set -e
cd "$(dirname "$0")"

export FARO_WEB_HOST=0.0.0.0
export FARO_WEB_PORT=8000
export FARO_MODEL_PATH=/home/faro/scout_e5
export FARO_INDEX_PATH=/home/faro/scout_source_indexes
export FARO_COLLECTION_PATH=/home/faro/data_collection
export FARO_DOCUMENT_PATH=/home/faro/source_documents

if [ ! -f "$FARO_MODEL_PATH/revision" ]; then
    python scripts/prepare_scout_model.py
fi

exec python run_web_demo.py
