import pyperclip
from rich.console import Console
from rich.syntax import Syntax
import os

def display_code_with_syntax_highlighting(code: str):
    """Display the clipboard content with syntax highlighting."""
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console = Console()
    console.print(syntax)

def save_to_file(content: str, filename: str):
    """Save the content to the specified file."""
    try:
        with open(filename, 'w') as file:
            file.write(content)
        print(f"File saved successfully as {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")

def vim_like_mode():
    """Mimic a simple Vim-like mode for saving files."""
    print("\nVim-like mode activated. Type ':filename' to save, or 'exit' to quit.")
    while True:
        command = input(":").strip()  # Strip any extra spaces
        if command and command.lower() in ['exit','quit','q','x']:
            print("Exiting Vim-like mode.")
            break
        elif command and os.path.isdir(os.path.dirname(command)):
            # filename = command[1:].strip()  # Get the filename after the colon
            # filname = command
            if command:
                # Check for invalid filename cases
                if not os.path.isdir(command):
                    return command
                else:
                    print(f"Invalid filename: {command} is a directory.")
            else:
                print("Please provide a valid filename after ':'.")
        elif command:
            return command
        else:
            print("Invalid command. Use ':filename' to save, or 'exit' to quit.")

if __name__ == "__main__":
    # Read clipboard content
    clipboard_content = pyperclip.paste()

    # Display the content with syntax highlighting
    print("Clipboard content (Python code):\n")
    display_code_with_syntax_highlighting(clipboard_content)

    # Enter Vim-like mode for saving the file
    filename = vim_like_mode()

    if filename:
        # Save clipboard content to the specified file
        save_to_file(clipboard_content, filename)
