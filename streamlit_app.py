import streamlit as st
from openai import OpenAI
import glob  

def read_multiple_files(pattern):
    """ Đọc nội dung từ nhiều file có cùng mẫu tên và ghép lại """
    content = []
    files = sorted(glob.glob(pattern))  
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content.append(f.read().strip())  
    return "\n\n".join(content)  

def truncate_text(text, max_tokens=1000):
    """ Cắt ngắn nội dung chỉ giữ lại số từ quan trọng nhất """
    words = text.split()
    return " ".join(words[:max_tokens])  

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

# **Đọc và rút gọn nhiều file system training**
system_content = read_multiple_files("01*.system_trainning.txt")
system_content = truncate_text(system_content, 1000)  # Giữ nội dung hệ thống ngắn hơn
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": system_content}

# Đọc nội dung trợ lý
assistant_content = read_multiple_files("02.assistant.txt")
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": assistant_content}

# **Giới hạn chỉ giữ lại 5-7 tin nhắn gần nhất**
MAX_MESSAGES = 7  

if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

# Chỉ lưu lại 7 tin nhắn gần nhất
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

    # Chỉ giữ lại 7 tin nhắn gần nhất trước khi gửi đến OpenAI
    messages_to_send = st.session_state.messages[-MAX_MESSAGES:]

    # Gửi tin nhắn đến OpenAI API
    try:
        stream = client.chat.completions.create(
            model=read_multiple_files("module_chatgpt.txt").strip(),
            messages=[{"role": m["role"], "content": m["content"]} for m in messages_to_send],
            stream=True,
        )

        # Hiển thị phản hồi của trợ lý
        with st.chat_message("assistant"):
            response_text = ""
            for chunk in stream:
                if chunk.choices:
                    response_text += chunk.choices[0].delta.content or ""  

            st.markdown(response_text)

        # Lưu phản hồi của trợ lý vào session
        st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"Lỗi khi gọi OpenAI API: {str(e)}")
