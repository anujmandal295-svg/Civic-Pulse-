"""Grounded explainer: Claude extracts structured items WITH verbatim quotes,
a verifier checks each quote exists in the source chunk (retry once, then drop)."""
import os, re, json, anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
client = anthropic.Anthropic()
SECTIONS = ["rights", "eligibility", "deadlines", "actions", "impact"]
LANGS = {"English": "en", "Hindi": "hi", "Marathi": "mr", "Bengali": "bn", "Tamil": "ta",
         "Telugu": "te", "Gujarati": "gu", "Kannada": "kn", "Malayalam": "ml", "Punjabi": "pa", "Urdu": "ur"}

def _call(system, user, max_tokens=4000):
    r = client.messages.create(model=MODEL, max_tokens=max_tokens, system=system,
                               messages=[{"role": "user", "content": user}])
    return r.content[0].text

def _json(t):
    return json.loads(t[t.index("{"): t.rindex("}") + 1])

def _norm(s): return re.sub(r"\W+", " ", s.lower()).strip()

def _extract(chunks, audience, note=""):
    ctx = "\n\n".join(f"[{c['id']}] {c['text']}" for c in chunks)
    system = ("You explain Indian government notifications to ordinary people. Use ONLY the provided text. "
              "Never invent amounts, dates or eligibility. If something is absent, omit it. Reply with JSON only.")
    user = f"""Audience: {audience}. Source chunks:\n{ctx}\n\n{note}
Return JSON: {{"title": str, "summary": "3 plain sentences", "rights": [], "eligibility": [], "deadlines": [], "actions": [], "impact": []}}
Each list item: {{"text": plain-language statement (grade-6 English), "chunk": "C#", "quote": "VERBATIM <=25 words copied from that chunk"}}.
'impact' = real-world effect on the {audience}."""
    return _json(_call(system, user))

def explain(chunks, audience="citizen"):
    cmap = {c["id"]: c["text"] for c in chunks}
    note, data = "", None
    for attempt in range(2):
        data = _extract(chunks, audience, note)
        bad = [i["text"] for s in SECTIONS for i in data.get(s, [])
               if _norm(i.get("quote", "")) not in _norm(cmap.get(i.get("chunk"), "")) or not i.get("quote")]
        if not bad:
            break
        note = f"Your previous quotes were not verbatim for: {bad[:5]}. Copy exact words from the chunk."
    dropped = 0
    for s in SECTIONS:
        ok = [i for i in data.get(s, []) if i.get("quote") and _norm(i["quote"]) in _norm(cmap.get(i.get("chunk"), ""))]
        dropped += len(data.get(s, [])) - len(ok)
        data[s] = ok
    data["dropped_unverified"] = dropped
    return data

def voice_script(data, language):
    body = json.dumps({k: data[k] for k in ["title", "summary"] + SECTIONS}, ensure_ascii=False)
    return _call("You write short, warm spoken explainers for radio-style audio. Output only the script.",
                 f"Write a 150-200 word spoken explainer in {language}, simple village-friendly words, "
                 f"covering rights, who qualifies, deadlines, what to do. Use only facts below.\n{body}", 1200)

def answer(question, chunks, language="English"):
    ctx = "\n\n".join(f"[{c['id']}] {c['text']}" for c in chunks)
    return _call("Answer ONLY from the context and cite chunk ids like [C3]. If the answer is not there, "
                 "say the document does not specify it.",
                 f"Context:\n{ctx}\n\nQuestion: {question}\nAnswer in {language}.", 800)
