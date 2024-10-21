import clang.cindex

# Set the path to libclang.dll
clang.cindex.Config.set_library_file("c:/SDK/LLVM/bin/libclang.dll")

def get_c_file_structure(filename):
    # Initialize clang index
    index = clang.cindex.Index.create()

    # Parse the C file
    translation_unit = index.parse(filename)

    # Function to recursively extract functions and structs
    def extract_structure(node, structures):
        if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            structures["functions"].append(node.spelling)
        elif node.kind == clang.cindex.CursorKind.STRUCT_DECL:
            structures["structs"].append(node.spelling)

        for child in node.get_children():
            extract_structure(child, structures)

    structures = {"functions": [], "structs": []}
    extract_structure(translation_unit.cursor, structures)
    return structures

def print_structure(structure):
    from rich.console import Console
    from rich.tree import Tree

    console = Console()
    root = Tree("C File Structure")

    structs_tree = root.add("Structs")
    for struct in structure["structs"]:
        structs_tree.add(f"|_ {struct}")

    functions_tree = root.add("Functions")
    for function in structure["functions"]:
        functions_tree.add(f"|_ {function}")

    console.print(root)

if __name__ == "__main__":
    filename = r"c:\PROJECTS\hadiocr\hadiocr\ocr.c"
    structure = get_c_file_structure(filename)
    print_structure(structure)
