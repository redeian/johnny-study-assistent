import io
import time
import streamlit as st
from PIL import Image



# ------------------------------ Page Logic --------------------------------

logo = Image.open("./static/johnny.jpg")
st.set_page_config(page_title = "Johnny - Study Assistant", page_icon = logo, layout="wide")

ft = """<h2>Credit</h2>
<ol>
<li>This application is developed by <a style='display: inline; text-align: left;' href="https://www.chatchaiwang.com"> Chatchai Wangwiwattana </a> based on the work of <a style='display: inline; text-align: left;' href="https://www.linkedin.com/in/tg120/" target="_blank">Tejas Gorla</a> 
<li>This tool is analysed by <a href = "https://tools.pdf24.org/en/ocr-pdf">PDF OCR</a>.
<li>This tool is powered by Streamlit.
</ol>
"""
st.write(ft, unsafe_allow_html=True)
