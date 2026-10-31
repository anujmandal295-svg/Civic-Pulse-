import os, streamlit as st
from ingest import fetch_text, pdf_text, latest_notices, chunk
from rag import select, top
from explain import explain, voice_script, answer, LANGS, SECTIONS
from voice import speak

st.set_page_config(page_title="Civic Pulse", page_icon="🏛️", layout="wide")
st.title("🏛️ Civic Pulse — Policy & Scheme Explainer")
FEED = os.getenv("NOTICE_FEED", "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3")

with st.sidebar:
    src = st.radio("Source", ["Latest PIB releases (live)", "Paste notification URL", "Upload PDF"])
    lang = st.selectbox("Explain in", list(LANGS))
    audience = st.selectbox("For a", ["citizen", "small business owner", "farmer", "student"])

url, pdf = None, None
try:
    if src.startswith("Latest"):
        items = latest_notices(FEED)
        pick = st.selectbox("Pick a release", range(len(items)), format_func=lambda i: f"{items[i]['date'][:16]} · {items[i]['title']}")
        url = items[pick]["link"]
    elif src.startswith("Paste"):
        url = st.text_input("Government notification / scheme page URL")
    else:
        pdf = st.file_uploader("Gazette / scheme PDF", type="pdf")
except Exception as e:
    st.error(f"Could not load feed: {e}")

if st.button("Explain", type="primary") and (url or pdf):
    try:
        with st.status("Fetching and reading…") as s:
            text = pdf_text(pdf.read()) if pdf else fetch_text(url)
            chunks = select(chunk(text))
            s.update(label="Extracting rights & verifying quotes…")
            data = explain(chunks, audience)
            s.update(label=f"Writing {lang} voice script…")
            script = voice_script(data, lang)
            audio = speak(script, LANGS[lang])
        st.session_state.update(chunks=chunks, data=data, script=script, audio=audio)
    except Exception as e:
        st.error(f"Failed: {e}")

if "data" in st.session_state:
    d = st.session_state["data"]
    st.header(d.get("title", ""))
    st.info(d.get("summary", ""))
    st.audio(st.session_state["audio"], format="audio/mp3")
    st.text_area(f"{lang} script", st.session_state["script"], height=160)
    cols = st.columns(2)
    for n, sec in enumerate(SECTIONS):
        with cols[n % 2]:
            st.subheader(sec.title())
            for it in d.get(sec, []):
                st.markdown(f"✅ {it['text']}")
                with st.expander(f"Source {it['chunk']}"):
                    st.caption(f"“{it['quote']}”")
    if d["dropped_unverified"]:
        st.warning(f"{d['dropped_unverified']} claim(s) removed: quote could not be verified in the source.")
    q = st.text_input("Ask about this document")
    if q:
        ch = top(st.session_state["chunks"], q)
        st.write(answer(q, ch, lang))
