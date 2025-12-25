#!/usr/bin/env python3

# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-09-23 10:08:46.578627
# Description: A powerful, feature-rich Python code analyzer with beautiful syntax highlighting, duplicate detection, Git integration, and interactive capabilities. Built with Rich library for stunning terminal output.
# License: MIT

import time
import ast
import sys
import os
# import jedi

exceptions = []
LOG_LEVEL = "DEBUG"
tprint = None  # type: ignore

if str(os.getenv('DEBUG', '0')).lower() in ['1', 'true', 'ok', 'yes']:
    print("🐞 Debug mode enabled")
    os.environ['LOGGING'] = "1"
    os.environ.pop('NO_LOGGING', None)
    os.environ['TRACEBACK'] = "1"
else:
    os.environ['NO_LOGGING'] = "1"

try:
    from richcolorlog import setup_logging, print_exception as tprint  # type: ignore
    setup_logging(exceptions = exceptions)
    logger = setup_logging(__name__, level=LOG_LEVEL, exceptions=exceptions)  # type: ignore
except:
    import logging
    logging.basicConfig(  # type: ignore
        level=logging.DEBUG,  # type: ignore
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    if exceptions:
        for exc in exceptions:
            logger.getLoger(exc).setLevel(logging.CRITICAL)

if not tprint:
    def tprint(*args, **kwargs):
        traceback.print_exc(*args, **kwargs)

import argparse
import subprocess
from pathlib import Path
from jsoncolor import jprint
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.syntax import Syntax
from rich_argparse import RichHelpFormatter, _lazy_rich as rr
from typing import ClassVar, Dict, List, Optional, Union, Tuple
from rich import traceback as rich_traceback
from rich.panel import Panel
from rich.table import Table
from rich.markup import escape
from rich.style import Style
# import shutil
# from pydebugger.debug import debug
import pyperclip

from pygments.lexers import PythonLexer
# from pygments.token import Token
from pygments import lex
from pygments.styles import get_style_by_name

# Configure rich traceback
rich_traceback.install(theme='fruity', max_frames=30, width=os.get_terminal_size()[0], show_locals = False)

console = Console()
start_time = time.time()

def highlight_line(line: str, theme: str = "fruity") -> Text:
    """Return a Rich Text object with Pygments highlighting applied to a line (safe: no markup parsing)."""
    pygments_style = get_style_by_name(theme)
    text = Text(no_wrap=True, overflow="ignore")

    for token, value in lex(line, PythonLexer()):
        if not value:
            continue

        pyg_style = pygments_style.style_for_token(token)

        # normalize hex color
        def fix(color):
            if color and not color.startswith("#"):
                return f"#{color}"
            return color

        color = fix(pyg_style['color'])
        bgcolor = fix(pyg_style['bgcolor'])

        rich_style = Style(
            color=color,
            bgcolor=bgcolor,
            bold=pyg_style.get("bold", False),
            italic=pyg_style.get("italic", False),
        )

        # append *verbatim*, tidak pernah diparse sebagai markup
        text.append(value, style=rich_style)

    return text

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


class DuplicateInfo:
    """Information about duplicate methods/functions."""
    
    def __init__(self, name: str):
        self.name = name
        self.occurrences: List[CodeElement] = []
        
    def add_occurrence(self, element: CodeElement):
        """Add an occurrence of this duplicate."""
        self.occurrences.append(element)
        
    @property
    def count(self) -> int:
        """Get the number of occurrences."""
        return len(self.occurrences)
        
    @property
    def is_duplicate(self) -> bool:
        """Check if this is actually a duplicate (more than 1 occurrence)."""
        return self.count > 1


class EnhancedCodeVisitor(ast.NodeVisitor):
    """Enhanced visitor that collects all classes and functions with better organization."""
    
    def __init__(self):
        self.classes: Dict[str, List[str]] = {}
        self.functions: Dict[str, List[CodeElement]] = {}
        self.current_class: Optional[str] = None
        self.all_elements: List[CodeElement] = []  # Track all elements for duplicate detection
        
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
                
                element = CodeElement(child, node.name)
                self.functions[node.name].append(element)
                self.all_elements.append(element)  # Track for duplicates
        
        self.current_class = None
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit standalone function definition."""
        if self.current_class is None:  # Only standalone functions
            if 'standalone' not in self.functions:
                self.functions['standalone'] = []
            
            element = CodeElement(node)
            self.functions['standalone'].append(element)
            self.all_elements.append(element)  # Track for duplicates
    
    def find_duplicates(self) -> Dict[str, DuplicateInfo]:
        """Find all duplicate method/function names."""
        name_tracker: Dict[str, DuplicateInfo] = {}
        
        for element in self.all_elements:
            # Use full name for methods, simple name for standalone functions
            key = element.full_name if element.class_name else element.name
            
            if key not in name_tracker:
                name_tracker[key] = DuplicateInfo(key)
            
            name_tracker[key].add_occurrence(element)
        
        # Return only actual duplicates
        return {k: v for k, v in name_tracker.items() if v.is_duplicate}


class GitChangeTracker:
    """Git integration for tracking file changes."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.is_git_repo = False
        self.git_root = None
        self.changes: Dict[int, str] = {}  # line_number -> change_type ('+', '-', '~')
        
        self._detect_git_repo()
        if self.is_git_repo:
            self._analyze_changes()
    
    def _detect_git_repo(self) -> None:
        """Detect if the file is in a Git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=os.path.dirname(os.path.abspath(self.filename)) or '.',
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.is_git_repo = True
                self.git_root = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.is_git_repo = False
    
    def _analyze_changes(self) -> None:
        """Analyze Git changes for the file."""
        if not self.is_git_repo:
            return
            
        try:
            # Get git diff with line numbers
            result = subprocess.run([
                'git', 'diff', '--no-index', '--no-prefix', '-U0',
                '/dev/null' if not self._file_in_git() else f'{self.filename}',
                self.filename
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode not in [0, 1]:  # 0 = no diff, 1 = has diff
                # Try alternative: compare with HEAD
                result = subprocess.run([
                    'git', 'diff', 'HEAD', '--no-prefix', '-U0', self.filename
                ], capture_output=True, text=True, timeout=10)
            
            if result.stdout:
                self._parse_diff(result.stdout)
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # Fallback: check git status for basic info
            try:
                status_result = subprocess.run([
                    'git', 'status', '--porcelain', self.filename
                ], capture_output=True, text=True, timeout=5)
                
                if status_result.stdout.strip():
                    # File has changes, mark all lines as modified
                    self._mark_all_modified()
            except:
                pass
    
    def _file_in_git(self) -> bool:
        """Check if file is tracked by Git."""
        try:
            result = subprocess.run([
                'git', 'ls-files', '--error-unmatch', self.filename
            ], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _parse_diff(self, diff_output: str) -> None:
        """Parse git diff output to identify changed lines."""
        lines = diff_output.split('\n')
        current_line = 0
        
        for line in lines:
            if line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                parts = line.split(' ')
                if len(parts) >= 3:
                    try:
                        new_info = parts[2].lstrip('+')
                        if ',' in new_info:
                            current_line = int(new_info.split(',')[0])
                        else:
                            current_line = int(new_info)
                    except (ValueError, IndexError):
                        continue
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                self.changes[current_line] = '+'
                current_line += 1
            elif line.startswith('-') and not line.startswith('---'):
                # Deleted line (we'll mark the next line as modified)
                if current_line > 0:
                    self.changes[current_line] = '~'
            elif line.startswith(' '):
                # Unchanged line
                current_line += 1
    
    def _mark_all_modified(self) -> None:
        """Mark all lines as modified when we can't get detailed diff."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            for i in range(1, line_count + 1):
                self.changes[i] = '~'
        except:
            pass
    
    def get_change_indicator1(self, line_number: int) -> str:
        """Get change indicator for a specific line."""
        change_type = self.changes.get(line_number, '')
        
        if change_type == '+':
            return '[bold green]+[/]'
        elif change_type == '-':
            return '[bold red]-[/]'
        elif change_type == '~':
            return '[bold yellow]~[/]'
        else:
            return ' '

    def get_change_indicator(self, line_number: int) -> Text:
        """Get change indicator for a specific line."""
        change_type = self.changes.get(line_number, '')

        if change_type == '+':
            return Text("+", style="bold green")
        elif change_type == '-':
            return Text("-", style="bold red")
        elif change_type == '~':
            return Text("~", style="bold yellow")
        else:
            return Text(" ")
    
    def has_changes(self) -> bool:
        """Check if file has any changes."""
        return bool(self.changes)
    
    def get_change_summary(self) -> Tuple[int, int, int]:
        """Get summary of changes (added, deleted, modified)."""
        added = sum(1 for c in self.changes.values() if c == '+')
        deleted = sum(1 for c in self.changes.values() if c == '-')
        modified = sum(1 for c in self.changes.values() if c == '~')
        return added, deleted, modified


class CodeAnalyzer:
    """Main class for analyzing Python code structure."""
    
    def __init__(self, filename: Optional[str] = None):
        self.source_data: Optional[str] = None
        self.tree_data: Optional[ast.AST] = None
        self.filename = filename
        self.duplicates_cache: Optional[Dict[str, DuplicateInfo]] = None
        self.git_tracker: Optional[GitChangeTracker] = None
        
        if filename and os.path.isfile(filename):
            self._load_file(filename)
    
    def _load_file(self, filename: str) -> None:
        """Load and parse a Python file."""
        try:
            with open(filename, "r", encoding='utf-8') as file:
                self.source_data = file.read()
                self.tree_data = ast.parse(self.source_data)
                self.filename = filename
                self.duplicates_cache = None  # Reset cache when loading new file
                self.git_tracker = GitChangeTracker(filename)  # Initialize Git tracking
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
    
    def find_duplicates(self) -> Dict[str, DuplicateInfo]:
        """Find all duplicate methods/functions in the code."""
        if not self.tree_data:
            return {}
        
        # Use cache if available
        if self.duplicates_cache is not None:
            return self.duplicates_cache
            
        visitor = EnhancedCodeVisitor()
        visitor.visit(self.tree_data)
        
        self.duplicates_cache = visitor.find_duplicates()
        return self.duplicates_cache
    
    def print_duplicate_warnings(self) -> None:
        """Print warnings for duplicate methods/functions."""
        duplicates = self.find_duplicates()
        
        if not duplicates:
            return
        
        # Create warning panel
        warning_content = []
        for name, duplicate_info in duplicates.items():
            locations = []
            for occurrence in duplicate_info.occurrences:
                if occurrence.class_name:
                    locations.append(f"Line [bold #00FFFF]{occurrence.lineno}[/] ([bold #AAAAFF]in class[/] [bold #FFFF00]{occurrence.class_name}[/])")
                else:
                    locations.append(f"Line [bold #00FFFF]{occurrence.lineno}[/] ([bold #FFFF00]standalone[/])")
            
            warning_content.append(f"• [white on #AA0000]{name}[/] found {duplicate_info.count} times:")
            for location in locations:
                warning_content.append(f"  └─ {location}")
        
        panel = Panel(
            "\n".join(warning_content),
            title="⚠ [white on red]DUPLICATE METHODS/FUNCTIONS DETECTED[/]",
            border_style="bold #FF00FF",
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print()
    
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
    
    def print_structure(self, highlight = None, short_mode: Optional[bool] = False) -> None:
        """Print the code structure as a beautiful tree."""
        structure = self.get_structure()
        if not structure:
            console.print("[yellow]⚠️  No classes or functions found[/]")
            return
            
        filename_display = self.filename or "Code Structure"
        git_indicator = " [dim]📝 (Git changes detected)[/]" if (self.git_tracker and self.git_tracker.has_changes()) else ""
        
        root = Tree(
            f"🌳 [bold #00FF88]Python Code Analysis[/] [dim]│[/] [bold #55FFFF]{filename_display}[/]{git_indicator}",
            guide_style="bold #00AAFF"
        )
        
        for container_name, items in structure.items():
            if container_name == '📄 Standalone Functions':
                container_tree = root.add(f"📄 [bold #FF55FF]Standalone Functions[/]")
                icon = "🔧"
            else:
                if highlight and container_name.lower() == highlight.lower():
                    container_tree = root.add(f"🏛️ [bold italic white on red]{container_name}[/]")
                else:
                    container_tree = root.add(f"🏛️ [bold italic #FFFFFF on #0000FF]{container_name}[/]")
                icon = "⚙️"
            
            data_lower = [i.lower() for i in items]
            logger.debug(f"data_lower: {data_lower}")
            logger.debug(f"len(data_lower): {len(data_lower)}")
            # print(f"items: {items}")
            for item in items:
                standalone_color_highlight = "bold #FFFFFF on #AA00FF"
                common_color_highlight = "bold #000000 on #00FF00"
                
                if not short_mode:
                    if container_name == '📄 Standalone Functions':
                        if highlight and item.lower() == highlight.lower():
                            container_tree.add(f"{icon} [{standalone_color_highlight}]{item}[/]")
                        else:
                            container_tree.add(f"{icon} [bold #55FFFF]{item}[/]")
                    else:
                        if highlight and item.lower() == highlight.lower():
                            container_tree.add(f"{icon} [{common_color_highlight}]{item}[/]")
                        else:
                            container_tree.add(f"{icon} [bold #FFD700]{item}[/]")
                else:
                    logger.debug(f"highlight: {highlight}")
                    
                    if highlight and highlight.lower() in data_lower and item.lower() == data_lower[data_lower.index(highlight.lower()) - 1] and not item.lower() == highlight.lower():
                        container_tree.add(f"{icon} [bold #AAAA00].[/]")
                        container_tree.add(f"{icon} [bold #AAAA00].[/]")
                    elif highlight and highlight.lower() in data_lower and item.lower() == data_lower[data_lower.index(highlight.lower()) + 1 if len(data_lower) > 1 and not data_lower.index(highlight.lower()) == len(data_lower) - 1 else 0] and not item.lower() == highlight.lower():
                        container_tree.add(f"{icon} [bold #AAAA00].[/]")
                        container_tree.add(f"{icon} [bold #AAAA00].[/]")
                    else:
                        if container_name == '📄 Standalone Functions':
                            if highlight and item.lower() == highlight.lower():
                                container_tree.add(f"{icon} [{standalone_color_highlight}]{item}[/]")
                            else:
                                if not short_mode:
                                    container_tree.add(f"{icon} [bold #55FFFF]{item}[/]")
                        else:
                            if highlight and item.lower() == highlight.lower():
                                container_tree.add(f"{icon} [{common_color_highlight}]{item}[/]")
                            else:
                                if not short_mode:
                                    container_tree.add(f"{icon} [bold #FFD700]{item}[/]")

        
        console.print(root)

        print()
        # Print Git changes summary if available
        if self.git_tracker and self.git_tracker.has_changes():
            self._print_git_summary()
        
        # Print duplicate warnings first
        self.print_duplicate_warnings()
        
    def _print_git_summary(self) -> None:
        """Print Git changes summary."""
        if not self.git_tracker or not self.git_tracker.has_changes():
            return
            
        added, deleted, modified = self.git_tracker.get_change_summary()
        
        git_table = Table(
            title=" 📝 [bold cyan]Git Changes Summary[/]",
            border_style="cyan",
            show_header=False,
            box=None,
            padding=(0, 1),
            title_justify='left'
        )
        git_table.add_column("", style="bold", min_width=8)
        git_table.add_column("", style="", min_width=15)
        
        if added > 0:
            git_table.add_row("[bold #00FFFF]+[/]", f"[green]{added} lines added[/]")
        if deleted > 0:
            git_table.add_row("[red]-[/]", f"[red]{deleted} lines deleted[/]")
        if modified > 0:
            git_table.add_row("[bold #FFFF00]~[/]", f"[yellow]{modified} lines modified[/]")
        
        console.print(git_table)
        console.print()
    
    def display_code(self, element: CodeElement, theme: str = 'fruity', show_git_changes: bool = True) -> None:
        """Display code with syntax highlighting and copy to clipboard."""
        code = self.extract_code(element)
        
        if not code:
            console.print(f"[red]❌ Could not extract code for {element.full_name}[/]")
            return
        
        # Header with icon and styling
        if element.class_name:
            header = f"🏛️ [black on #00FF88]Class Method[/] [italic #FFFF00 on #4400CC]'{element.full_name}'[/]"
        else:
            header = f"🔧 [black on #00FF88]Function[/] [italic #FFFF00 on #4400CC]'{element.name}'[/]"
            
        # Add line number info
        header += f" [dim]│[/] [bold #55FFFF]Lines {element.start_line + 1}-{element.end_lineno}[/]"
        
        # Add Git change info if available
        if show_git_changes and self.git_tracker and self.git_tracker.has_changes():
            changes_in_range = []
            for line_num in range(element.start_line + 1, element.end_lineno + 1):
                if line_num in self.git_tracker.changes:
                    changes_in_range.append(self.git_tracker.changes[line_num])
            
            if changes_in_range:
                change_counts = {}
                for change in changes_in_range:
                    change_counts[change] = change_counts.get(change, 0) + 1
                
                change_info = []
                if '+' in change_counts:
                    change_info.append(f"[green]+{change_counts['+']}[/]")
                if '-' in change_counts:
                    change_info.append(f"[red]-{change_counts['-']}[/]")
                if '~' in change_counts:
                    change_info.append(f"[yellow]~{change_counts['~']}[/]")
                
                if change_info:
                    header += f" [dim]│[/] [bold]Git:[/] {' '.join(change_info)}"
        
        console.print(f"\n{header}\n")
        
        # Display code with Git indicators
        if show_git_changes and self.git_tracker and self.git_tracker.has_changes():
            self._display_code_with_git_indicators(code, element.start_line + 1, theme)
        else:
            # Standard syntax highlighting
            syntax = Syntax(
                code, 
                'python', 
                theme=theme, 
                line_numbers=True, 
                tab_size=4, 
                word_wrap=True,
                code_width=os.get_terminal_size()[0] - 4,
                start_line=element.start_line + 1
            )
            console.print(syntax)
        
        # Copy to clipboard
        pyperclip.copy(code)
        console.print(f"[dim]📋 Code copied to clipboard[/]")
    
    def _display_code_with_git_indicators(self, code: str, start_line: int, theme: str) -> None:
        """Display code with Git change indicators."""
        lines = code.split('\n')
        console_width = os.get_terminal_size()[0]
        
        # Create a custom display with git indicators
        for i, line in enumerate(lines, start=start_line):
            line_num = str(i).rjust(4)
            git_indicator = self.git_tracker.get_change_indicator(i) if self.git_tracker else ' '
            
            # Create the formatted line
            formatted_line = f"[dim]{line_num}[/] {git_indicator} {line}"
            
            # Apply syntax highlighting to just the code part
            try:
                from pygments import highlight
                from pygments.lexers import PythonLexer
                from pygments.formatters import Terminal256Formatter
                
                # This is a simplified approach - in a full implementation,
                # you'd want to integrate this more deeply with Rich's Syntax class
                console.print(formatted_line)
            except:
                console.print(formatted_line)
    
    def display_multiple_elements(self, elements: List[CodeElement], theme: str = 'fruity', show_git_changes: bool = True) -> None:
        """Display multiple code elements with duplicate warnings."""
        if len(elements) > 1:
            # Show duplicate warning
            warning_table = Table(
                title="⚠️ [bold red]MULTIPLE MATCHES FOUND[/]",
                border_style="red",
                show_header=True,
                header_style="bold white on red"
            )
            warning_table.add_column("Match", style="bold yellow")
            warning_table.add_column("Location", style="cyan")
            warning_table.add_column("Lines", style="magenta")
            
            if show_git_changes and self.git_tracker and self.git_tracker.has_changes():
                warning_table.add_column("Git Changes", style="white")
            
            for i, element in enumerate(elements, 1):
                location = f"Class: {element.class_name}" if element.class_name else "Standalone"
                lines = f"{element.start_line + 1}-{element.end_lineno}"
                
                row_data = [f"#{i}", location, lines]
                
                # Add Git change info if available
                if show_git_changes and self.git_tracker and self.git_tracker.has_changes():
                    changes_in_range = []
                    for line_num in range(element.start_line + 1, element.end_lineno + 1):
                        if line_num in self.git_tracker.changes:
                            changes_in_range.append(self.git_tracker.changes[line_num])
                    
                    if changes_in_range:
                        change_counts = {}
                        for change in changes_in_range:
                            change_counts[change] = change_counts.get(change, 0) + 1
                        
                        change_parts = []
                        if '+' in change_counts:
                            change_parts.append(f"[green]+{change_counts['+']}[/]")
                        if '-' in change_counts:
                            change_parts.append(f"[red]-{change_counts['-']}[/]")
                        if '~' in change_counts:
                            change_parts.append(f"[yellow]~{change_counts['~']}[/]")
                        
                        row_data.append(' '.join(change_parts) if change_parts else "No changes")
                    else:
                        row_data.append("No changes")
                
                warning_table.add_row(*row_data)
            
            console.print(warning_table)
            console.print()
        
        # Display all elements
        for i, element in enumerate(elements, 1):
            if len(elements) > 1:
                console.print(f"[bold #FF6B35]═══ Match #{i} ═══[/]")
            self.display_code(element, theme, show_git_changes)
            if i < len(elements):
                console.print("\n" + "─" * 50 + "\n")
    
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
        description="🚀 Advanced Python Code Analyzer with Rich Display",
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
    parser.add_argument(
        '-d', '--duplicates',
        help='Show only duplicate method/function analysis',
        action='store_true'
    )
    
    parser.add_argument(
        '-L', '--lines',
        help='Show specific line or range of lines (e.g. -L 20 or -L 20 30)',
        nargs='+',
        type=int,
        metavar=('START', 'END')
    )

    parser.add_argument(
        '-nl', '--no-linenumber',
        help="Don't show line numbers",
        action='store_true'
    )

    parser.add_argument(
        '-S', '--strip',
        help="No padding at start of lines",
        action='store_true'
    )

    parser.add_argument(
        '-z', '--show',
        help="Keep show tree structure",
        action='store_true'
    )
    
    parser.add_argument(
        '--no-git',
        help="Disable Git change detection even in Git repositories",
        action='store_true'
    )
    
    parser.add_argument(
        '-e', '--emoji-detector',
        help="Detect emojis/icons in file",
        action='store_true'
    )

    parser.add_argument(
        '--clean',
        help="Remove/clean emojis/icons from files (modifies files in-place)",
        action='store_true'
    )

    parser.add_argument(
        '--dry-run',
        help="Show what would be cleaned without modifying files, test before run",
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

    if args.emoji_detector:
        if args.dry_run and not args.clean:
            args.clean = False  # Treat dry-run as detection mode

        try:
            from . emoji_detector import EmojiDetector
            detector = EmojiDetector(clean_mode=args.clean and not args.dry_run)
        except:
            try:
                from emoji_detector import EmojiDetector
                detector = EmojiDetector(clean_mode=args.clean and not args.dry_run)
            except:
                print("Can't run emoji_detector !, please check the script for args.emoji_detector !")
                sys.exit(0)

        if args.FILE:
            if args.FILE == 'c':
                args.FILE = clipboard.paste()
        
            if args.dry_run:
                detector.formatter.print_colored(
                    "ℹ️  Dry-run mode: No files will be modified",
                    'cyan',
                    bold=True
                )

            if args.clean and not args.dry_run:
                detector.formatter.print_colored(
                    "⚠️  WARNING: Clean mode will modify files in-place!",
                    'yellow',
                    bold=True
                )
                response = input("Continue? (y/N): ").strip().lower()
                if response != 'y':
                    detector.formatter.print_colored("Operation cancelled.", 'yellow')
                    sys.exit(0)
        
            if not os.path.exists(args.FILE):
                detector.formatter.print_colored(f"Error: Path '{args.FILE}' does not exist!", 'red', bold=True)
                sys.exit(1)
            
            if os.path.isfile(args.FILE):
                count = detector.scan_file(args.FILE)
                if count == 0:
                    detector.formatter.print_colored("No emojis found in file.", 'yellow')
            elif os.path.isdir(args.FILE):
                detector.scan_directory(args.FILE, '*', False)
            else:
                detector.formatter.print_colored(f"Error: '{args.FILE}' is not a file or directory!", 'red')
                sys.exit(1)

        sys.exit(0)
    
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
                
                # Handle duplicate analysis only
                if args.duplicates:
                    duplicates = analyzer.find_duplicates()
                    if duplicates:
                        analyzer.print_duplicate_warnings()
                        
                        # Show detailed duplicate table
                        detail_table = Table(
                            title="🔍 [bold cyan]DETAILED DUPLICATE ANALYSIS[/]",
                            border_style="cyan",
                            show_header=True,
                            header_style="bold white on cyan"
                        )
                        detail_table.add_column("Method/Function", style="bold yellow")
                        detail_table.add_column("Count", justify="center", style="bold red")
                        detail_table.add_column("Locations", style="white")
                        
                        for name, duplicate_info in duplicates.items():
                            locations = []
                            for occurrence in duplicate_info.occurrences:
                                if occurrence.class_name:
                                    locations.append(f"Line {occurrence.lineno} (class {occurrence.class_name})")
                                else:
                                    locations.append(f"Line {occurrence.lineno} (standalone)")
                            
                            detail_table.add_row(
                                name,
                                str(duplicate_info.count),
                                "\n".join(locations)
                            )
                        
                        console.print(detail_table)
                    else:
                        console.print("[bold green]✅ No duplicate methods/functions found![/]")
                    return
                
                # Handle line range
                if args.lines:
                    try:
                        with open(args.FILE, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        total_lines = len(lines)

                        if len(args.lines) == 1:
                            start = end = args.lines[0]
                        else:
                            start, end = args.lines[0], args.lines[1]

                        # Clamp values to valid range
                        start = max(1, start)
                        end = max(start, min(total_lines, end))

                        if start > total_lines:
                            console.print(f"[red]❌ Start line {start} exceeds total lines ({total_lines})[/]")
                            return

                        selected = lines[start - 1:end]

                        if not ''.join(selected).strip():
                            console.print(f"[yellow]⚠️ No visible code found on lines {start}-{end}[/]")
                            return

                        console.print(f"[bold #00FF88]📄 Lines {start}-{end} from:[/] [bold #55FFFF]{args.FILE}[/]\n")

                        # Add manual numbering
                        numbered_code = ""
                        for i, line in enumerate(selected, start=start):
                            numbered_code += f"{str(i).rjust(4) + ' | ' if not args.no_linenumber else '   ' if not args.strip else ''}{line}"

                        syntax = Syntax(numbered_code, 'python', theme=args.style, line_numbers=False)
                        console.print(syntax)
                        return

                    except Exception as e:
                        console.print(f"[red]❌ Error reading lines {args.lines} from file: {e}[/]")
                        return

                if args.method:
                    # Handle specific method/function
                    class_name = None
                    method_name = args.method
                    
                    if '.' in args.method:
                        class_name, method_name = args.method.split('.', 1)
                    
                    elements = analyzer.find_code_elements(method_name, class_name)
                    
                    if elements:
                        analyzer.display_multiple_elements(elements, args.style, not args.no_git)
                    else:
                        if class_name:
                            console.print(f"[red]❌ Method '{method_name}' not found in class '{class_name}'[/]")
                        else:
                            console.print(f"[red]❌ Function/method '{method_name}' not found[/]")

                    if args.show:
                        print("\n")
                        analyzer.print_structure(args.method, True)
                
                elif args.code:
                    # Display entire file
                    with open(args.FILE, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    console.print(f"[bold #00FF88]📄 Complete Source Code:[/] [bold #55FFFF]{args.FILE}[/]")
                    
                    # Show Git summary if available
                    if not args.no_git and analyzer.git_tracker and analyzer.git_tracker.has_changes():
                        analyzer._print_git_summary()
                    
                    console.print()
                    
                    # Display with Git indicators if available
                    # if not args.no_git and analyzer.git_tracker and analyzer.git_tracker.has_changes():
                    #     lines = content.split('\n')
                    #     for i, line in enumerate(lines, 1):
                    #         git_indicator = analyzer.git_tracker.get_change_indicator(i)
                    #         line_num = str(i).rjust(4)
                    #         # console.print(f"[dim]{line_num} |[/] {git_indicator} {line}")
                    #         console.print(f"[dim]{line_num} |[/] {git_indicator} {escape(line)}")
                    if not args.no_git and analyzer.git_tracker and analyzer.git_tracker.has_changes():
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            git_indicator = analyzer.git_tracker.get_change_indicator(i)  # sekarang Text
                            line_num = str(i).rjust(4)

                            code_text = highlight_line(line, args.style)  # juga Text

                            # rakit semua jadi satu Text
                            # overflow (str, optional): Overflow method: "crop", "fold", "ellipsis". Defaults to None.
                            row = Text()
                            row.append(f"{line_num}", style="white on #AA55FF")
                            row.append(' │ ')
                            row.append_text(git_indicator)
                            row.append(" ")
                            row.append_text(code_text)

                            console.print(row, end="")  # ⬅️ end="" supaya tidak ada newline ekstra

                    else:
                        syntax = Syntax(content, 'python', theme=args.style, line_numbers=True)
                        console.print(syntax)
                
                else:
                    # Show structure (includes duplicate warnings)
                    analyzer.print_structure()
                    
            except Exception as e:
                # console.print(f"[red]❌ Error processing file: {e}[/]")
                console.print(f"❌ Unexpected error: {e}", style="red", markup=False)
                if os.getenv('TRACEBACK', '0').lower() in ['1', 'yes', 'true']:
                    console.print_exception()
       
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
        # console.print(f"[red]❌ Unexpected error: {e}[/]")
        console.print(f"❌ Unexpected error: {e}", style="red", markup=False)
        if os.getenv('TRACEBACK', '0').lower() in ['1', 'yes', 'true']:
            console.print_exception()
    finally:
        end_time = time.time()
        execution_time = end_time - start_time
        console.print(f"[dim]⏱️  Execution time: {execution_time:.3f}s[/]")