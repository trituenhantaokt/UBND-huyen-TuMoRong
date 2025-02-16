import streamlit as st
from openai import OpenAI
import os
import datetime
import re

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

# Hàm nhận diện và chuyển đổi phân số từ "a/b" thành LaTeX "\frac{a}{b}"
def format_fractions(text):
    return re.sub(r"(\d+)/(\d+)", r"\\frac{\1}{\2}", text)

# Hiển thị logo ở trên cùng, căn giữa
col1, col2, col3 = st.columns([3, 2, 3])
with col2:
    st.image("logo.png", use_container_width=True)

# Hiển thị tiêu đề từ file
title_content = rfile("00.xinchao.txt")
st.markdown(f"<h1 style='text-align: center; font-size: 24px;'>{title_content}</h1>", unsafe_allow_html=True)

# Lấy OpenAI API key từ `st.secrets`.
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Tạo OpenAI client.
client = OpenAI(api_key=openai_api_key)

# Khởi tạo lời nhắn "system" để định hình hành vi mô hình.
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": rfile("01.system_trainning.txt")}

# Khởi tạo lời nhắn ví dụ từ vai trò "assistant".
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": rfile("02.assistant.txt")}

# Tạo một biến trạng thái session để lưu trữ các tin nhắn nếu chưa tồn tại.
if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

# Loại bỏ INITIAL_SYSTEM_MESSAGE khỏi giao diện hiển thị.
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Khi người dùng nhập nội dung
if prompt := st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé?"):

    # Lưu trữ và hiển thị tin nhắn của người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ghi lại câu hỏi vào file log
    log_user_input(prompt)

    # Tạo phản hồi từ API OpenAI
    response = ""
    with st.chat_message("assistant"):
        response_container = st.empty()  # Tạo container để hiển thị nội dung

        for chunk in client.chat.completions.create(
            model=rfile("module_chatgpt.txt"),
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            if hasattr(chunk, "choices") and chunk.choices:
                response += chunk.choices[0].delta.content or ""
                formatted_response = format_fractions(response)

                # Nếu có công thức toán học, hiển thị bằng st.latex()
                if "\\" in formatted_response:
                    response_container.latex(formatted_response)
                else:
                    response_container.markdown(formatted_response)

    # Lưu phản hồi vào session
    st.session_state.messages.append({"role": "assistant", "content": response})
