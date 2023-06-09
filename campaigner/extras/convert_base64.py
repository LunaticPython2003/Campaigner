import tkinter as tk
from tkinter import filedialog
import base64

def convert_to_base64():
    # Open file dialog to select a file
    filepath = filedialog.askopenfilename()

    try:
        # Read the file as binary
        with open(filepath, 'rb') as file:
            # Read file contents
            file_content = file.read()

            # Convert file content to Base64
            base64_content = base64.b64encode(file_content).decode('utf-8')

            # Display the Base64 content in a text box
            text_box.delete(1.0, tk.END)  # Clear previous content
            text_box.insert(tk.END, base64_content)

    except FileNotFoundError:
        # Handle file not found error
        text_box.delete(1.0, tk.END)
        text_box.insert(tk.END, "File not found.")

# Create the main Tkinter window
window = tk.Tk()
window.title("File to Base64 Converter")

# Create a button to browse and convert a file
browse_button = tk.Button(window, text="Browse", command=convert_to_base64)
browse_button.pack(pady=10)

# Create a text box to display the Base64 content
text_box = tk.Text(window, height=10, width=50)
text_box.pack()

# Run the Tkinter event loop
window.mainloop()
