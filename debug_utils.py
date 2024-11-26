from brewparse import parse_program
from type_valuev3 import get_printable

DEBUG_MODE = True  # Toggle for debugging
INFO_MODE = True  # Toggle for general information
indent_amount = 0  # Tracks current indentation level for functions
BLUE = "\033[94m"  # To color print statements
RESET = "\033[0m"


def debug(msg):
    global indent_amount
    if DEBUG_MODE:
        print(" " * indent_amount + f"DEBUG: {msg}")


def info(msg):
    global indent_amount
    if INFO_MODE:
        print(" " * indent_amount + f"INFO: {msg}")


def warning(msg):
    global indent_amount
    print(" " * indent_amount + f"WARNING: {msg}")


def debug_logger(func):
    def wrapper(*args, **kwargs):
        global indent_amount
        if DEBUG_MODE:
            print(" " * indent_amount + f"{BLUE}Entering: {func.__name__}{RESET}")
            indent_amount += 2  # Increase indentation for nested calls
        result = func(*args, **kwargs)
        if DEBUG_MODE:
            indent_amount -= 2  # Decrease indentation after exiting
            print(" " * indent_amount + f"{BLUE}Exiting: {func.__name__}{RESET}")
        return result

    return wrapper


def debug_logger_with_return_val(func):
    def wrapper(*args, **kwargs):
        global indent_amount
        if DEBUG_MODE:
            print(" " * indent_amount + f"{BLUE}Entering: {func.__name__}{RESET}")
            indent_amount += 2  # Increase indentation for nested calls
        result = func(*args, **kwargs)
        if DEBUG_MODE:
            indent_amount -= 2  # Decrease indentation after exiting
            print(
                " " * indent_amount
                + f"{BLUE}Exiting: {func.__name__} with return value: {get_printable(result)}{RESET}"
            )
        return result

    return wrapper


def _understand_ast(program):
    """This function is intended for internal debugging use to understand
    the ast tree and how to read it"""
    # print("----------------PROGRAM----------------")
    if DEBUG_MODE:
        ast = parse_program(program)
        print("AST LOOKS LIKE")
        print(ast)
        print("AST DICT LIKE")
        print(ast.dict)
        # print(ast.elem_type)
        print("LOOKING AT ALL FUNCTIONS IN AST")
        for elem in ast.get("functions"):
            print(f"-----{elem.get("name")}-----")
            print("ELEM STR")
            print(str(elem))
            print("ELEM DICT")
            print(elem.dict)
            print("ELEM VAL")
            print(elem._Element__val(elem))  # ??? OH: Why might we use this?
        # for ast_part in ast:  # Of type Element, so not iterable
        #     print(ast_part)
        # self.output(ast)
