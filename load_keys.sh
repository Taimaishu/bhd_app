#!/bin/bash
# Load API keys from .env file
# Usage: source load_keys.sh

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ API keys loaded from .env"
    echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."
    echo "  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:25}..."
else
    echo "Error: .env file not found"
    exit 1
fi
