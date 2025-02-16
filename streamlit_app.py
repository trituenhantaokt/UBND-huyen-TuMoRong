import streamlit as st
from openai import OpenAI
import glob  
import sys
import subprocess
import requests
from bs4 import BeautifulSoup

# ✅ Kiểm tra và cài đặt `tiktoken` nếu chưa có
try:
    import tiktoken
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken"])
    import tiktoken  

# ✅ Kiểm tra và cài đặt `beautifulsoup4` nếu chưa có
try:
    import bs4
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup  

# 🔹 Hàm đọc nội dung từ nhiều file và ghép lại
def read_multiple_files(pattern):
    content = []
    files = sorted(glob.glob(pattern))  
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content.append(f.read().strip())  
    return "\n\n".join(content)  

# 🔹 Hàm đếm số tokens
def count_tokens(text):
    encoding = tiktoken.get_encoding("cl100k_base")  # Dùng tokenizer GPT-4
    return len(encoding.encode(text))

# 🔹 Hàm rút gọn nội dung nếu vượt quá số token cho phép
def truncate_text(text, max_tokens=1000):
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    truncated_tokens = tokens[:max_tokens]  # Giữ lại tối đa max_tokens tokens
    return encoding.decode(truncated_tokens)

# 🔹 Hàm lấy dữ liệu từ `https://tintuctonghoponline247.weebly.com/` nếu file training không có thông tin
def fetch_from_website(query):
    try:
        website_url = "https://nguyendinhvinh.com"
        response = requests.get(website_url, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")  # Lấy tất cả nội dung trong thẻ <p>
            content = " ".join([p.get_text() for p in paragraphs])

            # Kiểm tra nếu từ khóa có trong nội dung trang web
            if query.lower() in content.lower():
                return content[:2000]  # Trả về 2000 ký tự đầu tiên
            else:
                return "Không tìm thấy thông tin phù hợp trên website."

        else:
            return "Không thể truy cập trang web để lấy dữ liệu."
    
    except Exception as e:
        return f"Lỗi khi truy cập website: {str(e)}"

# 📌 Hiển thị logo
col1, col2, col3 = st.columns([3, 2, 3])
with col2:
    st.image("logo.png", use_container_width=True)

# 📌 Hiển thị tiêu đề từ file
title_content = read_multiple_files("00.xinchao.txt")
st.markdown(f"<h1 style='text-align: center; font-size: 24px;'>{title_content}</h1>", unsafe_allow_html=True)

# 📌 Lấy OpenAI API key
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# 📌 Tạo OpenAI client
client = OpenAI(api_key=openai_api_key)

# 🔹 Đọc và rút gọn nội dung hệ thống nếu quá dài
system_content = read_multiple_files("01*.system_trainning.txt")
if count_tokens(system_content) > 1000:
    system_content = truncate_text(system_content, 1000)  # Rút gọn nếu quá dài
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": system_content}

# 🔹 Đọc nội dung trợ lý
assistant_content = read_multiple_files("02.assistant.txt")
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": assistant_content}

# 🔹 Giới hạn chỉ giữ lại 5-7 tin nhắn gần nhất
MAX_MESSAGES = 7  

if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

# 📌 Chỉ giữ lại 7 tin nhắn gần nhất để tránh lỗi context length
st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# 📌 Hiển thị tin nhắn cũ
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 📌 Nhập nội dung mới từ người dùng
if prompt := st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé?"):

    # 🔹 Lưu và hiển thị tin nhắn của người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 📌 Kiểm tra xem file training có chứa thông tin hay không
    training_data = read_multiple_files("01*.system_trainning.txt")
    
    if prompt.lower() in training_data.lower():
        web_result = ""  # Không cần tìm kiếm web nếu đã có trong training
    else:
        web_result = fetch_from_website(prompt)  # Lấy thông tin từ website

    # 🔹 Chỉ giữ lại 7 tin nhắn gần nhất trước khi gửi đến OpenAI
    messages_to_send = st.session_state.messages[-MAX_MESSAGES:]

    # 🔹 Gửi tin nhắn đến OpenAI API
    try:
        stream = client.chat.completions.create(
            model=read_multiple_files("module_chatgpt.txt").strip(),
            messages=[{"role": m["role"], "content": m["content"]} for m in messages_to_send],
            stream=True,
        )

        # 📌 Hiển thị phản hồi của trợ lý
        with st.chat_message("assistant"):
            response_text = web_result  # Gộp thông tin từ web vào câu trả lời nếu có

            for chunk in stream:
                if chunk.choices:
                    response_text += chunk.choices[0].delta.content or ""  

            st.markdown(response_text)

        # 🔹 Lưu phản hồi của trợ lý vào session
        st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"Lỗi khi gọi OpenAI API: {str(e)}")
