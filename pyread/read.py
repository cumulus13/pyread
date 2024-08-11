import time
import ast
import sys, os
import jedi
import argparse
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.syntax import Syntax
from rich import traceback as rich_traceback
import shutil
from pydebugger.debug import debug
rich_traceback.install(theme = 'fruity', max_frames = 30, width = shutil.get_terminal_size()[0])

console = Console()

start_time = time.time()

class ClassMethodVisitor(ast.NodeVisitor):
    def __init__(self):
        self.class_methods = {}

    def visit_ClassDef(self, node):
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        self.class_methods[node.name] = methods
        self.generic_visit(node)

class FunctionVisitor(ast.NodeVisitor):
    def __init__(self, function_name):
        self.target_function = None
        self.function_name = function_name

    def visit_FunctionDef(self, node):
        if node.name == self.function_name:
            self.target_function = node
        # Continue to visit child nodes
        self.generic_visit(node)

class Read:
    
    def __init__(self, filename = None):
        self.tree_data = None
        self.source_data = None
        
        if filename and os.path.isfile(filename):
            with open(filename, "r") as file:
                self.source_data = file.read()
                self.tree_data = ast.parse(self.source_data)
                
    def progress_file(self, filename):
        if os.path.isfile(filename):
            with open(filename, "r") as file:
                self.source_data = file.read()
                self.tree_data = ast.parse(self.source_data)
        
        return self.source_data, self.tree_data

    def get_class_and_function_names1(self, filename = None):
        if filename: self.source_data, self.tree_data = self.progress_file(filename)
        script = jedi.Script(self.source_data)
        names = script.get_names(all_scopes=True)
    
        classes = [name.name for name in names if name.type == "class"]
        functions = [name.name for name in names if name.type == "function"]
    
        return classes, functions
    
    def get_class_and_function_names(self, filename = None):
        if filename: self.source_data, self.tree_data = self.progress_file(filename)
        classes = [node.name for node in ast.walk(self.tree_data) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
        return classes, functions
    
    def get_function_code(self, function_name, filename = None):
        #console.log(f"filename: {filename}")
        #console.log(f"function_name: {function_name}")
        #debug(function_name = function_name, debug = 1)
        #debug(filenamex = filename, debug = 1)
        if filename: self.source_data, self.tree_data = self.progress_file(filename)
        #console.log(f"self.source_data: {self.source_data}")
    
        # Parse the source code into an AST
        tree = ast.parse(self.source_data)
    
        # Visit the AST to find the function
        visitor = FunctionVisitor(function_name)
        visitor.visit(tree)
    
        if visitor.target_function:
            # Get the start and end line numbers of the function
            start_line = min(decorator.lineno for decorator in visitor.target_function.decorator_list) - 1 \
                if visitor.target_function.decorator_list else visitor.target_function.lineno - 1
            
            end_line = visitor.target_function.end_lineno
    
            # Extract the code lines for the function
            code_lines = self.source_data.splitlines()[start_line:end_line]
            return "\n".join(code_lines)
        else:
            return None
    
    def get_class_method_structure(self, filename = None):
        if filename: self.source_data, self.tree_data = self.progress_file(filename)
    
        visitor = ClassMethodVisitor()
        visitor.visit(self.tree_data)
        return visitor.class_methods
    
    def print_structure(self, structure):
        console = Console()
        root = Tree("[bold #ff5500]Classes and Methods[/]", guide_style = "bold #00ffff")
    
        for class_name, methods in structure.items():
            #class_str = Text(class_name, "bold #ff0000 on white")
            class_tree = root.add(f":cl_button: [bold #ff0000 on white]{class_name}[/]")
            for method in methods:
                class_tree.add(f":no_entry: [bold #ffff00]{method}[/]")
    
        console.print(root)
    
    def get_list_themes(self):
        from pygments.styles import get_all_styles
        
        # Get all available Pygments styles
        styles = list(get_all_styles())
        
        # Print the list of styles
        n = 1
        zfill = len(str(len(styles)))
        for style in sorted(styles):
            print(f"{str(n).zfill(zfill)}. {style}")
            n += 1
        
    def usage(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('FILE', help = 'Python File', action = 'store')
        parser.add_argument('-m', '--method', help = "Print method with color", action = 'store')
        parser.add_argument('-s', '--style', help = 'Style coloring, default = "fruity"', action = 'store', default = 'fruity')
        parser.add_argument('-l', '--list-style', help = 'List valid of Style coloring', action = 'store_true')
        
        if len(sys.argv) == 1:
            parser.print_help()
        else:
            args = parser.parse_args()
            if os.path.isfile(args.FILE):
                if args.method:
                    #debug(args_method = args.method, debug = 1)
                    #debug(args_FILE = args.FILE, debug = 1)
                    function_code = self.get_function_code(args.method, args.FILE)
                    console.print(f"[black on #55ff00]Code for function[/] [black on #ffff00]'{args.method}':[/]\n")
                    console.print(Syntax(function_code, 'python', theme = args.style, line_numbers = True, tab_size = 2, word_wrap = True, code_width = shutil.get_terminal_size()[0]))
                elif args.list_style:
                    self.get_list_themes()
                else:
                    structure = self.get_class_method_structure(args.FILE)
                    self.print_structure(structure)

if __name__ == "__main__":
    c = Read()
    c.usage()
    #filename = r"c:\PROJECTS\hadiocr\hadiocr\ocr.py"
    #structure = get_class_method_structure(filename)
    #print_structure(structure)


#if __name__ == "__main__":
    #filename = r"c:\PROJECTS\hadiocr\hadiocr\ocr.py"
    #function_name = "scanning"
    #function_code = get_function_code(filename, function_name)

    #if function_code:
        #print(f"Code for function '{function_name}':\n")
        #print(function_code)
    #else:
        #print(f"Function '{function_name}' not found in {filename}.")
        
    #end_time = time.time()
    #execution_time = end_time - start_time
    #print(f"Execution time: {execution_time}")    

#if __name__ == "__main__":
    #filename = r"c:\PROJECTS\hadiocr\hadiocr\ocr.py"
    #classes, functions = get_class_and_function_names(filename)
    #print("Classes:", classes)
    #print("Functions:", functions)
    
    #end_time = time.time()

    #execution_time = end_time - start_time
    #print(f"Execution time: {execution_time}")