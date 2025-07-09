# PyRead #

Advanced Python Code Analyzer with Rich Display. Read source code from file or clipboard

usage
======
```bash:
Usage: read.py [-h] [-m NAME] [-s THEME] [-l] [-t TYPE] [-c] [-L START [END ...]] [-nl] [-S] [FILE]

🐍 Advanced Python Code Analyzer with Rich Display

Positional Arguments:
  FILE                  Python file to analyze, or "c" to read from clipboard

Options:
  -h, --help            show this help message and exit
  -m, --method NAME     Show specific method/function (use Class.method for class methods)
  -s, --style THEME     Syntax highlighting theme (default: fruity)
  -l, --list-themes     List all available syntax highlighting themes
  -t, --type TYPE       Code type for syntax highlighting (default: python)
  -c, --code            Display the entire source code with syntax highlighting
  -L, --lines START [END ...]
                        Show specific line or range of lines (e.g. -L 20 or -L 20 30)
  -nl, --no-linenumber  Don't show line numbers
  -S, --strip           No padding at start of lines
```

author
========
[cumulus13](mailto:cumulus13@gmail.com)
