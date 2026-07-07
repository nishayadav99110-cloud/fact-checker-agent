# The Fact-Check Agent Web App

An automated truth-layer tool designed for Product Management evaluation. It parses text from uploaded PDFs, extracts specific data parameters or claims using LLMs, verifies them against live web results via search APIs, and reports their accuracy status.

## Tech Stack
* Frontend & UI: Streamlit
* Core Parsing: PyPDF
* Processing & Evaluation Engine: OpenAI API (`gpt-4o-mini`)
* Real-Time Search: Serper.dev API

## Setup Instructions
1. Upload `app.py` and `requirements.txt` to your repository.
2. Link your repository directly to Streamlit Cloud.
3. Launch the app, enter your API keys, and upload a document to begin auditing data claims.
