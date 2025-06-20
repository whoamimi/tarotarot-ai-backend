#!/bin/bash

/bin/ollama serve &

pid=$!

sleep 5


echo "Pulling llama3.1 bartowski's Llama3.2 GGUF model"
ollama pull hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q5_K_S


wait $pid