#!/bin/bash

# Used before or alongside deployment e.g. run DB migrations, check if port is open or free, log rotations
# or list files under fast_load that need to load quickly on start (e.g. model checkpoints).

# source ./ollama_root/start_ollama.sh
docker-compose -p tarohub up --build -d

echo "$HF_TOKEN" | huggingface-cli login --token

huggingface-cli snapshot-download facebook/bart-large-mnli --local-dir ./models/bart-large-mnli
