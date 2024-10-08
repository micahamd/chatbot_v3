import sys
import io
import base64
import re
import markdown
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QComboBox, QTextEdit, QFileDialog, 
                             QLabel, QScrollArea, QCheckBox, QProgressBar, QLineEdit,
                             QStyleFactory, QTextBrowser)
from PyQt6.QtGui import (QPixmap, QTextCursor, QTextDocument, QIntValidator, QFontDatabase, QImage, QTextImageFormat)
from PyQt6.QtCore import (QUrl, Qt)
from PyQt6.QtNetwork import (QNetworkAccessManager, QNetworkRequest, QNetworkReply)
from model_interact import AIPlayground
from prep_file import context_directory


class AIPlaygroundGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Playground")
        self.setGeometry(100, 100, 500, 1000)
        self.network_manager = QNetworkAccessManager()
      # self.network_manager.finished.connect(self.on_image_downloaded)

        self.playground = AIPlayground(context_dir=None)
        self.file_path = None
        self.batch_dir = None
        self.current_theme = "RedTheme"
        
        self.init_ui()
        self.load_fonts()
        self.apply_theme()

    def load_fonts(self):
        QFontDatabase.addApplicationFont("path/to/Roboto-Regular.ttf")
        QFontDatabase.addApplicationFont("path/to/Roboto-Bold.ttf")

    def display_image(self, image_path_or_url):
        if image_path_or_url.startswith(('http://', 'https://')):
            # It's a URL, download the image
            request = QNetworkRequest(QUrl(image_path_or_url))
            self.network_manager.get(request)
        else:
            # It's a local file path
            pixmap = QPixmap(image_path_or_url)
            if not pixmap.isNull():
                self.add_image_to_output(pixmap)

    def on_image_downloaded(self, reply):
        if reply.error() == QNetworkRequest.NetworkError.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.add_image_to_output(pixmap)
        else:
            self.output_widget.append(f"Error loading image: {reply.errorString()}")

    def add_image_to_output(self, pixmap):
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
            image_label = QLabel()
            image_label.setPixmap(scaled_pixmap)
            self.output_widget.insertHtml('<br>')
            cursor = self.output_widget.textCursor()
            cursor.insertText('\n')
            self.output_widget.setTextCursor(cursor)
            self.output_widget.insertHtml('<br>')
            self.output_widget.document().addResource(
                QTextDocument.ImageResource,
                QUrl("myimg"), 
                scaled_pixmap
            )
            cursor.insertImage("myimg")
            self.output_widget.insertHtml('<br><br>')

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Developer and Model selection
        dev_model_layout = QHBoxLayout()
        self.dev_combo = QComboBox()
        self.dev_combo.addItems(["google", "openai", "mistral", "anthropic", "ollama"])  # Added "ollama"
        self.dev_combo.currentIndexChanged.connect(self.update_model_options)
        dev_model_layout.addWidget(QLabel("AI Provider:"))
        dev_model_layout.addWidget(self.dev_combo)
        self.model_combo = QComboBox()
        dev_model_layout.addWidget(QLabel("Model:"))
        dev_model_layout.addWidget(self.model_combo)
        layout.addLayout(dev_model_layout)
        self.update_model_options()

        # Configure Max tokens
        max_tok_layout = QHBoxLayout()
        max_tok_label = QLabel("Max Tokens:")
        self.max_tok_input = QLineEdit()
        self.max_tok_input.setText("1000")  # Set default value to 1000
        self.max_tok_input.setValidator(QIntValidator(1, 100000))  # Limit input to integers
        max_tok_layout.addWidget(max_tok_label)
        max_tok_layout.addWidget(self.max_tok_input)
        layout.addLayout(max_tok_layout)

        # Prompt input
        layout.addWidget(QLabel("Enter your prompt:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter your prompt here...")
        layout.addWidget(self.prompt_input)


        # Include chat history
        self.include_history_checkbox = QCheckBox("Include Chat History")
        layout.addWidget(self.include_history_checkbox)

        # Image skip checkbox
        self.image_skip_checkbox = QCheckBox("Skip Image Processing")
        self.image_skip_checkbox.setChecked(True)  # Default to checked
        layout.addWidget(self.image_skip_checkbox)

        # Add file selection
        file_layout = QHBoxLayout()
        self.file_button = QPushButton("Select File")
        self.file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_button)
        self.file_label = QLabel("No File Selected")
        file_layout.addWidget(self.file_label)
        layout.addLayout(file_layout)

        # Context directory selection
        context_layout = QHBoxLayout()
        self.context_button = QPushButton("Select Context Directory")
        self.context_button.clicked.connect(self.select_context_directory)
        context_layout.addWidget(self.context_button)
        self.context_label = QLabel("No Context Directory Selected")
        context_layout.addWidget(self.context_label)
        layout.addLayout(context_layout)

        # Batch directory selection
        batch_layout = QHBoxLayout()
        self.batch_button = QPushButton("Select Batch Directory")
        self.batch_button.clicked.connect(self.select_batch_directory)
        batch_layout.addWidget(self.batch_button)
        self.batch_label = QLabel("No Batch Directory Selected")
        batch_layout.addWidget(self.batch_label)
        layout.addLayout(batch_layout)

        # Process button
        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.process_request)
        layout.addWidget(self.process_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setVisible(False)  # Initially invisible
        layout.addWidget(self.progress_bar)

        # Output display
        layout.addWidget(QLabel("Output:"))
        self.output_area = QScrollArea()
        self.output_area.setWidgetResizable(True)
        self.output_widget = QTextBrowser()
        self.output_widget.setOpenExternalLinks(True)
        self.output_area.setWidget(self.output_widget)
        layout.addWidget(self.output_area)

        # Clear and Save buttons
        button_layout = QHBoxLayout()
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_output)
        button_layout.addWidget(self.clear_button)
        self.save_button = QPushButton("Save Output")
        self.save_button.clicked.connect(self.save_output)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        # Theme toggle button
        self.theme_button = QPushButton("Toggle Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)

        central_widget.setLayout(layout)

    def apply_theme(self):
        with open("style.qss", "r") as f:
            self.setStyleSheet(f.read())
        self.setProperty("class", self.current_theme)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def toggle_theme(self):
        self.current_theme = "GreyTheme" if self.current_theme == "RedTheme" else "RedTheme"
        self.apply_theme()

    def update_model_options(self):
        self.model_combo.clear()
        dev = self.dev_combo.currentText()
        if dev == "google":
            self.model_combo.addItems(["gemini-1.5-flash", "gemini-1.5-pro","gemini-1.5-flash-002", "gemini-1.5-pro-002"])
        elif dev == "openai":
            self.model_combo.addItems(["gpt-4o-mini", "gpt-4o", "dall-e-3"])
        elif dev == "mistral":
            self.model_combo.addItems(["open-mistral-nemo", "mistral-large-latest","codestral-latest"])
        elif dev == "anthropic":
            self.model_combo.addItems(["claude-3-5-sonnet-20240620", "claude-3-opus-20240229","claude-3-haiku-20240307"])
        elif dev == "ollama":  
            self.model_combo.addItems(["mannix/llama3.1-8b-abliterated:latest", "mistral-nemo:latest", "llama3.2:latest", "minicpm-v:latest","codestral:latest","phi3.5:latest"])

    def select_context_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Context Directory")
        if dir_path:
            self.playground.context_dir = dir_path
            self.context_label.setText(f"Context: {dir_path}")
        else:
            self.playground.context_dir = None
            self.context_label.setText("No Context Directory Selected")

    def select_batch_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Batch Directory")
        if dir_path:
            self.batch_dir = dir_path
            self.batch_label.setText(f"Batch Directory: {dir_path}")
        else:
            self.batch_dir = None
            self.batch_label.setText("No Batch Directory Selected")

    def select_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
            if file_path:
                self.file_path = file_path
                self.file_label.setText(f"File: {file_path}")
            else:
                self.file_path = None
                self.file_label.setText("No File Selected")
        except Exception as e:
            self.file_label.setText(f"Error: {str(e)}")

    def process_request(self):
        try:
            prompt = self.prompt_input.toPlainText()
            dev = self.dev_combo.currentText()
            model = self.model_combo.currentText()

            include_history = self.include_history_checkbox.isChecked()
            image_skip = self.image_skip_checkbox.isChecked()
    
            print(f"Image skip: {image_skip}")
            print(f"Include chat history: {include_history}") 
    
            if self.batch_dir:
                self.progress_bar.setVisible(True)
                self.progress_bar.setMaximum(100)
                batch_results = self.playground.batch_process(
                    self.batch_dir,
                    prompt,
                    dev,
                    model_name=model,
                    max_tokens=int(self.max_tok_input.text()),
                    include_chat_history=include_history,
                    image_skip=image_skip
                )
        
                total_files = len(batch_results)
                html_output = ""
        
                for i, (file_path, response) in enumerate(batch_results.items()):
                    html_output += f"<h3>File: {file_path}</h3>"
                    html_output += self.markdown_to_html(response)
                    html_output += "<hr>"
                    if (i + 1) % max(1, total_files // 20) == 0:  # Update every 5% of progress
                        progress_value = int((i + 1) / total_files * 100)
                        self.progress_bar.setValue(progress_value)
                        QApplication.processEvents()
                self.output_widget.append(html_output)
                self.progress_bar.setVisible(False)
            
            else:
                response = self.playground.process_prompt(
                    prompt=prompt,
                    dev=dev,
                    file_path=self.file_path,
                    model_name=model,
                    max_tokens=int(self.max_tok_input.text()),
                    include_chat_history=include_history,
                    image_skip=image_skip
                )
                
                # Handle image generation models
                if model == "dall-e-3":
                    self.handle_image_response(response)
                    self.playground.conversation.add_message("Assistant", "Generated image", response)
                else:
                    # Split the response into image summaries and content summary if applicable
                    if "Image summaries:" in response and "Content summary:" in response:
                        parts = response.split("Content summary:", 1)
                        image_summaries = parts[0].replace("Image summaries:", "").strip()
                        content_summary = parts[1].strip()
                        
                        html_response = f"<strong>Image Summaries:</strong><br>{self.markdown_to_html(image_summaries)}<br><br>"
                        html_response += f"<strong>Content Summary:</strong><br>{self.markdown_to_html(content_summary)}"
                    else:
                        html_response = self.markdown_to_html(response)
                    
                    # Handle images in the response
                    if "http://" in response or "https://" in response:
                        urls = [word for word in response.split() if word.startswith(('http://', 'https://'))]
                        for url in urls:
                            html_response = html_response.replace(url, f'<img src="{url}" />')
                    elif "file://" in response:
                        file_paths = [word for word in response.split() if word.startswith('file://')]
                        for file_path in file_paths:
                            html_response = html_response.replace(file_path, self.embed_image(file_path[7:]))
                    
                    # Append only the assistant's response to the output
                    self.output_widget.append(f"<strong>Assistant:</strong> {html_response}")
                    self.output_widget.append("<hr>")
                    
                    # Add only the assistant's response to the conversation history
                    self.playground.conversation.add_message("Assistant", response)
    
            # Scroll to the bottom of the output widget
            self.output_widget.verticalScrollBar().setValue(
                self.output_widget.verticalScrollBar().maximum()
            )
        except Exception as e:
            self.output_widget.append(f"<p style='color: red;'>Error: {str(e)}</p>")
            print(f"Error in process_request: {str(e)}")  # Add this line for debugging
        
    def handle_image_response(self, response):
        print(f"Handling image response: {response[:100]}...")  # Add this line for debugging
        if isinstance(response, str) and response.startswith("http"):
            # It's an image URL, download and display it
            self.download_and_display_image(response)
        elif isinstance(response, QImage):
            # It's already a QImage, display it directly
            self.display_image(response, url=None)  # You might want to store the URL somewhere if available
        else:
            # It's probably an error message, display it as text
            self.output_widget.append(f"<strong>Assistant:</strong> {response}")

    def download_and_display_image(self, url):
        print(f"Downloading image from URL: {url}")
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        # Connect the finished signal to a lambda function that passes both reply and url
        reply.finished.connect(lambda: self.on_image_downloaded(reply, url))

    def on_image_downloaded(self, reply, url):
        error = reply.error()
        if error == QNetworkReply.NetworkError.NoError:
            image_data = reply.readAll()
            image = QImage()
            image.loadFromData(image_data)
            if not image.isNull():
                self.display_image(image, url)
            else:
                print("Error: Downloaded image is null")
                self.output_widget.append("Error: Unable to load the image.")
        else:
            error_message = f"Error downloading image: {reply.errorString()}"
            print(error_message)
            self.output_widget.append(error_message)

    def display_image(self, image, url=None):
        pixmap = QPixmap.fromImage(image)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
            image_label = QLabel()
            image_label.setPixmap(scaled_pixmap)
            self.output_widget.insertHtml('<br>')
            cursor = self.output_widget.textCursor()
            cursor.insertText('\n')
            self.output_widget.setTextCursor(cursor)
            self.output_widget.insertHtml('<br>')
            
            # Create a unique name for each image
            image_name = f"generated_image_{id(image)}"
            
            # Add the image to the document's resource collection
            self.output_widget.document().addResource(
                QTextDocument.ResourceType.ImageResource,
                QUrl(image_name), 
                scaled_pixmap
            )
            
            # Create an image format and insert it into the document
            image_format = QTextImageFormat()
            image_format.setName(image_name)
            image_format.setWidth(scaled_pixmap.width())
            image_format.setHeight(scaled_pixmap.height())
            cursor.insertImage(image_format)
            
            # Add the hyperlink with the image URL
            if url:
                self.output_widget.insertHtml(f'<br><a href="{url}">Image-link</a><br><br>')
            else:
                self.output_widget.insertHtml('<br><br>')

    def clear_output(self):
        self.output_widget.clear()
        self.playground.clear_history()
        print("Conversation history cleared.")

    def save_output(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Output", "", "HTML Files (*.html);;Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            if selected_filter == "HTML Files (*.html)":
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.output_widget.toHtml())
            else:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.output_widget.toPlainText())

    def markdown_to_html(self, text):
        # Convert markdown to HTML
        html = markdown.markdown(text)
        
        # Replace LaTeX equations with MathJax rendering
        html = re.sub(r'\$\$(.*?)\$\$', lambda m: f'\\({m.group(1)}\\)', html)
        html = re.sub(r'\$(.*?)\$', lambda m: f'\\({m.group(1)}\\)', html)
        
        # Wrap the content with MathJax script
        html = f'''
        <html>
        <head>
        <script type="text/javascript" async
          src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
        </script>
        </head>
        <body>
        {html}
        </body>
        </html>
        '''
        return html

    def embed_image(self, image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f'<img src="data:image/png;base64,{encoded_string}" />'

    def closeEvent(self, event):
        self.clear_output()
        event.accept()  # Accept the event to close the window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIPlaygroundGUI()
    window.show()
    sys.exit(app.exec())