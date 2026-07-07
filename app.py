import streamlit as st
import pypdf
import json
from openai import OpenAI
import requests

# App configuration
st.set_page_config(page_title="Fact-Check Agent", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ The Fact-Check Agent")
st.subheader("Your AI Truth Layer for Marketing Content") [cite: 7, 9]

# Sidebar for API Keys
with st.sidebar:
    st.header("Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password")
    serper_key = st.text_input("Serper (Google Search) API Key", type="password")
    st.caption("Get a Serper key from serper.dev to query live web data.") [cite: 9, 13]

def extract_text_from_pdf(pdf_file):
    """Extracts raw text from an uploaded PDF file.""" [cite: 12]
    reader = pypdf.PdfReader(pdf_file)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() + "\n"
    return extracted_text

def extract_claims_with_llm(client, text):
    """Uses LLM to identify specific stats, dates, and figures to verify.""" [cite: 12]
    prompt = f"""
    Analyze the following marketing text and extract the top 3-5 most specific verifiable claims 
    (such as percentages, dates, market sizes, or concrete financial/technical statistics).
    
    Return ONLY a valid JSON array of strings containing the distinct claims. Do not include markdown formatting.
    Example output format:
    ["Global AI market will reach $1.3 trillion by 2030", "Company X grew by 45% in Q2 2025"]

    Text to analyze:
    {text}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    try:
        claims = json.loads(response.choices[0].message.content.strip().replace("```json", "").replace("```", ""))
        return claims
    except Exception:
        return []

def search_live_web(query, serper_api_key):
    """Searches the live web using Serper API for the given claim.""" [cite: 13]
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        results = response.json()
        snippets = [item.get('snippet', '') for item in results.get('organic', [])[:3]]
        return " | ".join(snippets)
    except Exception:
        return "No real-time search results found."

def verify_claim_with_context(client, claim, search_results):
    """Cross-references the claim against the live web context.""" [cite: 9, 13]
    prompt = f"""
    You are an expert fact-checker. Cross-reference the claimed statistic with the provided live web search context. [cite: 7, 9, 13]
    
    Claim to evaluate: "{claim}"
    Live Web Context: "{search_results}"
    
    Categorize the claim into exactly one of these labels:
    - VERIFIED: If the live web data closely matches or supports the claim. [cite: 14]
    - INACCURATE: If the statistic is outdated, slightly incorrect, or misquoted. [cite: 14]
    - FALSE: If the live web search directly refutes the claim or if absolutely no supporting evidence exists. [cite: 14]
    
    Provide your output strictly in the following JSON format:
    {{
        "status": "VERIFIED or INACCURATE or FALSE",
        "explanation": "A short sentence explaining why, including the correct 'real' facts found on the web." 
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# Main Application Flow
if not openai_key or not serper_key:
    st.warning("⚠️ Please provide both your OpenAI and Serper API keys in the sidebar to start fact-checking.")
else:
    client = OpenAI(api_key=openai_key)
    uploaded_file = st.file_file("Upload marketing or analytics PDF", type=["pdf"]) [cite: 11, 15]

    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            # 1. Extract Text
            raw_text = extract_text_from_pdf(uploaded_file) [cite: 12]
            
            # 2. Extract Claims
            claims_to_check = extract_claims_with_llm(client, raw_text) [cite: 12]
            
        if not claims_to_check:
            st.error("Could not confidently isolate discrete data points or claims from this document. Try a different file.")
        else:
            st.success(f"Isolated {len(claims_to_check)} core claims for live verification!") [cite: 13]
            st.write("---")
            
            # 3. Verify and Report Layout
            for i, claim in enumerate(claims_to_check, start=1):
                with st.status(f"Verifying Claim {i}: '{claim}'...", expanded=True):
                    # Fetch search engine context
                    search_context = search_live_web(claim, serper_key) [cite: 13]
                    # Run valuation LLM prompt
                    evaluation = verify_claim_with_context(client, claim, search_context)
                    
                    status = evaluation.get("status", "FALSE") [cite: 14]
                    explanation = evaluation.get("explanation", "No explanation compiled.") [cite: 20]
                    
                    # Display metrics visually to catch the evaluator's eye
                    if status == "VERIFIED":
                        st.markdown(f"**Status:** ✅ :green[{status}]") [cite: 14]
                    elif status == "INACCURATE":
                        st.markdown(f"**Status:** ⚠️ :orange[{status}]") [cite: 14]
                    else:
                        st.markdown(f"**Status:** ❌ :red[{status}]") [cite: 14]
                        
                    st.write(f"**Analysis:** {explanation}") [cite: 20]
