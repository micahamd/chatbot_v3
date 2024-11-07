import streamlit as st
from other_py_files.rag_chat import RAGChat
import os

st.title("Local RAG Chatbot")

# Initialize the chatbot
if "chatbot" not in st.session_state:
    st.session_state.chatbot = RAGChat()

# Document loading section
with st.sidebar:
    st.header("Document Loading")
    docs_path = st.text_input("Enter documents directory path:")
    if st.button("Load Documents"):
        if docs_path and os.path.exists(docs_path):
            num_docs = st.session_state.chatbot.load_documents(docs_path)
            st.success(f"Loaded and processed {num_docs} document chunks!")
        else:
            st.error("Please enter a valid directory path!")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.chatbot.chat(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
