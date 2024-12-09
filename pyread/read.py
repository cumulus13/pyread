import time
import ast
import sys, os
import jedi
import argparse
from jsoncolor import jprint
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.syntax import Syntax
from rich import traceback as rich_traceback
import shutil
from pydebugger.debug import debug
import pyperclip

rich_traceback.install(theme = 'fruity', max_frames = 30, width = shutil.get_terminal_size()[0])

console = Console()

start_time = time.time()

class ClassMethodVisitor(ast.NodeVisitor):
    def __init__(self):
        self.class_methods = {}

    def visit_ClassDef(self, node):
        #debug(node_name = node.name, debug = 1)
        # #debug(node_body = node.body, debug = 1)
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        #debug(methods = methods, debug = 1)
        self.class_methods[node.name] = methods
        #debug(self_class_methods = self.class_methods, debug = 1)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        if not self.class_methods.get('no_class'):
            self.class_methods['no_class'] = [node.name]
        else:
            self.class_methods['no_class'].append(node.name)
        self.generic_visit(node)

class FunctionVisitor(ast.NodeVisitor):
    def __init__(self, class_name=None, method_name=None):
        #debug(class_name = class_name)
        #debug(method_name = method_name, debug = 1)
        # self.target_function = None
        self.target_functions = {}
        self.class_name = class_name
        self.method_name = method_name
        self.inside_class = False  # Track if we're inside the right class
        self.temp_class = None

    def visit_ClassDef(self, node):
        self.inside_class = False
        # #debug(self_class_name_0 = self.class_name, debug = 1)
        # #debug(node_class = node, debug = 1)
        #debug(node_name_class = node.name, debug = 1)
        self.temp_class = node.name
        if self.class_name and node.name == self.class_name:
            self.inside_class = True  # We are inside the target class
            self.target_functions.update({node.name:''})
            # self.temp_class = node.name
        self.generic_visit(node)  # Visit the body of the class to find the method
        # elif not self.class_name:
        #     self.inside_class = False  # Outside any
        #     self.generic_visit(node)  # Visit the body of the class to find the method
        # else:
        #     self.inside_class = False  # Skip visiting other classes

    def visit_FunctionDef(self, node):
        # #debug(self_class_name_1 = self.class_name, debug = 1)
        # #debug(self_method_name = self.method_name, debug = 1)
        # #debug(self_inside_class = self.inside_class, debug = 1)
        # #debug(node_func = node, debug = 1)
        #debug(node_name_func = node.name, debug = 1)
        # if self.inside_class and node.name == self.method_name and self.class_name:
        if node.name == self.method_name:
            # If we're inside the class and the method matches, we found it
            # self.target_function = node
            # self.target_functions.append(node)
            #debug(self_class_name = self.class_name, debug = 1)
            #debug(self_temp_class = self.temp_class, debug = 1)
            if self.class_name and self.class_name == self.temp_class:
                self.target_functions[self.class_name] = node
                self.temp_class = None
            else:
                if self.temp_class:
                    self.target_functions[self.temp_class] = node
                    self.temp_class = None
                else:
                    if not self.target_functions.get('no_class'):
                        self.target_functions['no_class'] = [node]
                    else:
                        self.target_functions['no_class'].append(node)
            # print('-'*shutil.get_terminal_size()[0])
            # #debug(self_inside_class = self.inside_class, debug = 1)
            # #debug(self_method_name = self.method_name, debug = 1)
            # #debug(node_name = node.name, debug = 1)
            # #debug(self_target_function = self.target_function, debug = 1)
            # #debug(self_target_function_decorator_list = self.target_function.decorator_list, debug = 1)
            # #debug(self_target_function_lineno = self.target_function.lineno, debug = 1)
            # self.inside_class = False
            
        # elif not self.inside_class and not self.class_name and node.name == self.method_name:
        #     self.target_function = node
        #     self.target_functions.append(node)
        # self.generic_visit(node)  # Keep looking for methods
        
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
        # tree = ast.parse(self.source_data)

        #debug(function_name = function_name, debug = 1)
        # Visit the AST to find the function
        visitor = FunctionVisitor(None, function_name)
        visitor.visit(self.tree_data)
        #debug(visitor_target_function = visitor.target_function, debug = 1)
        
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
        
        # #debug(self_source_data = self.source_data, debug = 1)
        # #debug(self_tree_data = self.tree_data, debug = 1)
    
        visitor = ClassMethodVisitor()
        visitor.visit(self.tree_data)
        # debug(visitor_class_methods = visitor.class_methods, debug = 1)
        # debug(dir_visitor_class_methods = dir(visitor.class_methods), debug = 1)
        # jprint(str(visitor.class_methods))
        return visitor.class_methods
    
    def print_structure(self, structure, filename = None):
        console = Console()
        root = Tree(f"[bold #ff5500]Classes and Methods[/] [bold #55FFFF]{filename if filename else ''}[/]", guide_style = "bold #00ffff")
    
        for class_name, methods in structure.items():
            #class_str = Text(class_name, "bold #ff0000 on white")
            if not class_name == 'no_class':
                class_tree = root.add(f":cl_button: [bold #ff0000 on white]{class_name}[/]")
                for method in methods:
                    class_tree.add(f":no_entry: [bold #ffff00]{method}[/]")
            else:
                class_tree = root.add(f":cl_button: [bold #ff0000 on white]{filename if filename else 'root'}[/]")
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
        
    def print_node(self, visitor, node, method_name, class_name = None, theme = 'fruity', clip = False):
        visitor.generic_visit(node)
        # Get the start and end line numbers of the function
        start_line = min(decorator.lineno for decorator in node.decorator_list) - 1 \
            if node.decorator_list else node.lineno - 1
        #debug(start_line = start_line, debug = 1)
        end_line = node.end_lineno
        #debug(end_line = end_line, debug = 1)

        # Extract the code lines for the method
        code_lines = self.source_data.splitlines()[start_line:end_line]
        function_code = "\n".join(code_lines)

        if class_name:
            console.print(f"[black on #55ff00]Code for method[/] [black on #ffff00]'{class_name}.{method_name}':[/]\n")
        else:
            console.print(f"[black on #55ff00]Code for method[/] [black on #ffff00]'{method_name} (Outside Any Class)':[/]\n")
        syntax = Syntax(function_code, 'python', theme=theme, line_numbers=True, tab_size=2, word_wrap=True, code_width=shutil.get_terminal_size()[0])
        
        console.print(syntax)
        pyperclip.copy(syntax.code)

    def display_code_with_syntax_highlighting(self, code: str, theme: str = 'fruity', code_type = 'python'):
        """Display the clipboard content with syntax highlighting."""
        syntax = Syntax(code, code_type, theme=theme, line_numbers=True)
        console = Console()
        console.print(syntax)

    def save_to_file(self, content: str, filename: str):
        """Save the content to the specified file."""
        try:
            with open(filename, 'w') as file:
                file.write(content)
            console.print(f"[bold #00FFFF]File saved successfully as [/][bold #FFAA00]{filename}[/]")
        except Exception as e:
            console.print(f"[white on red blink]Error saving file:[/] [white on #0000FF]{e}[/]")

    def vim_like_mode(self):
        """Vim-like mode for saving files."""
        console.print(f"\n[bold #55FFFF]Type[/] [bold #00FFFF]'filename'[/] [bold #55FFFF]to save, or[/] [bold #FF00FF]'x,q,exit,quit'[/] [bold #55FFFF]to quit.[/]")
        while True:
            command = input(":").strip()  # Strip any extra spaces
            if command and command.lower() in ['exit','quit','q','x']:
                console.print("[bold #FFAA00]Exiting .[/]")
                break
            elif command and os.path.isdir(os.path.dirname(command)):
                # filename = command[1:].strip()  # Get the filename after the colon
                # filname = command
                if command:
                    # Check for invalid filename cases
                    if not os.path.isdir(command):
                        return command
                    else:
                        console.print(f"[white on red blink]Invalid filename:[/] [bold #FFFF00]{command}[/] [white on red blink]is a directory.[/]")
                else:
                    console.print("[white on #FF00FF]Please provide a valid filename !.[/]")
            elif command:
                return command
            else:
                console.print("[white on red blink]Invalid command.[/] [bold #55FF00]Use[/] [bold #00FFFF]'filename'[/] [bold #55FFFF]to save, or[/] [bold #FF00FF]'x,q,exit,quit'[/] [bold #55FFFF]to quit.[/]")
    
    def usage(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('FILE', help='Python File', action='store', nargs='?')
        parser.add_argument('-m', '--method', help="Print method with color", action='store')
        parser.add_argument('-s', '--style', help='Style coloring, default = "fruity"', action='store', default='fruity')
        parser.add_argument('-l', '--list-style', help='List valid Style coloring', action='store_true')
        parser.add_argument('-t', '--type', help = 'Code type', default = 'python')
        parser.add_argument('-C', '--code', help = 'Read source code', action='store_true')
        parser.add_argument('-c', '--copy', help = 'Copy to clipboard', action='store_true')
    
        if len(sys.argv) == 1:
            parser.print_help()
        else:
            args = parser.parse_args()
    

            if args.FILE:
                if os.path.isfile(args.FILE):
                    self.source_data, self.tree_data = self.progress_file(args.FILE)
                    class_name = None

                    if args.method:
                        # Check if the method argument includes a dot (e.g., Classname.method)
                        if '.' in args.method:
                            class_name, method_name = args.method.split('.')
                            # self.source_data, self.tree_data = self.progress_file(args.FILE)
                        else:
                            method_name = args.method
        
                        # Use the refined FunctionVisitor to search for the method inside the specified class
                        visitor = FunctionVisitor(class_name=class_name, method_name=method_name)
                        #debug(visitor = visitor, debug = 1)
                        visitor.visit(self.tree_data)
                        # #debug(visitor_target_function = visitor.target_function, debug = 1)
                        #debug(visitor_target_functions = visitor.target_functions, debug = 1)
                        
                        if visitor.target_functions:
                            for target in visitor.target_functions:
                                if not target == 'no_class':
                                    node = visitor.target_functions.get(target)
                                    self.print_node(visitor, node, method_name, target, args.style, args.copy)
                                else:
                                    for node_method in visitor.target_functions.get(target):
                                        self.print_node(visitor, node_method, method_name, None, args.style, args.copy)
                        else:
                            console.print(f"[bold red]Method '{method_name}' not found in class '{class_name}'.[/]")
        
                        # else:
                            # If no class is specified, search for the method in all classes
                            # structure = self.get_class_method_structure(args.FILE)
                            # print("-"*shutil.get_terminal_size()[0])
                            # #jprint(structure)
                            # #debug(structure_items = structure.items(),debug = 1)
                            # found_methods = [(cls, args.method) for cls, methods in structure.items() if args.method in methods]
                            # #debug(found_methods = found_methods, debug = 1)
                            
                            ###########################################################################################################################
                            # function_names = [node.name for node in ast.iter_child_nodes(self.tree_data) if isinstance(node, ast.FunctionDef)]
                            # #debug(function_names = function_names, debug = 1)
                            # found_methods = list(filter(lambda k: k == args.method, function_names))
                            # #debug(found_methods = found_methods, debug = 1)
        
                            # if found_methods:
                            #     # for class_name, method_name in found_methods:
                            #     for method in found_methods:
                            #         # function_code = self.get_function_code(method_name, args.FILE)
                            #         function_code = self.get_function_code(method, args.FILE)
                            #         #debug(function_code = function_code, debug = 1)
                            #         # console.print(f"[black on #55ff00]Code for method[/] [black on #ffff00]'{class_name}.{method_name}':[/]\n")
                            #         console.print(f"[black on #55ff00]Code for method[/] [black on #ffff00]'{method}':[/]\n")
                            #         console.print(Syntax(function_code, 'python', theme=args.style, line_numbers=True, tab_size=2, word_wrap=True, code_width=shutil.get_terminal_size()[0]))
                            # else:
                            #     console.print(f"[bold red]Method '{args.method}' not found in any class.[/]")
                            ###########################################################################################################################

                            # visitor = FunctionVisitor(method_name=args.method)
                            # #debug(visitor = visitor, debug = 1)
                            # visitor.visit(self.tree_data)
                            # #debug(visitor_target_function = visitor.target_function, debug = 1)
                            
                            # if visitor.target_function:
                            #     # Get the start and end line numbers of the function
                            #     start_line = min(decorator.lineno for decorator in visitor.target_function.decorator_list) - 1 \
                            #         if visitor.target_function.decorator_list else visitor.target_function.lineno - 1
                            #     #debug(start_line = start_line, debug = 1)
                            #     end_line = visitor.target_function.end_lineno
                            #     #debug(end_line = end_line, debug = 1)
        
                            #     # Extract the code lines for the method
                            #     code_lines = self.source_data.splitlines()[start_line:end_line]
                            #     function_code = "\n".join(code_lines)
        
                            #     console.print(f"[black on #55ff00]Code for method[/] [black on #ffff00]'{class_name}.{method_name}':[/]\n")
                            #     console.print(Syntax(function_code, 'python', theme=args.style, line_numbers=True, tab_size=2, word_wrap=True, code_width=shutil.get_terminal_size()[0]))
                            # else:
                            #     console.print(f"[bold red]Method '{method_name}' not found in class '{class_name}'.[/]")
            
                    elif args.list_style:
                        self.get_list_themes()
                    else:
                        structure = self.get_class_method_structure(args.FILE)
                        self.print_structure(structure, args.FILE)

                    if args.code:
                        with open(args.FILE, 'r') as f:
                            self.display_code_with_syntax_highlighting(f.read())
                
                elif args.FILE == 'c':
                    clipboard_content = pyperclip.paste()

                    # Display the content with syntax highlighting
                    print("Code:\n")
                    self.display_code_with_syntax_highlighting(clipboard_content, args.style, args.type)

                    # Enter Vim-like mode for saving the file
                    filename = self.vim_like_mode()

                    if filename:
                        # Save clipboard content to the specified file
                        self.save_to_file(clipboard_content, filename)
                
                else:
                    parser.print_help()

            elif args.list_style:
                self.get_list_themes()
    
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