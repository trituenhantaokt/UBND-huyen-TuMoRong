import streamlit as st
from openai import OpenAI
import os
import datetime
import re
from web import search

# Hàm đọc nội dung từ file
def rfile(name_file):
    with open(name_file, "r", encoding="utf-8") as file:
        return file.read()

# Tạo thư mục logs nếu chưa có
os.makedirs("logs", exist_ok=True)

# Hàm ghi log câu hỏi của người dùng
def log_user_input(user_input):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/user_questions.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {user_input}\n")

# Hàm nhận diện và chuyển đổi phân số thành LaTeX
def format_fractions(text):
    return re.sub(r"(\d+)/(\d+)", r"\\frac{\1}{\2}", text)

# Hàm tìm kiếm thông tin từ trang web nếu cần
def search_web(query):
    search_results = search(f"site:https://tintuctonghoponline247.weebly.com/ {query}")
    if search_results:
        return search_results[0]["snippet"]  # Trích xuất nội dung phù hợp
    return "Không tìm thấy thông tin phù hợp trên trang web."

# Hiển thị logo
col1, col2, col3 = st.columns([3, 2, 3])
with col2:
    st.image("logo.png", use_container_width=True)

# Hiển thị tiêu đề từ file
title_content = rfile("00.xinchao.txt")
st.markdown(f"<h1 style='text-align: center; font-size: 24px;'>{title_content}</h1>", unsafe_allow_html=True)

# Lấy OpenAI API key từ `st.secrets`
openai_api_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Khởi tạo tin nhắn hệ thống
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": rfile("01.system_trainning.txt")}
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": rfile("02.assistant.txt")}

if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    log_user_input(prompt)

    response = ""
    with st.chat_message("assistant"):
        response_container = st.empty()

        chat_response = ""
        for chunk in client.chat.completions.create(
            model=rfile("module_chatgpt.txt"),
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            if hasattr(chunk, "choices") and chunk.choices:
                chat_response += chunk.choices[0].delta.content or ""
                formatted_response = format_fractions(chat_response)
                response_container.markdown(formatted_response)

        if not chat_response.strip():  # Nếu không có phản hồi từ AI, tìm kiếm trên web
            web_response = search_web(prompt)
            response_container.markdown(f"🔍 **Thông tin từ web**: {web_response}")
            response = web_response
        else:
            response = chat_response

    st.session_state.messages.append({"role": "assistant", "content": response})
