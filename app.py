import io

import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

# ---------------- Config ----------------
# Pehla model chalega; agar wo 404/NOT_FOUND de to agla try hoga.
MODEL_CANDIDATES = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
]
SUMMARY_LIMIT = 45000
QA_LIMIT = 55000

st.set_page_config(page_title="AI PDF Assistant", page_icon="🚀", layout="wide")
st.title("🚀 AI PDF Assistant (made by SAGAR)")

# ---------------- API client ----------------
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error(
        "⚠️ GEMINI_API_KEY nahi mili. Streamlit → Settings → Secrets me ye add karein:\n\n"
        'GEMINI_API_KEY = "aapki_key"'
    )
    st.stop()


# ---------------- Helpers ----------------
@st.cache_data(show_spinner=False)
def extract_text(files_data):
    """files_data = tuple of (filename, bytes). Cache hota hai, to baar-baar parse nahi hoga."""
    out = ""
    for name, data in files_data:
        try:
            reader = PdfReader(io.BytesIO(data))
        except Exception as e:
            out += f"\n--- [Document: {name} | padh nahi paya: {e}] ---\n"
            continue
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
            except Exception:
                text = None
            if text:
                out += f"\n--- [Document: {name} | Page: {i + 1}] ---\n{text}"
    return out


def ask_gemini(prompt, system=None):
    """Models ko ek-ek karke try karta hai. Error ho to message return karta hai (crash nahi)."""
    last_error = None
    for model in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.2,
                ),
            )
            return response.text or "⚠️ Model ne khaali jawab diya."
        except Exception as e:
            last_error = e
            msg = str(e)
            # Sirf model-not-found par agla model try karein
            if "404" in msg or "NOT_FOUND" in msg:
                continue
            break
    return f"❌ Error: {last_error}"


# ---------------- UI ----------------
uploaded_files = st.file_uploader(
    "Apni PDF files upload karein", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    files_data = tuple((f.name, f.getvalue()) for f in uploaded_files)

    with st.spinner("PDF se text nikala ja raha hai..."):
        full_context = extract_text(files_data)

    if not full_context.strip():
        st.warning("PDF me text nahi mila. Shayad ye scanned/image PDF hai.")
        st.stop()

    st.success(f"✅ {len(uploaded_files)} document(s) load ho gaye!")

    if len(full_context) > QA_LIMIT:
        st.info(
            f"PDF bahut bada hai, isliye sirf shuru ke {QA_LIMIT:,} characters use ho rahe hain."
        )

    # ----- Summary -----
    if st.button("📝 Detailed Summary banao"):
        with st.spinner("Summary ban rahi hai..."):
            st.session_state["summary"] = ask_gemini(
                "Niche diye gaye PDF data ka clear aur detailed summary points me "
                f"Hindi me likhein:\n\n{full_context[:SUMMARY_LIMIT]}"
            )

    if "summary" in st.session_state:
        st.write("### 📋 PDF Summary")
        st.write(st.session_state["summary"])

    # ----- Q&A -----
    st.write("---")
    st.subheader("💬 PDF se sawal poochein")
    question = st.text_input("Apna sawal likhein:")

    if question:
        system_instruction = (
            "Aap ek helpful AI assistant hain. Sirf diye gaye context ke basis par jawab do. "
            "Jawab Hindi me, clear aur sateek ho. Jawab me Document Name aur Page Number "
            "zaroor batao. Agar jawab context me nahi hai to saaf bolo ki PDF me nahi mila."
        )
        with st.spinner("Jawab dhoondha ja raha hai..."):
            answer = ask_gemini(
                f"Context:\n{full_context[:QA_LIMIT]}\n\nSawal: {question}",
                system=system_instruction,
            )
        st.write("### 🤖 Jawab")
        st.write(answer)
else:
    st.info("👆 Shuru karne ke liye ek ya zyada PDF upload karein.")
