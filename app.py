import streamlit as st
import pypdf
import json
from openai import OpenAI
import requests

st.set_page_config(page_title="Fact-Check Agent", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ The Fact-Check Agent")
st.subheader("Automated Truth Layer for PDF Verification")

with st.sidebar:
    st.header("🔑 API Credentials")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key (sk-...)")
    serper_key = st.text_input("Serper API Key", type="password", help="Enter your serper.dev API key for live web search")
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Enter your API keys above.\n2. Upload a PDF document.\n3. The agent will extract, verify, and flag claims.")

def extract_text_from_pdf(pdf_file):
    reader = pypdf.PdfReader(pdf_file)
    extracted_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text + "\n"
    return extracted_text

def extract_claims_with_llm(client, text):
    prompt = f"""
    Analyze the following text and extract 3 to 5 core specific verifiable claims (such as statistics, dates, market shares, or technical figures).
    Return ONLY a valid JSON array of strings containing the distinct claims. Do not include markdown or text wrapping.
    
    Example Output:
    ["Global smartphone adoption reached 85% in 2024", "The company reported a 40% decline in revenue"]

    Text:
    {text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        st.error(f"Error parsing claims: {e}")
        return []

def search_live_web(query, serper_api_key):
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': serper_api_key, 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        results = response.json()
        snippets = [item.get('snippet', '') for item in results.get('organic', [])[:3]]
        return " | ".join(snippets)
    except Exception:
        return "No real-time search results found."

def verify_claim_with_context(client, claim, search_results):
    prompt = f"""
    You are an expert fact-checker evaluating claims against real-time web search contexts.
    
    Claim to evaluate: "{claim}"
    Live Web Context: "{search_results}"
    
    Categorize the claim into exactly one of these labels:
    - VERIFIED: If the live web data closely matches or supports the claim.
    - INACCURATE: If the statistic is outdated, misquoted, or partially wrong.
    - FALSE: If the live web data completely contradicts the claim or no evidence supports it.
    
    Provide your output strictly in the following JSON format:
    {{
        "status": "VERIFIED or INACCURATE or FALSE",
        "explanation": "A short, concise sentence explaining why, providing the actual true fact/stat found on the web."
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"status": "FALSE", "explanation": "Failed to generate evaluation format."}

if not openai_key or not serper_key:
    st.info("💡 To start, please input your OpenAI and Serper API keys in the sidebar menu.")
else:
    client = OpenAI(api_key=openai_key)
    uploaded_file = st.file_uploader("Upload your document (PDF format)", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("Extracting text and isolating claims..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            claims = extract_claims_with_llm(client, raw_text)

        if not claims:
            st.warning("No clear statistical or data claims could be extracted from this PDF.")
        else:
            st.success(f"Successfully extracted {len(claims)} key claims for verification!")
            st.write("---")

            for i, claim in enumerate(claims, start=1):
                with st.expander(f"📋 Claim {i}: {claim}", expanded=True):
                    with st.spinner("Searching the live web & checking accuracy..."):
                        search_context = search_live_web(claim, serper_key)
                        evaluation = verify_claim_with_context(client, claim, search_context)
                        
                        status = evaluation.get("status", "FALSE")
                        explanation = evaluation.get("explanation", "")

                        if status == "VERIFIED":
                            st.markdown(f"**Status:** ✅ :green[{status}]")
                        elif status == "INACCURATE":
                            st.markdown(f"**Status:** ⚠️ :orange[{status}]")
                        else:
                            st.markdown(f"**Status:** ❌ :red[{status}]")
                        
                        st.write(f"**Fact-Check Analysis:** {explanation}")
