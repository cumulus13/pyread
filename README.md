# 🚀 Advanced Python Code Analyzer

A powerful, feature-rich Python code analyzer with beautiful syntax highlighting, duplicate detection, Git integration, and interactive capabilities. Built with Rich library for stunning terminal output.

## ✨ Features

### 🔍 Code Analysis
- **AST-based parsing** for accurate code structure analysis
- **Class and method discovery** with hierarchical display
- **Duplicate method detection** with comprehensive warnings
- **Line-specific code extraction** with precise range support
- **Interactive clipboard integration** for quick code analysis

### 📝 Git Integration
- **Automatic Git repository detection** for change tracking
- **Visual change indicators** (`+` added, `-` deleted, `~` modified)
- **Git diff analysis** with line-by-line change display
- **Change summary statistics** for quick overview
- **Smart fallback handling** when Git is unavailable

### 🎨 Beautiful Display
- **Rich syntax highlighting** with 50+ themes
- **Tree-structured output** for code organization
- **Color-coded warnings** for duplicate methods
- **Professional formatting** with icons and styling
- **Terminal-optimized** responsive design
- **Git change visualization** integrated into all views

### 🛠️ Interactive Features
- **Copy-to-clipboard** functionality for extracted code
- **Interactive save mode** with directory creation
- **Multiple output formats** (structure, code, lines, duplicates)
- **Theme preview** with complete theme listing
- **Error handling** with helpful messages

## 📦 Installation

### Prerequisites
```bash
pip install rich rich-argparse pygments pyperclip ast jedi jsoncolor pydebugger
```

### Quick Start
```bash
# install with pip
pip install git+https://github.com/cumulus13/pyread

# Or clone this repo
git clone https://github.com/cumulus13/pyread
cd pyread
pip install -e .

# then run
read --help
# or
pyread --help

# Or Clone or download the read.py file
python read.py --help
```

## 🚀 Usage

### Basic Commands

#### Display Code Structure with Git Changes
```bash
# Show complete code structure with duplicate warnings and Git changes
python read.py myfile.py

# Example output:
📝 Git Changes Summary
+ 5 lines added
- 2 lines deleted
~ 8 lines modified

🌳 Python Code Analysis │ myfile.py 📝 (Git changes detected)
├── 🏛️ MyClass
│   ├── ⚙️ __init__
│   ├── ⚙️ process_data
│   └── ⚙️ save_result
└── 📄 Standalone Functions
    ├── 🔧 main
    └── 🔧 helper_function
```

#### Extract Specific Methods with Git Info
```bash
# Extract specific method or function with Git change indicators
python read.py myfile.py -m method_name

# Extract class method with Git changes
python read.py myfile.py -m ClassName.method_name

# Example output with Git changes:
🏛️ Class Method 'MyClass.process_data' │ Lines 15-25 │ Git: +2 ~3

   15 | + def process_data(self):
   16 |     """Process the data."""
   17 | ~     self.data = self.clean_data()
   18 |       return self.data
   19 | + 
   20 | +     # New validation step
```

#### Display Full File with Git Changes
```bash
# Show entire file with syntax highlighting and Git indicators
python read.py myfile.py -c

# Use different theme with Git changes
python read.py myfile.py -c -s monokai

# Disable Git integration
python read.py myfile.py -c --no-git
```

### Advanced Features

#### 📝 Git Integration Features

#### Git Change Detection
```bash
# Automatic Git repository detection and change tracking
python read.py myfile.py

# Disable Git integration if not needed
python read.py myfile.py --no-git

# View Git changes in different contexts
python read.py myfile.py -m method_name    # Method-level changes
python read.py myfile.py -L 10 20          # Range-level changes
python read.py myfile.py -c                # File-level changes
```

#### Git Change Indicators
- **`[+]` Green** - Lines added since last commit
- **`[-]` Red** - Lines deleted (marked on surrounding lines)
- **`[~]` Yellow** - Lines modified since last commit
- **Git Summary** - Overview of total changes per file

#### Git Integration Examples
```bash
# Code structure with Git changes
🌳 Python Code Analysis │ myfile.py 📝 (Git changes detected)

# Method display with Git info
🏛️ Class Method 'process_data' │ Lines 15-25 │ Git: +3 ~2

# Line-by-line Git indicators
   23 | + def new_method(self):
   24 | ~     self.updated_code = True
   25 |       return self.result
```

#### Line Range Extraction with Git Changes
```bash
# Extract specific line with Git indicators
python read.py myfile.py -L 25

# Extract line range with Git changes
python read.py myfile.py -L 25 50

# Example output with Git changes:
📄 Lines 25-30 from: myfile.py
Git changes: +2 added, ~1 modified

   25 |   def __init__(self):
   26 | +     self.new_feature = True
   27 | ~     self.data = []
   28 |       self.status = "ready"

# Without line numbers but with Git indicators
python read.py myfile.py -L 25 50 -nl

# No padding, clean display
python read.py myfile.py -L 25 50 -S
```

#### Duplicate Detection
```bash
# Show only duplicate analysis
python read.py myfile.py -d

# Example output:
⚠️  DUPLICATE METHODS/FUNCTIONS DETECTED
• MyClass.process found 2 times:
  └─ Line 15 (in class MyClass)
  └─ Line 45 (in class AnotherClass)
• helper_function found 3 times:
  └─ Line 10 (standalone)
  └─ Line 35 (standalone)
  └─ Line 60 (standalone)
```

#### Clipboard Integration
```bash
# Analyze code from clipboard
python read.py c

# With different syntax type
python read.py c -t javascript

# Save clipboard content to file (interactive)
python read.py c
# Follow prompts to save
```

#### Theme Management
```bash
# List all available themes
python read.py -l

# Use specific theme
python read.py myfile.py -s dracula
python read.py myfile.py -s github-dark
```

## 📋 Command Line Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `FILE` | - | Python file to analyze or "c" for clipboard | `myfile.py` |
| `--method` | `-m` | Show specific method/function | `-m process_data` |
| `--style` | `-s` | Syntax highlighting theme | `-s monokai` |
| `--list-themes` | `-l` | List all available themes | `-l` |
| `--type` | `-t` | Code type for highlighting | `-t python` |
| `--code` | `-c` | Display entire source code | `-c` |
| `--duplicates` | `-d` | Show duplicate analysis only | `-d` |
| `--lines` | `-L` | Show specific line/range | `-L 10 20` |
| `--no-linenumber` | `-nl` | Don't show line numbers | `-nl` |
| `--strip` | `-S` | No padding at start of lines | `-S` |
| `--no-git` | - | Disable Git change detection | `--no-git` |

## 🔧 Advanced Usage Examples

### Git-Enhanced Code Review Workflow
```bash
# 1. Check for duplicates and Git changes first
python read.py myproject.py -d

# 2. Review overall structure with change indicators
python read.py myproject.py

# 3. Examine specific methods that have been modified
python read.py myproject.py -m modified_method

# 4. Extract specific sections for detailed review
python read.py myproject.py -L 100 150 -s github-dark

# 5. Disable Git if working with non-Git files
python read.py myproject.py --no-git
```

### Development Workflow with Git Integration
```bash
# Quick clipboard analysis during development
python read.py c

# Extract method with Git change tracking
python read.py myfile.py -m important_method

# Review specific lines after Git changes
python read.py myfile.py -L 45 55

# Full file review with Git indicators
python read.py myfile.py -c

# Debug mode with detailed error tracking
TRACEBACK=1 python read.py myfile.py
```

### Code Documentation
```bash
# Generate structure overview
python read.py mymodule.py > structure.txt

# Extract all methods from a class
python read.py myfile.py -m MyClass.method1
python read.py myfile.py -m MyClass.method2
```

## ⚠️ Duplicate Detection

The analyzer automatically detects and warns about:

### Types of Duplicates Detected
- **Method overrides** in different classes
- **Function redefinitions** in same file
- **Similar naming patterns** across classes
- **Accidental duplications** during development

### Warning Display
- **Visual warnings** with red panels
- **Line number references** for easy navigation
- **Context information** (class vs standalone)
- **Detailed analysis** with `-d` flag

### Example Duplicate Warning
```
⚠️  DUPLICATE METHODS/FUNCTIONS DETECTED

• DatabaseManager.connect found 2 times:
  └─ Line 23 (in class DatabaseManager)
  └─ Line 67 (in class BackupManager)

• validate_input found 3 times:
  └─ Line 12 (standalone)
  └─ Line 145 (standalone)
  └─ Line 203 (standalone)
```

## 🎨 Theme Gallery

### Popular Themes
- `fruity` - Colorful and vibrant (default)
- `monokai` - Dark theme with excellent contrast
- `github-dark` - GitHub's dark theme
- `dracula` - Popular dark theme
- `solarized-dark` - Easy on the eyes
- `nord` - Arctic, north-bluish color palette

### Light Themes
- `github-light` - GitHub's light theme
- `default` - Classic Python highlighting
- `colorful` - Bright and cheerful
- `friendly` - Soft and readable

## 📁 File Structure Support

### Supported File Types
- **Python files** (`.py`) - Full analysis
- **Any text files** - Syntax highlighting only
- **Clipboard content** - Real-time analysis

### Analysis Depth
- **Classes** and inheritance detection
- **Methods** and decorators
- **Functions** and parameters
- **Imports** and dependencies
- **Comments** and docstrings

## 🚨 Error Handling & Debugging

### Graceful Error Recovery
- **File not found** - Clear error messages with suggestions
- **Syntax errors** - Helpful parsing feedback with line numbers
- **Permission issues** - Alternative file access suggestions
- **Encoding problems** - UTF-8 fallback with warnings
- **Git command failures** - Graceful fallback to standard mode

### Debug Mode
```bash
# Enable detailed error tracking
TRACEBACK=1 python read.py myfile.py

# This will show full Python tracebacks for debugging
```

### User-Friendly Messages
```bash
❌ Error loading file myfile.py: [Errno 2] No such file or directory
⚠️  Clipboard is empty
✅ File saved successfully: output.py
📝 Git changes detected but Git command failed, continuing without Git integration
```

### Git Integration Error Handling
- **Git not installed** - Continues without Git features
- **Not a Git repository** - Standard analysis mode
- **Git command timeout** - Falls back to git status
- **Permission issues** - Disables Git integration gracefully

## 🔄 Interactive Features

### Save Mode
When using clipboard mode (`python read.py c`), you can:
1. **Analyze** clipboard content
2. **Choose theme** for display
3. **Save to file** interactively
4. **Create directories** if needed

### Interactive Prompts
```
💾 Save Mode │ Enter filename or 'q'/'exit' to quit
📝 output.py
✅ File saved successfully: output.py
```

## 🎯 Use Cases

### For Developers
- **Code review** with Git change tracking
- **Duplicate detection** before commits
- **Method extraction** for documentation
- **Structure visualization** for large files
- **Change impact analysis** during development

### For Code Auditors
- **Comprehensive analysis** of code organization
- **Duplicate identification** for refactoring opportunities
- **Structure comparison** across file versions
- **Quality metrics** and reporting with change tracking
- **Git history integration** for audit trails

### For Educators
- **Code structure** teaching aid with visual changes
- **Syntax highlighting** for presentations
- **Method isolation** for focused learning
- **Visual code** organization with Git integration
- **Change tracking** for student progress

## 📊 Performance

### Optimizations
- **AST caching** for repeated operations
- **Efficient parsing** with Python's ast module
- **Terminal detection** for responsive display
- **Memory management** for large files
- **Git command optimization** with timeouts and caching
- **Change tracking efficiency** with minimal Git calls

### Benchmarks
- **Small files** (<100 lines): ~0.001s
- **Medium files** (100-1000 lines): ~0.01s
- **Large files** (1000+ lines): ~0.1s
- **Git integration overhead**: +0.05-0.2s (depending on repository size)

## 🛡️ Requirements

### System Requirements
- **Git** (optional) - For change tracking features
- **Terminal** with Unicode support for best display
- **UTF-8** file encoding support

### Python Version
- **Python 3.7+** required
- **Python 3.9+** recommended for best performance

### Dependencies
```python
rich>=13.0.0          # Terminal formatting and display
rich-argparse>=1.0.0  # Enhanced argument parsing
pygments>=2.0.0       # Syntax highlighting engine
pyperclip>=1.8.0      # Clipboard operations
subprocess            # Git integration (built-in)
```

### Optional Dependencies
```python
jedi                   # Enhanced code analysis (if available)
pydebugger            # Additional debugging features (if available)
jsoncolor             # JSON syntax highlighting (if available)
```

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black read.py

# Type checking
mypy read.py
```

### Feature Requests
- Create detailed GitHub issues
- Provide example use cases
- Include sample code files

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Rich library** - For beautiful terminal output
- **Python AST** - For accurate code parsing
- **Pygments** - For syntax highlighting
- **Community** - For feedback and suggestions

## 📞 Support

### Getting Help
- Check the **examples** above
- Use `python read.py --help`
- Create **GitHub issues** for bugs
- Join discussions for feature requests

### Common Issues & Solutions
- **Module not found**: Install required dependencies with pip
- **Git not found**: Install Git or use `--no-git` flag
- **Encoding errors**: Ensure files use UTF-8 encoding
- **Permission denied**: Check file and directory permissions
- **Theme not found**: Use `-l` to list available themes
- **Git timeout**: Repository too large, will fallback automatically
- **Markup errors**: File may contain special characters, try different encoding

### Troubleshooting Git Integration
```bash
# If Git integration fails, disable it
python read.py myfile.py --no-git

# Check if file is in Git repository
git status myfile.py

# Enable debug mode for Git issues
TRACEBACK=1 python read.py myfile.py
```

### Performance Issues
- **Large files**: Use `-L` flag to analyze specific ranges
- **Slow Git operations**: Use `--no-git` for faster analysis
- **Memory issues**: Process files in smaller chunks

---

## author
[Hadi Cahyadi](mailto:cumulus13@gmail.com)
    

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)

[Support me on Patreon](https://www.patreon.com/cumulus13)

**Made with ❤️ for Python developers everywhere! 🐍✨**
