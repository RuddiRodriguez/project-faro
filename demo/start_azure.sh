#!/bin/sh
set -e
cd "$(dirname "$0")"

# Keep local service imports tied to the deployed files, not Oryx's build folder.
export PYTHONPATH="$PWD/api_objects:$PWD/utils${PYTHONPATH:+:$PYTHONPATH}"
for service in */machine-learning-*-api; do
    export PYTHONPATH="$PYTHONPATH:$PWD/$service"
    for library in "$service"/infer/*; do
        export PYTHONPATH="$PYTHONPATH:$PWD/$library"
    done
done

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
