# 🤖 Multimodal Chatbot v0.3

## 🌟 AI Chatbot

Multimodal Chatbot 0.3 is a Python-based chatbot that allows interaction with several proprietary and local (via Ollama) AI models. The application works with individual files or directories (for context and batch processing). You can additionally generate images using DALL-E3 via OpenAI if you have their API.

## 🚀 Features

- 🌐 **Multiple models**: Switch between OpenAI, Google AI, Anthropic (Claude), Mistral AI, and local Ollama models within a single session.
- 🧠 **Context-Selection**: All files within a specified directory can be cached to function as a context.
- 📊 **File Preprocessing**: 
  - 📄 Extract text from various file formats (PDF, DOCX, PPTX, RMD, HTML etc.) to a pre-specified JSON structure before being passed on to the API.
  - 🖼️ All images from a file are extracted and stored in a temporary local folder for AI processing. Skipping images (default=TRUE) will bypass all image processing.
  - 📑 Chat history can be selectively included in the prompt.
- 💾 **Conversation Archiving**: Export your AI dialogues in HTML or plain text.

## 🏆 AI Providers (to be updated)

1. 🟢 OpenAI 
2. 🔵 Google AI
3. 🟣 Anthropic AI
4. 🔴 Mistral AI (No vision capabilities)
5. 🟠 Ollama (Vision capabilities is hard-coded to the 'minicpm-v:latest' model in the ollama_method. Feel free to alter this to your preferred model in the ollama_method.py file, line 79)

## 🛠️ Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/micahamd/chatbot_v3
   cd multimodal-chatbot
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install additional components:
   - Tesseract OCR: [Installation guide](https://github.com/tesseract-ocr/tesseract)
   - Ollama (for local models): [Download instructions](https://ollama.ai/download)

5. Ensure to have API keys for proprietary vendors in an .env file located in the main directory:
   ```
   TESSERACT_CMD=C:\Tesseract-OCR\tesseract.exe # If you want to use OCR
   OPENAI_API_KEY=
   ANTHROPIC_API_KEY=
   GOOGLE_API_KEY=
   MISTRAL_API_KEY=
   ```

6. Launch Multimodal Chatbot 0.3:
   ```
   python main.py
   ```



## 🎯 Interface instructions

1. **Choose your AI**: Select an AI provider and model from the dropdown menus.

2. **Prompt input**: Input your prompt or question in the text area. You can also input in rich text format.

3. **Context directory (optional)**:
   - Optionally select a file or directory to provide additional context.
   - Use the "Cancel" button to clear selections if you change your mind. 

4. **Batch processing (optional)**:
   - Analyze multiple files within a directory with the same prompt set.
   - Remember to press "Cancel" to de-select the folder.

5. **Submit and wait**: Click "Process" to send your request to the chosen AI model. Do not interact with the model while the "Process" button appears depressed.

6. *Output**: Review the AI-generated response in the output area. Decide to include this in the prompt by selecting the "include chat history" checkbox (Default = FALSE).

7. **Other options**:
   - "Save Output": Save your AI conversation as an HTML file.
   - "Clear": Clear conversation history.

## 🛠️ Housekeeping

- **API storage**: Store your API keys in a `.env` file in the directory of the chatbot. These should never be shared online.
- **Model Flexibility**: Tailor available models in the `update_model_options` function within `main.py`.
- **UI aesthetics**: Tinker with the app's look by tweaking `style.qss`.


## 📜 Legal

This project is under the MIT License. 