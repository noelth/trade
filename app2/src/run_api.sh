#!/bin/bash

# Create directory for chart images if it doesn't exist
mkdir -p static/charts

# Run the FastAPI server on port 8765
uvicorn api:app --reload --host 0.0.0.0 --port 8765