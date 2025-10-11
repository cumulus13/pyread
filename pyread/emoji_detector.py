#!/usr/bin/env python3
"""
Icon and Emoji Detector
Detects and displays icons/emojis in files with colored output
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Try to import rich, fallback to basic colors
try:
    from rich.console import Console
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ColorFormatter:
    """Handles colored output with rich or fallback ANSI colors"""
    
    def __init__(self):
        if RICH_AVAILABLE:
            self.console = Console()
            self.use_rich = True
        else:
            self.use_rich = False
            # ANSI color codes
            self.colors = {
                'red': '\033[91m',
                'green': '\033[92m',
                'yellow': '\033[93m',
                'blue': '\033[94m',
                'magenta': '\033[95m',
                'cyan': '\033[96m',
                'white': '\033[97m',
                'reset': '\033[0m',
                'bold': '\033[1m',
            }
    
    def print_colored(self, text: str, color: str = 'white', bold: bool = False):
        """Print colored text using rich or ANSI codes"""
        if self.use_rich:
            style = color
            if bold:
                style = f"bold {color}"
            self.console.print(text, style=style)
        else:
            prefix = self.colors.get('bold', '') if bold else ''
            color_code = self.colors.get(color, '')
            reset = self.colors.get('reset', '')
            print(f"{prefix}{color_code}{text}{reset}")
    
    def print_line(self, filename: str, line_num: int, line: str, emoji_positions: List[Tuple[int, str]]):
        """Print a formatted line with highlighted emojis"""
        if self.use_rich:
            self._print_line_rich(filename, line_num, line, emoji_positions)
        else:
            self._print_line_ansi(filename, line_num, line, emoji_positions)
    
    def _print_line_rich(self, filename: str, line_num: int, line: str, emoji_positions: List[Tuple[int, str]]):
        """Print using rich library"""
        text = Text()
        text.append(f"{filename}:", style="cyan bold")
        text.append(f"{line_num}:", style="yellow bold")
        text.append(" ")
        
        last_pos = 0
        for pos, emoji in emoji_positions:
            text.append(line[last_pos:pos], style="white")
            text.append(emoji, style="magenta bold")
            last_pos = pos + len(emoji)
        text.append(line[last_pos:], style="white")
        
        self.console.print(text)
    
    def _print_line_ansi(self, filename: str, line_num: int, line: str, emoji_positions: List[Tuple[int, str]]):
        """Print using ANSI color codes"""
        cyan_bold = f"{self.colors['bold']}{self.colors['cyan']}"
        yellow_bold = f"{self.colors['bold']}{self.colors['yellow']}"
        magenta_bold = f"{self.colors['bold']}{self.colors['magenta']}"
        reset = self.colors['reset']
        
        output = f"{cyan_bold}{filename}:{reset}{yellow_bold}{line_num}:{reset} "
        
        last_pos = 0
        for pos, emoji in emoji_positions:
            output += line[last_pos:pos]
            output += f"{magenta_bold}{emoji}{reset}"
            last_pos = pos + len(emoji)
        output += line[last_pos:]
        
        print(output)


class EmojiDetector:
    """Detects icons and emojis in text files"""
    
    # Excluded characters (box drawing, arrows, etc.)
    EXCLUDED_CHARS = set(range(0x2500, 0x257F))  # Box Drawing
    EXCLUDED_CHARS.update(range(0x2580, 0x259F))  # Block Elements
    EXCLUDED_CHARS.update(range(0x25A0, 0x25FF))  # Geometric Shapes (basic)
    EXCLUDED_CHARS.update(range(0x2190, 0x21FF))  # Arrows
    
    # Unicode ranges for emojis and icons
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats (selective)
        "\U0001F004"              # Mahjong Tiles
        "\U0001F0CF"              # Playing Cards
        "\U0001F170-\U0001F251"  # Enclosed Alphanumeric Supplement
        "\U00002600-\U000026FF"  # Miscellaneous Symbols (weather, zodiac, etc.)
        "\U00002B50"              # Star
        "\U0000231A-\U0000231B"  # Watch and Hourglass
        "\U000023E9-\U000023F3"  # Playback symbols
        "\U000023F8-\U000023FA"  # More playback symbols
        "\U0001F191-\U0001F19A"  # Regional indicator symbols
        "]+", 
        flags=re.UNICODE
    )
    
    @classmethod
    def is_excluded_char(cls, char: str) -> bool:
        """Check if character should be excluded from emoji detection"""
        return ord(char) in cls.EXCLUDED_CHARS
    
    def __init__(self, clean_mode: bool = False):
        self.formatter = ColorFormatter()
        self.total_files = 0
        self.total_lines = 0
        self.total_emojis = 0
        self.clean_mode = clean_mode
        self.cleaned_files = []
    
    def detect_emojis_in_line(self, line: str) -> List[Tuple[int, str]]:
        """Find all emojis in a line and return their positions"""
        matches = []
        for match in self.EMOJI_PATTERN.finditer(line):
            emoji = match.group()
            # Filter out excluded characters (box drawing, arrows, etc.)
            if not all(self.is_excluded_char(char) for char in emoji):
                matches.append((match.start(), emoji))
        return matches
    
    def clean_emojis_from_line(self, line: str) -> str:
        """Remove all emojis from a line"""
        return self.EMOJI_PATTERN.sub('', line)
    
    def scan_file(self, filepath: Path, encodings: List[str] = None) -> int:
        """Scan a file for emojis and print results, optionally clean them"""
        if encodings is None:
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        emoji_count = 0
        lines_with_emojis = []
        all_lines = []
        found_encoding = None
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    all_lines = []
                    for line_num, line in enumerate(f, 1):
                        original_line = line
                        line = line.rstrip('\n\r')
                        emoji_positions = self.detect_emojis_in_line(line)
                        
                        all_lines.append((original_line, line, emoji_positions))
                        
                        if emoji_positions:
                            lines_with_emojis.append(line_num)
                            if not self.clean_mode:
                                self.formatter.print_line(
                                    str(filepath), 
                                    line_num, 
                                    line, 
                                    emoji_positions
                                )
                            emoji_count += len(emoji_positions)
                            self.total_lines += 1
                
                found_encoding = encoding
                
                if emoji_count > 0:
                    self.total_files += 1
                    self.total_emojis += emoji_count
                    
                    # Clean mode: write cleaned file
                    if self.clean_mode:
                        self._clean_file(filepath, all_lines, found_encoding, lines_with_emojis)
                
                return emoji_count
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.formatter.print_colored(
                    f"Error reading {filepath}: {e}", 
                    'red'
                )
                return 0
        
        return 0
    
    def _clean_file(self, filepath: Path, lines_data: List, encoding: str, affected_lines: List[int]):
        """Write cleaned version of file without emojis"""
        try:
            cleaned_lines = []
            for original_line, stripped_line, emoji_positions in lines_data:
                if emoji_positions:
                    # Remove emojis but preserve line endings
                    cleaned = self.clean_emojis_from_line(stripped_line)
                    # Restore original line ending
                    if original_line.endswith('\r\n'):
                        cleaned += '\r\n'
                    elif original_line.endswith('\n'):
                        cleaned += '\n'
                    elif original_line.endswith('\r'):
                        cleaned += '\r'
                    cleaned_lines.append(cleaned)
                else:
                    cleaned_lines.append(original_line)
            
            # Write cleaned content
            with open(filepath, 'w', encoding=encoding) as f:
                f.writelines(cleaned_lines)
            
            self.cleaned_files.append((str(filepath), len(affected_lines)))
            self.formatter.print_colored(
                f"✓ Cleaned {filepath} ({len(affected_lines)} lines affected)",
                'green'
            )
            
        except Exception as e:
            self.formatter.print_colored(
                f"Error cleaning {filepath}: {e}",
                'red'
            )
    
    def scan_directory(self, directory: Path, pattern: str = '*', recursive: bool = True):
        """Scan directory for files containing emojis"""
        mode_text = "Cleaning" if self.clean_mode else "Scanning"
        self.formatter.print_colored(
            f"\n🔍 {mode_text}: {directory}", 
            'green', 
            bold=True
        )
        
        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)
        
        files = [f for f in files if f.is_file()]
        
        if not files:
            self.formatter.print_colored("No files found!", 'yellow')
            return
        
        for filepath in files:
            self.scan_file(filepath)
        
        self._print_summary()
    
    def _print_summary(self):
        """Print summary statistics"""
        self.formatter.print_colored("\n" + "="*60, 'cyan')
        self.formatter.print_colored("📊 Summary:", 'cyan', bold=True)
        self.formatter.print_colored(f"  Files with emojis: {self.total_files}", 'white')
        self.formatter.print_colored(f"  Lines with emojis: {self.total_lines}", 'white')
        self.formatter.print_colored(f"  Total emojis found: {self.total_emojis}", 'white')
        
        if self.clean_mode and self.cleaned_files:
            self.formatter.print_colored("\n  Cleaned files:", 'green', bold=True)
            for filepath, line_count in self.cleaned_files:
                self.formatter.print_colored(f"    • {filepath} ({line_count} lines)", 'white')
        
        self.formatter.print_colored("="*60, 'cyan')


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Detect icons and emojis in files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='File or directory path (default: current directory)'
    )
    parser.add_argument(
        '-p', '--pattern',
        default='*',
        help='File pattern to match (default: *)'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=True,
        help='Scan directories recursively (default: True)'
    )
    parser.add_argument(
        '--no-recursive',
        dest='recursive',
        action='store_false',
        help='Do not scan directories recursively'
    )
    parser.add_argument(
        '-c', '--clean',
        action='store_true',
        help='Remove/clean emojis from files (modifies files in-place)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned without modifying files'
    )
    
    args = parser.parse_args()
    path = Path(args.path)
    
    # Handle dry-run mode
    if args.dry_run and not args.clean:
        args.clean = False  # Treat dry-run as detection mode
    
    detector = EmojiDetector(clean_mode=args.clean and not args.dry_run)
    
    if not path.exists():
        detector.formatter.print_colored(f"Error: Path '{path}' does not exist!", 'red', bold=True)
        sys.exit(1)
    
    # Warn user about clean mode
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
    
    if args.dry_run:
        detector.formatter.print_colored(
            "ℹ️  Dry-run mode: No files will be modified",
            'cyan',
            bold=True
        )
    
    if path.is_file():
        count = detector.scan_file(path)
        if count == 0:
            detector.formatter.print_colored("No emojis found in file.", 'yellow')
    elif path.is_dir():
        detector.scan_directory(path, args.pattern, args.recursive)
    else:
        detector.formatter.print_colored(f"Error: '{path}' is not a file or directory!", 'red')
        sys.exit(1)


if __name__ == "__main__":
    main()