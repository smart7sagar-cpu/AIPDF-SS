import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

st.set_page_config(page_title="AI PDF Assistant", layout="wide")
st.title("🚀 AI PDF Assistant (made by SAGAR)")

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("GEMINI_API_KEY secrets me nahi mili.")
    st.stop()

@st.cache_data(show_spinner=False)
def extract_text(files_data):
    out = ""
    for name, data in files_data:
        import io
        reader = PdfReader(io.BytesIO(data))
        for i, page in enumerate(reader.pages):
            t = page.extract_text()
            if t:
                out += f"\n--- [Document: {name} | Page: {i+1}] ---\n{t}"
    return out

def ask_gemini(prompt, system=None):
    try:
        r = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system, temperature=0.2),
        )
        return r.text
    except Exception as e:
        return f"❌ Error: {e}"

uploaded_files = st.file_uploader("PDF files upload karein", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    files_data = tuple((f.name, f.getvalue()) for f in uploaded_files)
    full_context = extract_text(files_data)

    if not full_context.strip():
        st.warning("PDF me text nahi mila (shayad scanned PDF hai).")
        st.stop()

    st.success("Documents load ho gaye!")

    if st.button("📝 Summary chahiye"):
        with st.spinner("Summary ban rahi hai..."):
            st.session_state["summary"] = ask_gemini(
                f"Is PDF data ka detailed summary points me Hindi me likhein:\n\n{full_context[:45000]}"
            )
    if "summary" in st.session_state:
        st.write("### 📋 Summary")
        st.write(st.session_state["summary"])

    st.write("---")
    q = st.text_input("PDF ke baare me sawal poochein:")
    if q:
        with st.spinner("Jawab dhoondh raha hu..."):
            ans = ask_gemini(
                f"Context:\n{full_context[:55000]}\n\nSawal: {q}",
                system="Sirf diye gaye context se Hindi me jawab do aur Document Name aur Page Number zaroor batao.",
            )
        st.write("### 🤖 Jawab")
        st.write(ans)