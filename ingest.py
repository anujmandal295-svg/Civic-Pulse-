"""Live ingestion: fetch real government notices (HTML/PDF) and chunk them."""
import io, re, requests, feedparser
from bs4 import BeautifulSoup
from pypdf import PdfReader

HEADERS = {"User-Agent": "Mozilla/5.0 CivicPulse/1.0"}

def clean(t):
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{2,}", "\n\n", t)).strip()

def pdf_text(data: bytes) -> str:
    text = clean("\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages))
    if len(text) < 200:
        raise ValueError("PDF has no extractable text (likely scanned). Try the HTML version.")
    return text

def fetch_text(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if "pdf" in r.headers.get("content-type", "").lower() or url.lower().endswith(".pdf"):
        return pdf_text(r.content)
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "form"]):
        t.decompose()
    text = clean(soup.get_text("\n"))
    if len(text) < 200:
        raise ValueError("Page returned too little text (JS-rendered or blocked).")
    return text

def latest_notices(feed_url: str, n: int = 15):
    feed = feedparser.parse(feed_url, request_headers=HEADERS)
    if not feed.entries:
        raise ValueError("Feed returned no entries (check URL / network).")
    return [{"title": e.get("title", "?"), "link": e.get("link"), "date": e.get("published", "")}
            for e in feed.entries[:n]]

def chunk(text: str, size: int = 180, overlap: int = 30):
    words, out, i = text.split(), [], 0
    while i < len(words):
        out.append({"id": f"C{len(out)+1}", "text": " ".join(words[i:i + size])})
        i += size - overlap
    return out
