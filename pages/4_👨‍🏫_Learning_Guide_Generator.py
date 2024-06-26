import io
import time
import streamlit as st
import asyncio
from pypdf import PdfReader
import docx2txt
from PIL import Image
import src.processing as pr
import src.generatorGPT as gen
import src.async_generator as ag

def clear_cache():
    st.cache_data.clear()
    if 'doc' in st.session_state:
        del st.session_state['doc']

@st.cache_data(ttl = 2*3600, max_entries = 5)
def text_process(uploads):
    text = ""
    for doc in uploads:
        if doc.name.endswith(".txt"):
            stringio = io.StringIO(doc.getvalue().decode("utf-8"))
            text += stringio.read()
        if doc.name.endswith(".pdf"):
            pdf_reader = PdfReader(doc)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        if doc.name.endswith(".docx"):
            text += docx2txt.process(doc)
    chunks = pr.text_splitter(text)
    return chunks

@st.cache_resource
def cache_chain(_chat):
    cached_chain = gen.initialise_chain_no_mem(chat = _chat, type = "guide")
    return cached_chain

async def print_progress(progress_queue):
    last_processed_chunks = 0
    while True:
        processed_chunks = await progress_queue.get()
        if processed_chunks != last_processed_chunks:
            prog_value.text(f"Step: {processed_chunks}/{size}")
            last_processed_chunks = processed_chunks

async def main(chunks, chain, subject):
    progress_queue = asyncio.Queue()
    progress_task = asyncio.create_task(print_progress(progress_queue))
    results, processed_chunks = await ag.gen_concurrent(chunks, chain , subject, progress_queue)
    progress_task.cancel()
    return results, processed_chunks

# ------------------------------ Page Logic --------------------------------

logo = Image.open("./static/johnny.jpg")
st.set_page_config(page_title = "Johnny - Study Assistant", page_icon = logo, layout="wide")

chat3_5, chat4 = pr.initialise_llms_with_key(st.secrets["openai_api_key"])

chain = cache_chain(chat3_5)

col1, col2= st.columns([0.5, 2])
col1.image(logo, output_format="PNG", clamp=True, use_column_width=True)

with col2:
    st.title("Johnny - Study Assistant")
    st.subheader("Learning Guide Generator (Beta)")
    st.markdown("""Use this tool to allow handwritten study materials to be analysed: <a href = "https://tools.pdf24.org/en/ocr-pdf">PDF OCR</a>""", unsafe_allow_html = True, help = "If the tool says 0 words recognised, ignore this as it has still worked.")
    st.caption("Tired of cramming? Upload your study materials and generate a detailed learning guide to help you study more effectively!")

uploaded_pdfs = st.file_uploader("Upload Study Materials", type = ["pdf","txt","docx"], accept_multiple_files = True, help = "Due to cserver limitations, there is currently a limit of 100 mb per document.", on_change = clear_cache, key = "plan_uploads")

if uploaded_pdfs:
    st.caption("Files uploaded (upload new files or refresh to replace these)")
    chunks = text_process(uploaded_pdfs)
    st.session_state["plan_chunks"] = chunks

if 'plan_chunks' in st.session_state and st.session_state.plan_chunks is not None and st.session_state.plan_chunks != []:
    chunks = st.session_state["plan_chunks"]
    size = len(chunks)
    subject = st.text_input("Enter the name of the subject/module:", key="plan_subject")
    gen_button = st.button("Generate Plan", key="gen_plan_button", type="primary")
    filename = f"{subject}_Guide.txt"
    if gen_button and filename:
        prog_value = st.empty()
        prog_value.text(f"Step: starting process...")
        stay_open = st.empty()
        stay_open.info("Please do not close the page until the process is complete. If the process stops halfway, click generate again, without refreshing the page, to continue.")
        if "plan_doc" in st.session_state and st.session_state.plan_doc is not None and st.session_state.plan_doc["name"] == subject:
            st.success("Plan generated!")
            download = st.download_button("Download", st.session_state.plan_doc["doc"], file_name=filename, key="plan_download_button")
            if download:
                time.sleep(3)
                clear_cache()
        else:
            with st.spinner("Generating plan..."):
                bank_gen, prog = asyncio.run(main(chunks, chain = chain, subject = subject))
                try:
                    bank = "\n\n".join(bank_gen)
                except TypeError:
                    filtered = list(filter(None, bank_gen))
                    bank = " ".join(filtered)
            stay_open.empty()
            doc = bank + "\n\nGenerated by Johnny - Study Assistant"
            st.session_state["plan_doc"] = {"name" : subject, "doc" : doc}
            st.success("Plan generated!")
            download = st.download_button("Download", st.session_state.plan_doc["doc"], file_name=filename, key="plan_download_button")
            if download:
                time.sleep(3)
                clear_cache()

st.divider()
st.caption("*If something stops working, refresh the page twice and try again.")

# ------------------------------ FOOTER ------------------------------ #
