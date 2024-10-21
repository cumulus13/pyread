from textual.app import App, ComposeResult
from textual.widgets import TextArea, Header, Footer
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import TerminalFormatter
from pygments.styles import get_style_by_name
import os
import sys
import re  # For removing ANSI codes

class SimpleTextEditor(App):
    CSS_PATH = "simple_editor.css"
    TITLE = "Simple Text Editor"
    SUB_TITLE = "Press 'Ctrl+S' to save, 'Ctrl+Q' to quit"

    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.file_extension = ""
        self.file_name = ""
        self.original_content = ""  # This will store the raw, unhighlighted content

    def compose(self) -> ComposeResult:
        yield Header()
        self.text_area = TextArea()
        yield self.text_area
        yield Footer()

    def on_mount(self) -> None:
        """This function runs when the application starts."""
        if self.file_path:
            self.file_name = os.path.basename(self.file_path)
            self.file_extension = os.path.splitext(self.file_path)[1][1:]  # Get extension without dot
            self.load_file()

    def load_file(self) -> None:
        """Loads the file content into the text area."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                content = f.read()
                self.original_content = content  # Store the plain text
                highlighted_content = self.highlight_code(content)
                self.text_area.value = highlighted_content
        else:
            self.text_area.value = ""  # Load empty editor if file doesn't exist

    def highlight_code(self, content: str) -> str:
        """Applies syntax highlighting based on the file extension."""
        try:
            if self.file_extension == "py":
                lexer = get_lexer_by_name("python")
            else:
                lexer = guess_lexer(content)
        except:
            lexer = get_lexer_by_name("text")  # Default to plain text

        # Apply syntax highlighting using Pygments
        return highlight(content, lexer, TerminalFormatter(style=get_style_by_name("fruity")))

    async def on_key(self, event) -> None:
        """Handle key events like Ctrl+S and Ctrl+Q."""
        if event.key == "ctrl+s":  # Ctrl+S to save
            self.save_file()
        elif event.key == "ctrl+q":  # Ctrl+Q to quit
            self.exit()

    def save_file(self) -> None:
        """Save the content of the text area to the file (without ANSI codes)."""
        if not self.file_name:
            self.file_name = self.text_area.prompt("Enter file name: ")

        # Save the original content (plain text) to avoid saving ANSI color codes
        with open(self.file_name, "w") as f:
            f.write(self.original_content)
        self.console.print(f"File saved as: {self.file_name}")

    async def on_text_changed(self, event) -> None:
        """Update the original content whenever the text changes."""
        self.original_content = event.value  # Keep the plain text content for saving

if __name__ == "__main__":
    # If a file path is provided as an argument, pass it to the editor
    file_to_edit = sys.argv[1] if len(sys.argv) > 1 else None

    # Start the application
    SimpleTextEditor(file_path=file_to_edit).run()
