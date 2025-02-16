import streamlit as st
from openai import OpenAI

def rfile(name_file):
    with open(name_file, "r", encoding="utf-8") as file:
        content_sys = file.read()
        return content_sys

# Tạo 2 cột: cột 1 cho logo, cột 2 cho thông tin "Xin Chào"
col1, col2 = st.columns([1, 3])  # Tỷ lệ cột 1:3 (logo chiếm 1 phần, thông tin chiếm 3 phần)

# Hiển thị logo ở cột 1
with col1:
    st.image("logo.png", width=100)  # Điều chỉnh kích thước logo tại đây (đơn vị px)

# Hiển thị thông tin "Xin Chào" ở cột 2
with col2:
    st.markdown(
        f"""
        <h1 style="font-size: 20px; margin: 0;">Xin Chào, Tôi là trợ lý ảo UBND huyện Tu Mơ Rông, rất vui được trợ giúp, cung cấp các thông tin về quản lí nhà nước của Huyện Tu Mơ Rông!</h1>
        """,
        unsafe_allow_html=True
    )

# Lấy OpenAI API key từ `st.secrets`
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Tạo OpenAI client
client = OpenAI(api_key=openai_api_key)

# Khởi tạo lời nhắn "system" để định hình hành vi mô hình
INITIAL_SYSTEM_MESSAGE = {
    "role": "system",
    "content": rfile("01.system_trainning.txt"),
}

# Khởi tạo lời nhắn ví dụ từ vai trò "assistant"
INITIAL_ASSISTANT_MESSAGE = {
    "role": "assistant",
    "content": rfile("02.assistant.txt"),
}

# Tạo một biến trạng thái session để lưu trữ các tin nhắn nếu chưa tồn tại
if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

# Loại bỏ INITIAL_SYSTEM_MESSAGE khỏi giao diện hiển thị
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Tạo ô nhập liệu cho người dùng
if prompt := st.chat_input("Nhập nội dung cần hỗ trợ"):

    # Lưu trữ và hiển thị tin nhắn của người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Tạo phản hồi từ API OpenAI
    stream = client.chat.completions.create(
        model=rfile("module_chatgpt.txt"),
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
    )

    # Hiển thị và lưu phản hồi của trợ lý
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})