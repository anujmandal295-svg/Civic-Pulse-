import io
from gtts import gTTS

def speak(text: str, lang_code: str) -> bytes:
    buf = io.BytesIO()
    gTTS(text=text, lang=lang_code).write_to_fp(buf)
    return buf.getvalue()
