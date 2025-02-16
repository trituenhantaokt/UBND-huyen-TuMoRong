import streamlit as st
from openai import OpenAI
import glob  # Import thư viện để quét danh sách file

def read_multiple_files(pattern):
    """ Đọc nội dung từ nhiều file có cùng mẫu tên và ghép lại """
    content = []
    files = sorted(glob.glob(pattern))  # Lấy danh sách file theo mẫu, sắp xếp để có thứ tự cố định
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content.append(f.read().strip())  # Đọc file và loại bỏ khoảng trắng dư thừa
    return "\n\n".join(content)  # Ghép nội dung các file lại

# Hiển thị logo
col1, col2, col3 = st.columns([3, 2, 3])
with col2:
    st.image("logo.png", use_container_width=True)

# Hiển thị tiêu đề từ file
title_content = read_multiple_files("00.xinchao.txt")
st.markdown(f"<h1 style='text-align: center; font-size: 24px;'>{title_content}</h1>", unsafe_allow_html=True)

# Lấy OpenAI API key
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Tạo OpenAI client
client = OpenAI(api_key=openai_api_key)

# **Đọc nhiều file system training**
system_content = read_multiple_files("01*.system_trainning.txt")
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": system_content}

# Đọc nội dung trợ lý
assistant_content = read_multiple_files("02.assistant.txt")
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": assistant_content}

# Giới hạn số tin nhắn
MAX_MESSAGES = 10  

if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

# Chỉ giữ lại các tin nhắn gần nhất
st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# Hiển thị tin nhắn cũ
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Nhập nội dung mới từ người dùng
if prompt := st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé?"):

    # Lưu và hiển thị tin nhắn của người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gửi tin nhắn đến OpenAI API
    try:
        stream = client.chat.completions.create(
            model=read_multiple_files("module_chatgpt.txt").strip(),
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )

        # Hiển thị phản hồi của trợ lý
        with st.chat_message("assistant"):
            response_text = ""
            for chunk in stream:
                response_text += chunk  # Lưu toàn bộ nội dung phản hồi

            st.markdown(response_text)

        # Lưu phản hồi của trợ lý vào session
        st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"Lỗi khi gọi OpenAI API: {str(e)}")
