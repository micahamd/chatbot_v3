import sys
import io
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QComboBox, QTextEdit, QFileDialog, 
                             QLabel, QScrollArea, QCheckBox, QProgressBar, QLineEdit,
                             QStyleFactory)
from PyQt6.QtGui import (QPixmap, QTextCursor, QTextDocument, QIntValidator, QFontDatabase)
from PyQt6.QtCore import (QUrl, Qt)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from model_interact import AIPlayground
from prep_file import context_directory


class AIPlaygroundGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Playground")
        self.setGeometry(100, 100, 1000, 700)  # Increased window size for better layout
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_image_downloaded)

        self.playground = AIPlayground(context_dir=None)
        self.file_path = None
        self.batch_dir = None
        self.current_theme = "RedTheme"  # Default theme
        
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
        self.dev_combo.addItems(["google", "openai", "mistral"])
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
        self.context_checkbox = QCheckBox("Use Context Directory")
        context_layout.addWidget(self.context_checkbox)
        self.context_button = QPushButton("Select Context Directory")
        self.context_button.clicked.connect(self.select_context_directory)
        context_layout.addWidget(self.context_button)
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
        self.output_widget = QTextEdit()
        self.output_widget.setReadOnly(True)
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
            self.model_combo.addItems(["gemini-1.5-flash", "gemini-1.5-pro"])
        elif dev == "openai":
            self.model_combo.addItems(["gpt-4o-mini", "gpt-4o"])
        elif dev == "mistral":
            self.model_combo.addItems(["open-mistral-nemo", "mistral-large-latest"])

    def select_context_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Context Directory")
        if dir_path:
            self.playground.context_dir = dir_path
            self.context_button.setText(f"Context: {dir_path}")
        else:
            self.playground.context_dir = None
            self.context_button.setText("Select Context Directory")

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
            
            if self.context_checkbox.isChecked() and self.playground.context_dir:
                self.playground.update_context()
            
            include_history = self.include_history_checkbox.isChecked()
            
            if self.batch_dir:
                self.progress_bar.setVisible(True)  # Make sure the progress bar is visible
                self.progress_bar.setMaximum(100)
                batch_results = self.playground.batch_process(
                    self.batch_dir,
                    prompt,
                    dev,
                    model_name=model,
                    max_tokens=int(self.max_tok_input.text()),
                    include_chat_history=include_history
                )
                total_files = len(batch_results)
                for i, (file_path, response) in enumerate(batch_results.items()):
                    self.output_widget.append(f"File: {file_path}\nResponse:\n{response}\n")
                    self.output_widget.append("="*10 + "\n")  # Add a separator line
                    progress_value = int((i + 1) / total_files * 100)
                    self.progress_bar.setValue(progress_value)
                    QApplication.processEvents()  # Allow the GUI to update
                self.progress_bar.setVisible(False)  # Hide the progress bar when done
            else:
                response = self.playground.process_prompt(
                    prompt=prompt,
                    dev=dev,
                    file_path=self.file_path,
                    model_name=model,
                    max_tokens=int(self.max_tok_input.text()),
                    include_chat_history=include_history
                )
                self.output_widget.append(f"Response:\n{response}\n")
                
                # Check if the response contains an image URL or file path
                if "http://" in response or "https://" in response:
                    urls = [word for word in response.split() if word.startswith(('http://', 'https://'))]
                    for url in urls:
                        self.display_image(url)
                elif "file://" in response:
                    file_paths = [word for word in response.split() if word.startswith('file://')]
                    for file_path in file_paths:
                        self.display_image(file_path[7:])  # Remove 'file://' prefix
        except Exception as e:
            self.output_widget.append(f"Error: {str(e)}\n")
    
    def clear_output(self):
        self.output_widget.clear()
        self.playground.clear_history()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIPlaygroundGUI()
    window.show()
    sys.exit(app.exec())