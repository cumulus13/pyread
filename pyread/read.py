import time
import ast
import sys
import os
import jedi
import argparse
from jsoncolor import jprint
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.syntax import Syntax
from rich_argparse import RichHelpFormatter, _lazy_rich as rr
from typing import ClassVar, Dict, List, Optional, Union
from rich import traceback as rich_traceback
import shutil
from pydebugger.debug import debug
import pyperclip

# Configure rich traceback
rich_traceback.install(theme='fruity', max_frames=30, width=shutil.get_terminal_size()[0])

console = Console()
start_time = time.time()


class CustomRichHelpFormatter(RichHelpFormatter):
    """A custom RichHelpFormatter with enhanced styles."""

    styles: ClassVar[dict[str, rr.StyleType]] = {
        "argparse.args": "bold #FFFF00",
        "argparse.groups": "#AA55FF",
        "argparse.help": "bold #00FFFF",
        "argparse.metavar": "bold #FF00FF",
        "argparse.syntax": "underline",
        "argparse.text": "white",
        "argparse.prog": "bold #00AAFF italic",
        "argparse.default": "bold",
    }


class CodeElement:
    """Represents a code element (function or method) with metadata."""
    
    def __init__(self, node: ast.FunctionDef, class_name: Optional[str] = None):
        self.node = node
        self.name = node.name
        self.class_name = class_name
        self.lineno = node.lineno
        self.end_lineno = node.end_lineno
        self.decorator_list = node.decorator_list
        
    @property
    def full_name(self) -> str:
        """Get the full name including class if applicable."""
        return f"{self.class_name}.{self.name}" if self.class_name else self.name
        
    @property
    def start_line(self) -> int:
        """Get the starting line including decorators."""
        if self.decorator_list:
            return min(decorator.lineno for decorator in self.decorator_list) - 1
        return self.lineno - 1


class EnhancedCodeVisitor(ast.NodeVisitor):
    """Enhanced visitor that collects all classes and functions with better organization."""
    
    def __init__(self):
        self.classes: Dict[str, List[str]] = {}
        self.functions: Dict[str, List[CodeElement]] = {}
        self.current_class: Optional[str] = None
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition and collect methods."""
        self.current_class = node.name
        self.classes[node.name] = []
        
        # Visit all methods in this class
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                self.classes[node.name].append(child.name)
                
                # Add to functions dict with class context
                if node.name not in self.functions:
                    self.functions[node.name] = []
                self.functions[node.name].append(CodeElement(child, node.name))
        
        self.current_class = None
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit standalone function definition."""
        if self.current_class is None:  # Only standalone functions
            if 'standalone' not in self.functions:
                self.functions['standalone'] = []
            self.functions['standalone'].append(CodeElement(node))


class CodeAnalyzer:
    """Main class for analyzing Python code structure."""
    
    def __init__(self, filename: Optional[str] = None):
        self.source_data: Optional[str] = None
        self.tree_data: Optional[ast.AST] = None
        self.filename = filename
        
        if filename and os.path.isfile(filename):
            self._load_file(filename)
    
    def _load_file(self, filename: str) -> None:
        """Load and parse a Python file."""
        try:
            with open(filename, "r", encoding='utf-8') as file:
                self.source_data = file.read()
                self.tree_data = ast.parse(self.source_data)
                self.filename = filename
        except Exception as e:
            console.print(f"[red]❌ Error loading file {filename}: {e}[/]")
            raise
    
    def process_file(self, filename: str) -> tuple[str, ast.AST]:
        """Process a new file and return source and AST."""
        self._load_file(filename)
        return self.source_data, self.tree_data
    
    def get_structure(self) -> Dict[str, List[str]]:
        """Get the complete structure of classes and methods."""
        if not self.tree_data:
            return {}
            
        visitor = EnhancedCodeVisitor()
        visitor.visit(self.tree_data)
        
        # Combine classes and standalone functions
        structure = visitor.classes.copy()
        if visitor.functions.get('standalone'):
            structure['📄 Standalone Functions'] = [
                elem.name for elem in visitor.functions['standalone']
            ]
            
        return structure
    
    def find_code_elements(self, target_name: str, class_name: Optional[str] = None) -> List[CodeElement]:
        """Find code elements by name, optionally within a specific class."""
        if not self.tree_data:
            return []
            
        visitor = EnhancedCodeVisitor()
        visitor.visit(self.tree_data)
        
        results = []
        
        if class_name:
            # Look for method in specific class
            class_elements = visitor.functions.get(class_name, [])
            for element in class_elements:
                if element.name == target_name:
                    results.append(element)
        else:
            # Look in all classes and standalone functions
            for class_key, elements in visitor.functions.items():
                for element in elements:
                    if element.name == target_name:
                        results.append(element)
        
        return results
    
    def extract_code(self, element: CodeElement) -> str:
        """Extract the source code for a given code element."""
        if not self.source_data:
            return ""
            
        code_lines = self.source_data.splitlines()[element.start_line:element.end_lineno]
        return "\n".join(code_lines)
    
    def print_structure(self) -> None:
        """Print the code structure as a beautiful tree."""
        structure = self.get_structure()
        
        if not structure:
            console.print("[yellow]⚠️  No classes or functions found[/]")
            return
            
        filename_display = self.filename or "Code Structure"
        root = Tree(
            f"🐍 [bold #00FF88]Python Code Analysis[/] [dim]│[/] [bold #55FFFF]{filename_display}[/]",
            guide_style="bold #00AAFF"
        )
        
        for container_name, items in structure.items():
            if container_name == '📄 Standalone Functions':
                container_tree = root.add(f"📄 [bold #FF6B35]Standalone Functions[/]")
                icon = "🔧"
            else:
                container_tree = root.add(f"🏛️ [bold #FF1744 on #F5F5F5]{container_name}[/]")
                icon = "⚙️"
                
            for item in items:
                container_tree.add(f"{icon} [bold #FFD700]{item}[/]")
        
        console.print(root)
    
    def display_code(self, element: CodeElement, theme: str = 'fruity') -> None:
        """Display code with syntax highlighting and copy to clipboard."""
        code = self.extract_code(element)
        
        if not code:
            console.print(f"[red]❌ Could not extract code for {element.full_name}[/]")
            return
        
        # Header with icon and styling
        if element.class_name:
            header = f"🏛️ [black on #00FF88]Class Method[/] [black on #FFD700]'{element.full_name}'[/]"
        else:
            header = f"🔧 [black on #00FF88]Function[/] [black on #FFD700]'{element.name}'[/]"
            
        console.print(f"\n{header}\n")
        
        # Syntax highlighting
        syntax = Syntax(
            code, 
            'python', 
            theme=theme, 
            line_numbers=True, 
            tab_size=4, 
            word_wrap=True,
            code_width=shutil.get_terminal_size()[0] - 4
        )
        
        console.print(syntax)
        
        # Copy to clipboard
        pyperclip.copy(code)
        console.print(f"[dim]📋 Code copied to clipboard[/]")
    
    def get_available_themes(self) -> List[str]:
        """Get list of available syntax highlighting themes."""
        from pygments.styles import get_all_styles
        return sorted(list(get_all_styles()))
    
    def print_themes(self) -> None:
        """Print all available themes in a formatted list."""
        themes = self.get_available_themes()
        console.print(f"\n[bold #00FFFF]🎨 Available Syntax Themes ({len(themes)} total)[/]\n")
        
        for i, theme in enumerate(themes, 1):
            console.print(f"[dim]{str(i).zfill(2)}.[/] [bold #FFD700]{theme}[/]")
    
    def display_code_from_clipboard(self, theme: str = 'fruity', code_type: str = 'python') -> None:
        """Display clipboard content with syntax highlighting."""
        try:
            content = pyperclip.paste()
            if not content.strip():
                console.print("[yellow]⚠️  Clipboard is empty[/]")
                return
                
            console.print("[bold #00FF88]📋 Code from Clipboard[/]\n")
            syntax = Syntax(content, code_type, theme=theme, line_numbers=True)
            console.print(syntax)
            
        except Exception as e:
            console.print(f"[red]❌ Error reading clipboard: {e}[/]")
    
    def save_to_file(self, content: str, filename: str) -> bool:
        """Save content to file with error handling."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(content)
            console.print(f"[bold #00FF88]✅ File saved successfully:[/] [bold #FFD700]{filename}[/]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error saving file: {e}[/]")
            return False
    
    def interactive_save_mode(self) -> Optional[str]:
        """Interactive mode for saving files with improved UX."""
        console.print(f"\n[bold #55FFFF]💾 Save Mode[/] [dim]│[/] [bold #00FFFF]Enter filename[/] [dim]or[/] [bold #FF00FF]'q'/'exit' to quit[/]")
        
        while True:
            try:
                command = input("📝 ").strip()
                
                if not command:
                    console.print("[yellow]⚠️  Please enter a filename or 'q' to quit[/]")
                    continue
                    
                if command.lower() in ['exit', 'quit', 'q', 'x']:
                    console.print("[bold #FFD700]👋 Exiting save mode[/]")
                    return None
                
                # Validate filename
                if os.path.isdir(command):
                    console.print(f"[red]❌ '{command}' is a directory, not a valid filename[/]")
                    continue
                
                # Check if directory exists (if path contains directory)
                dirname = os.path.dirname(command)
                if dirname and not os.path.exists(dirname):
                    console.print(f"[yellow]⚠️  Directory '{dirname}' doesn't exist. Create it? (y/n)[/]")
                    create = input("🤔 ").strip().lower()
                    if create in ['y', 'yes']:
                        try:
                            os.makedirs(dirname, exist_ok=True)
                            console.print(f"[green]✅ Directory '{dirname}' created[/]")
                        except Exception as e:
                            console.print(f"[red]❌ Failed to create directory: {e}[/]")
                            continue
                    else:
                        continue
                
                return command
                
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Interrupted by user[/]")
                return None
            except Exception as e:
                console.print(f"[red]❌ Unexpected error: {e}[/]")
                continue


def main():
    """Main function with improved command line interface."""
    analyzer = CodeAnalyzer()
    
    parser = argparse.ArgumentParser(
        description="🐍 Advanced Python Code Analyzer with Rich Display",
        formatter_class=CustomRichHelpFormatter
    )
    
    parser.add_argument(
        'FILE', 
        help='Python file to analyze, or "c" to read from clipboard',
        nargs='?'
    )
    parser.add_argument(
        '-m', '--method',
        help='Show specific method/function (use Class.method for class methods)',
        metavar='NAME'
    )
    parser.add_argument(
        '-s', '--style',
        help='Syntax highlighting theme (default: fruity)',
        default='fruity',
        metavar='THEME'
    )
    parser.add_argument(
        '-l', '--list-themes',
        help='List all available syntax highlighting themes',
        action='store_true'
    )
    parser.add_argument(
        '-t', '--type',
        help='Code type for syntax highlighting (default: python)',
        default='python',
        metavar='TYPE'
    )
    parser.add_argument(
        '-c', '--code',
        help='Display the entire source code with syntax highlighting',
        action='store_true'
    )
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Handle theme listing
    if args.list_themes:
        analyzer.print_themes()
        return
    
    # Handle file input
    if args.FILE:
        if args.FILE == 'c':
            # Clipboard mode
            analyzer.display_code_from_clipboard(args.style, args.type)
            
            # Interactive save mode
            filename = analyzer.interactive_save_mode()
            if filename:
                content = pyperclip.paste()
                analyzer.save_to_file(content, filename)
                
        elif os.path.isfile(args.FILE):
            # File mode
            try:
                analyzer.process_file(args.FILE)
                
                if args.method:
                    # Handle specific method/function
                    class_name = None
                    method_name = args.method
                    
                    if '.' in args.method:
                        class_name, method_name = args.method.split('.', 1)
                    
                    elements = analyzer.find_code_elements(method_name, class_name)
                    
                    if elements:
                        for element in elements:
                            analyzer.display_code(element, args.style)
                    else:
                        if class_name:
                            console.print(f"[red]❌ Method '{method_name}' not found in class '{class_name}'[/]")
                        else:
                            console.print(f"[red]❌ Function/method '{method_name}' not found[/]")
                
                elif args.code:
                    # Display entire file
                    with open(args.FILE, 'r', encoding='utf-8') as f:
                        content = f.read()
                    console.print(f"[bold #00FF88]📄 Complete Source Code:[/] [bold #55FFFF]{args.FILE}[/]\n")
                    syntax = Syntax(content, 'python', theme=args.style, line_numbers=True)
                    console.print(syntax)
                
                else:
                    # Show structure
                    analyzer.print_structure()
                    
            except Exception as e:
                console.print(f"[red]❌ Error processing file: {e}[/]")
        else:
            console.print(f"[red]❌ File '{args.FILE}' not found[/]")
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Program interrupted by user[/]")
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/]")
    finally:
        end_time = time.time()
        execution_time = end_time - start_time
        console.print(f"[dim]⏱️  Execution time: {execution_time:.3f}s[/]")