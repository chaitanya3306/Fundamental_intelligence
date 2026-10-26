import os

# Dashboard configuration – can be overridden with environment variables.
# This allows the Streamlit UI to point at the FastAPI server even if it runs on a
# non‑default port (e.g., during development when port 8000 is occupied).

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
BASE_URL = f"http://{API_HOST}:{API_PORT}"
