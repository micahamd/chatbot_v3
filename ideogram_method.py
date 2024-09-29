import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import os
from dotenv import load_dotenv
import json
from PIL import Image, ImageTk
from io import BytesIO
import webbrowser
import traceback

class IdeogramAPIGUI:
    def __init__(self, master):
        self.master = master
        master.title("Ideogram API GUI")
        master.geometry("800x600")

        load_dotenv()
        self.api_key = os.getenv("IDEOGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("IDEOGRAM_API_KEY environment variable not set")

        self.image_counter = 0
        self.image_path = tk.StringVar()  # Initialize image_path here
        self.create_widgets()

    def create_widgets(self):
        # Function selection
        ttk.Label(self.master, text="Select Function:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.function_var = tk.StringVar()
        functions = ['generate', 'remix', 'upscale', 'describe']
        self.function_dropdown = ttk.Combobox(self.master, textvariable=self.function_var, values=functions, state="readonly")
        self.function_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.function_dropdown.bind("<<ComboboxSelected>>", self.update_parameters)

        # Parameters frame
        self.params_frame = ttk.Frame(self.master)
        self.params_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nswe")

        # Submit and Clear buttons
        self.submit_button = ttk.Button(self.master, text="Submit", command=self.submit_request)
        self.submit_button.grid(row=2, column=0, padx=5, pady=5)
        self.clear_button = ttk.Button(self.master, text="Clear Window", command=self.clear_window)
        self.clear_button.grid(row=2, column=1, padx=5, pady=5)

        # Output frame with scrollbar
        self.output_frame = ttk.Frame(self.master)
        self.output_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nswe")
        self.master.grid_rowconfigure(3, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.output_frame)
        self.scrollbar = ttk.Scrollbar(self.output_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.output_frame.grid_rowconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Response text
        self.response_text_frame = ttk.Frame(self.scrollable_frame)
        self.response_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.response_text = scrolledtext.ScrolledText(self.response_text_frame, height=10, width=70, wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True)

        # Initialize with generate parameters
        self.update_parameters(None)

    def update_parameters(self, event):
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        function = self.function_var.get()

        if function == 'generate':
            self.create_generate_params()
        elif function == 'remix':
            self.create_remix_params()
        elif function == 'upscale':
            self.create_upscale_params()
        elif function == 'describe':
            self.create_describe_params()

    def create_generate_params(self):
        ttk.Label(self.params_frame, text="Prompt:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prompt_entry = ttk.Entry(self.params_frame, width=50)
        self.prompt_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Aspect Ratio:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.aspect_ratio_var = tk.StringVar()
        aspect_ratios = ['ASPECT_1_1', 'ASPECT_16_9', 'ASPECT_9_16']
        self.aspect_ratio_dropdown = ttk.Combobox(self.params_frame, textvariable=self.aspect_ratio_var, values=aspect_ratios, state="readonly")
        self.aspect_ratio_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Model:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.model_var = tk.StringVar()
        models = ['V_1', 'V_1_TURBO', 'V_2', 'V_2_TURBO']
        self.model_dropdown = ttk.Combobox(self.params_frame, textvariable=self.model_var, values=models, state="readonly")
        self.model_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Magic Prompt:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.magic_prompt_var = tk.StringVar()
        magic_prompts = ['AUTO', 'ON', 'OFF']
        self.magic_prompt_dropdown = ttk.Combobox(self.params_frame, textvariable=self.magic_prompt_var, values=magic_prompts, state="readonly")
        self.magic_prompt_dropdown.grid(row=3, column=1, padx=5, pady=5, sticky="we")

    def create_remix_params(self):
        ttk.Label(self.params_frame, text="Prompt:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prompt_entry = ttk.Entry(self.params_frame, width=50)
        self.prompt_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Image:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.image_path = tk.StringVar()
        self.image_entry = ttk.Entry(self.params_frame, textvariable=self.image_path, width=40)
        self.image_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(self.params_frame, text="Browse", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(self.params_frame, text="Aspect Ratio:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.aspect_ratio_var = tk.StringVar()
        aspect_ratios = ['ASPECT_1_1', 'ASPECT_16_9', 'ASPECT_9_16']
        self.aspect_ratio_dropdown = ttk.Combobox(self.params_frame, textvariable=self.aspect_ratio_var, values=aspect_ratios, state="readonly")
        self.aspect_ratio_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Image Weight:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.image_weight_entry = ttk.Entry(self.params_frame, width=10)
        self.image_weight_entry.insert(0, "50")
        self.image_weight_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.params_frame, text="Magic Prompt:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.magic_prompt_var = tk.StringVar()
        magic_prompts = ['AUTO', 'ON', 'OFF']
        self.magic_prompt_dropdown = ttk.Combobox(self.params_frame, textvariable=self.magic_prompt_var, values=magic_prompts, state="readonly")
        self.magic_prompt_dropdown.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Model:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.model_var = tk.StringVar()
        models = ['V_1', 'V_1_TURBO', 'V_2', 'V_2_TURBO']
        self.model_dropdown = ttk.Combobox(self.params_frame, textvariable=self.model_var, values=models, state="readonly")
        self.model_dropdown.grid(row=5, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Negative Prompt:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.negative_prompt_entry = ttk.Entry(self.params_frame, width=50)
        self.negative_prompt_entry.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky="we")

    def create_upscale_params(self):
        ttk.Label(self.params_frame, text="Image:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.image_path = tk.StringVar()
        self.image_entry = ttk.Entry(self.params_frame, textvariable=self.image_path, width=40)
        self.image_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(self.params_frame, text="Browse", command=self.browse_image).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.params_frame, text="Prompt (optional):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.prompt_entry = ttk.Entry(self.params_frame, width=50)
        self.prompt_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Resemblance:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.resemblance_entry = ttk.Entry(self.params_frame, width=10)
        self.resemblance_entry.insert(0, "50")
        self.resemblance_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.params_frame, text="Detail:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.detail_entry = ttk.Entry(self.params_frame, width=10)
        self.detail_entry.insert(0, "50")
        self.detail_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.params_frame, text="Magic Prompt:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.magic_prompt_var = tk.StringVar()
        magic_prompts = ['AUTO', 'ON', 'OFF']
        self.magic_prompt_dropdown = ttk.Combobox(self.params_frame, textvariable=self.magic_prompt_var, values=magic_prompts, state="readonly")
        self.magic_prompt_dropdown.grid(row=4, column=1, padx=5, pady=5, sticky="we")

    def create_describe_params(self):
        ttk.Label(self.params_frame, text="Image:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.image_path = tk.StringVar()
        self.image_entry = ttk.Entry(self.params_frame, textvariable=self.image_path, width=40)
        self.image_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(self.params_frame, text="Browse", command=self.browse_image).grid(row=0, column=2, padx=5, pady=5)

    def create_image_input_params(self, function):
        if function != 'describe':
            ttk.Label(self.params_frame, text="Prompt:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.prompt_entry = ttk.Entry(self.params_frame, width=50)
            self.prompt_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(self.params_frame, text="Image:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.image_path = tk.StringVar()
        self.image_entry = ttk.Entry(self.params_frame, textvariable=self.image_path, width=40)
        self.image_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(self.params_frame, text="Browse", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)

    def browse_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")])
        if filename:
            self.image_path.set(filename)

    def submit_request(self):
        try:
            function = self.function_var.get()
            url = f"https://api.ideogram.ai/{function}"

            if function == 'generate':
                payload = {
                    "image_request": {
                        "prompt": self.prompt_entry.get(),
                        "aspect_ratio": self.aspect_ratio_var.get(),
                        "model": self.model_var.get(),
                        "magic_prompt_option": self.magic_prompt_var.get()
                    }
                }
                headers = {
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json"
                }
                response = requests.post(url, json=payload, headers=headers)
            elif function in ['remix', 'upscale', 'describe']:
                if not self.image_path.get():
                    messagebox.showerror("Error", "Please select an image file.")
                    return
                
                files = {"image_file": open(self.image_path.get(), "rb")}
                data = {"image_request": json.dumps(self.get_function_params(function))}
                headers = {"Api-Key": self.api_key}
                response = requests.post(url, files=files, data=data, headers=headers)

            if response.status_code == 200:
                self.display_response(response.json(), function)
            else:
                error_message = f"Request failed with status code {response.status_code}\n"
                error_message += f"Response content: {response.text}"
                messagebox.showerror("Error", error_message)
                print(error_message)  # Print to console for debugging
        except Exception as e:
            error_message = f"An error occurred: {str(e)}\n"
            error_message += traceback.format_exc()
            messagebox.showerror("Error", error_message)
            print(error_message)  # Print to console for debugging

    def get_function_params(self, function):
        if function == 'remix':
            return {
                "prompt": self.prompt_entry.get(),
                "aspect_ratio": self.aspect_ratio_var.get(),
                "image_weight": int(self.image_weight_entry.get()),
                "magic_prompt_option": self.magic_prompt_var.get(),
                "model": self.model_var.get(),
                "negative_prompt": self.negative_prompt_entry.get()
            }
        elif function == 'upscale':
            return {
                "prompt": self.prompt_entry.get(),
                "resemblance": int(self.resemblance_entry.get()),
                "detail": int(self.detail_entry.get()),
                "magic_prompt_option": self.magic_prompt_var.get()
            }
        elif function == 'describe':
            return {}  # No additional parameters for describe
        else:
            raise ValueError(f"Unknown function: {function}")

    def display_response(self, response_data, function):
        try:
            self.response_text.insert(tk.END, json.dumps(response_data, indent=2) + "\n\n")

            if function == 'describe':
                self.display_text_response(response_data)
            else:
                self.display_images(response_data)

            self.canvas.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            error_message = f"Error displaying response: {str(e)}\n"
            error_message += traceback.format_exc()
            messagebox.showerror("Error", error_message)
            print(error_message)  # Print to console for debugging

    def display_text_response(self, response_data):
        if 'descriptions' in response_data:
            descriptions = response_data['descriptions']
            for i, desc in enumerate(descriptions, 1):
                self.response_text.insert(tk.END, f"\nDescription {i}:\n")
                self.response_text.insert(tk.END, desc.get('description', 'No description available') + "\n")

    def display_images(self, response_data):
        if 'data' in response_data and isinstance(response_data['data'], list):
            for image_data in response_data['data']:
                if 'url' in image_data:
                    image_url = image_data['url']
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        image = Image.open(BytesIO(image_response.content))
                        self.display_single_image(image, image_url)

    def display_single_image(self, image, url):
        image.thumbnail((300, 300))  # Resize image to fit in the UI
        photo = ImageTk.PhotoImage(image)

        image_frame = ttk.Frame(self.scrollable_frame)
        image_frame.pack(pady=10)

        image_label = ttk.Label(image_frame, image=photo)
        image_label.image = photo  # Keep a reference to prevent garbage collection
        image_label.pack()

        button_frame = ttk.Frame(image_frame)
        button_frame.pack(pady=5)

        view_button = ttk.Button(button_frame, text="View Full Image", 
                                 command=lambda: webbrowser.open_new(url))
        view_button.pack(side=tk.LEFT, padx=5)

        save_button = ttk.Button(button_frame, text="Save Image", 
                                 command=lambda: self.save_image(image))
        save_button.pack(side=tk.LEFT, padx=5)

        self.image_counter += 1

    def save_image(self, image):
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"),
                                                            ("JPEG files", "*.jpg"),
                                                            ("All files", "*.*")])
        if file_path:
            image.save(file_path)
            messagebox.showinfo("Success", "Image saved successfully!")

    def clear_window(self):
        try:
            # Clear the response text
            self.response_text.delete(1.0, tk.END)

            # Remove all displayed images
            for widget in self.scrollable_frame.winfo_children():
                if isinstance(widget, ttk.Frame) and widget != self.response_text_frame:
                    widget.destroy()

            # Reset the image counter
            self.image_counter = 0

            # Update the canvas scroll region
            self.canvas.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

            print("Window cleared successfully")
        except Exception as e:
            error_message = f"Error clearing window: {str(e)}\n"
            error_message += traceback.format_exc()
            messagebox.showerror("Error", error_message)
            print(error_message)  # Print to console for debugging
            
if __name__ == "__main__":
    root = tk.Tk()
    app = IdeogramAPIGUI(root)
    root.mainloop()