# Civic Pulse — Multilingual Policy, Rights & Scheme Explainer
Turns live government notifications into verified, plain-language, regional-language voice explainers.

## Architecture
```mermaid
flowchart LR
  A[PIB RSS / URL / PDF] --> B[ingest.py fetch+parse+chunk]
  B --> C[rag.py BM25 facet retrieval]
  C --> D[explain.py Claude structured extraction]
  D --> E{Verifier: quote is verbatim in chunk?}
  E -- no --> D
  E -- yes/after 1 retry, drop rest --> F[Rights / Eligibility / Deadlines / Impact]
  F --> G[Voice script in 11 languages] --> H[gTTS audio]
  F --> I[Grounded Q&A with chunk citations]
```
**Guardrail:** every claim carries a verbatim source quote; unverifiable claims are retried once, then dropped and reported.
**No mock data:** all content is fetched live from the notice URL, uploaded PDF, or the PIB RSS feed (`NOTICE_FEED`).

## Run
```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
streamlit run app.py
```
Deploy: push to GitHub → Streamlit Community Cloud / HF Spaces, add `ANTHROPIC_API_KEY` as a secret.
