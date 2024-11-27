# document that we won't have a return inside the init/update of a for loop

import copy
from enum import Enum

from brewparse import parse_program
from env_v4 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev4 import (
    Type,
    Value,
    Thunk,
    create_value,
    get_printable,
    get_printable_debug,
)


import os  # remove/add as needed

from debug_utils import (
    debug_logger,
    debug,
    understand_ast,
)


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2
    RAISE = 3  # Add a status to raise an error


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    @debug_logger
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        self.env = EnvironmentManager()
        self.__call_func_aux("main", [])

    @debug_logger
    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = func_def

    @debug_logger
    def __get_func_by_name(self, name, num_params):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        candidate_funcs = self.func_name_to_ast[name]
        if num_params not in candidate_funcs:
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        return candidate_funcs[num_params]

    @debug_logger
    def __run_statements(self, statements, env_to_search=None):
        self.env.push_block()
        for statement in statements:
            if self.trace_output:
                print(statement)
            status, return_val = self.__run_statement(statement, env_to_search)
            if status == ExecStatus.RETURN or status == ExecStatus.RAISE:
                self.env.pop_block()
                return (status, return_val)

        self.env.pop_block()
        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    @debug_logger
    def __run_statement(self, statement, env_to_search=None):
        status = ExecStatus.CONTINUE
        return_val = None
        if statement.elem_type == InterpreterBase.FCALL_NODE:
            self.__call_func(statement)
        elif statement.elem_type == "=":
            self.__assign(statement)
        elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
            self.__var_def(statement)
        elif statement.elem_type == InterpreterBase.RETURN_NODE:
            status, return_val = self.__do_return(statement)
        elif statement.elem_type == InterpreterBase.IF_NODE:
            status, return_val = self.__do_if(statement, env_to_search)
        elif statement.elem_type == InterpreterBase.FOR_NODE:
            status, return_val = self.__do_for(statement, env_to_search)
        elif statement.elem_type == InterpreterBase.TRY_NODE:
            status, return_val = self.__do_try(statement)
        elif statement.elem_type == InterpreterBase.RAISE_NODE:
            status, return_val = self.__do_raise(statement)

        return (status, return_val)

    @debug_logger
    def __call_func(self, call_node, env_to_search=None):
        func_name = call_node.get("name")
        actual_args = call_node.get("args")
        return self.__call_func_aux(func_name, actual_args, env_to_search)

    @debug_logger
    def __call_func_aux(self, func_name, actual_args, env_to_search=None):
        if func_name == "print":
            return self.__call_print(actual_args, env_to_search)
        if func_name == "inputi" or func_name == "inputs":
            return self.__call_input(func_name, actual_args, env_to_search)

        func_ast = self.__get_func_by_name(func_name, len(actual_args))
        formal_args = func_ast.get("args")
        if len(actual_args) != len(formal_args):
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {func_ast.get('name')} with {len(actual_args)} args not found",
            )

        # first evaluate all of the actual parameters and associate them with the formal parameter names
        # pass actual parameters as a thunk object
        args = {}
        for formal_ast, actual_ast in zip(formal_args, actual_args):
            # result = copy.copy(self.__eval_expr(actual_ast, env_to_search))
            # enforce lazy evaluation by passing a thunk object
            result = Value(Type.THUNK, Thunk(actual_ast, self.env.environment))
            arg_name = formal_ast.get("name")
            args[arg_name] = result

        # then create the new activation record
        self.env.push_func()
        # and add the formal arguments to the activation record
        for arg_name, value in args.items():
            self.env.create(arg_name, value)
        _, return_val = self.__run_statements(
            func_ast.get("statements"), env_to_search
        )  # ??? should env_to_search go here?
        self.env.pop_func()
        return return_val

    @debug_logger
    def __call_print(self, args, env_to_search=None):
        output = ""
        for arg in args:
            result = self.__eval_expr(arg, env_to_search)  # result is a Value object
            debug(get_printable_debug(result))
            output = output + get_printable(result)
        super().output(output)
        return Interpreter.NIL_VALUE

    @debug_logger
    def __call_input(self, name, args, env_to_search=None):
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0], env_to_search)
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if name == "inputi":
            return Value(Type.INT, int(inp))
        if name == "inputs":
            return Value(Type.STRING, inp)

    @debug_logger
    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        expr_ast = assign_ast.get("expression")
        value_obj = Value(Type.THUNK, Thunk(expr_ast, self.env.environment))
        if not self.env.set(var_name, value_obj):
            super().error(
                ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment"
            )

    @debug_logger
    def __var_def(self, var_ast):
        var_name = var_ast.get("name")
        if not self.env.create(var_name, Interpreter.NIL_VALUE):
            super().error(
                ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}"
            )

    @debug_logger
    def __eval_expr(self, expr_ast, env_to_search=None):
        # We want to guarentee that anytime __eval_expr is called, a non-thunk object is called
        debug(f"expr_ast.elem_type is {expr_ast.elem_type}")
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            return Interpreter.NIL_VALUE
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            var_name = expr_ast.get("name")
            # searches appropriate environment (either global or captured one)
            val = self.env.get(var_name, env_to_search)
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            debug(get_printable_debug(val))
            # Force thunk to evaluate
            return_val = self.__force_thunk_evaluation(val)
            self.__check_if_thunk(return_val)
            return return_val
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            val = self.__call_func(expr_ast)
            return_val = self.__force_thunk_evaluation(val)
            self.__check_if_thunk(return_val)
            return return_val
            # return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return_val = self.__eval_op(expr_ast, env_to_search)
            self.__check_if_thunk(return_val)
            return return_val
        if expr_ast.elem_type == Interpreter.NEG_NODE:
            return_val = self.__eval_unary(
                expr_ast, Type.INT, lambda x: -1 * x, env_to_search
            )
            self.__check_if_thunk(return_val)
            return return_val
        if expr_ast.elem_type == Interpreter.NOT_NODE:
            return_val = self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)
            self.__check_if_thunk(return_val)
            return return_val
            # return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)

    def __check_if_thunk(self, ret_val):
        if ret_val.type() == Type.THUNK:
            super().error(
                ErrorType.TYPE_ERROR,
                f"THIS IS A PROBLEM: WE SHOULD NOT RETURN A THUNK OBJECT TYPE IN EVAL_EXPR",
            )

    @debug_logger
    def __force_thunk_evaluation(self, val):
        if (
            val.type() == Type.THUNK
        ):  # !!! maybe make this a while, shouldn't be necessary bc eval_expr should guarentee to return a value object
            value_obj = self.__eval_expr(val.value().expr(), val.value().env_snapshot())
            val.set_value_type(value_obj.value(), value_obj.type())
        return val

    @debug_logger
    def __eval_op(self, arith_ast, env_to_search):
        debug(f"arith_ast.get(op1) is {arith_ast.get("op1")}")
        left_value_obj = self.__eval_expr(arith_ast.get("op1"), env_to_search)
        right_value_obj = self.__eval_expr(arith_ast.get("op2"), env_to_search)
        if not self.__compatible_types(
            arith_ast.elem_type, left_value_obj, right_value_obj
        ):
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types for {arith_ast.elem_type} operation",
            )
        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    @debug_logger
    def __compatible_types(self, oper, obj1, obj2):
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        return obj1.type() == obj2.type()

    @debug_logger
    def __eval_unary(self, arith_ast, t, f, env_to_search):
        value_obj = self.__eval_expr(arith_ast.get("op1"), env_to_search)
        if value_obj.type() != t:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible type for {arith_ast.elem_type} operation",
            )
        return Value(t, f(value_obj.value()))

    @debug_logger
    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        #  set up operations on strings
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        #  set up operations on bools
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() and y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on nil
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

    @debug_logger
    def __do_if(self, if_ast, env_to_search=None):
        cond_ast = if_ast.get("condition")
        result = self.__eval_expr(cond_ast, env_to_search)
        if result.type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            )
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(
                statements, env_to_search
            )  # ??? does env_to_search go here?
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(
                    else_statements, env_to_search  # ??? does env_to_search go here?
                )
                return (status, return_val)

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    @debug_logger
    def __do_for(self, for_ast, env_to_search=None):
        init_ast = for_ast.get("init")
        cond_ast = for_ast.get("condition")
        update_ast = for_ast.get("update")

        self.__run_statement(
            init_ast, env_to_search
        )  # ??? does env_to_search go here? # initialize counter variable
        run_for = Interpreter.TRUE_VALUE
        while run_for.value():
            run_for = self.__eval_expr(
                cond_ast, env_to_search
            )  # check for-loop condition
            if run_for.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for for condition",
                )
            if run_for.value():
                statements = for_ast.get("statements")
                status, return_val = self.__run_statements(
                    statements, env_to_search
                )  # ??? does env_to_search go here?
                if status == ExecStatus.RETURN or status == ExecStatus.RAISE:
                    return status, return_val
                self.__run_statement(
                    update_ast, env_to_search  # ??? does env_to_search go here?
                )  # update counter variable

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    @debug_logger
    def __do_return(self, return_ast):
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            return (ExecStatus.RETURN, Interpreter.NIL_VALUE)
        # value_obj = copy.copy(self.__eval_expr(expr_ast))
        value_obj = Value(Type.THUNK, Thunk(expr_ast, self.env.environment))
        return (ExecStatus.RETURN, value_obj)

    # !!! ??? should I pass in env_to_search here or no
    @debug_logger
    def __do_try(self, try_ast):
        # Run the statements in the try block (either all run or run until error or until hit raise statement or until hit return)
        statements = try_ast.get("statements")
        # don't need to worry about scoping as this is taking care of by __run_statements
        status, return_val = self.__run_statements(statements)
        # If the status is RAISE, look through catchers to see if it matches any
        if status == ExecStatus.RAISE:
            catchers = try_ast.get("catchers")
            for catch_ast in catchers:
                # If the catch exception type is the same as the raised exception value, run the catch block, returning the status and return_val
                if catch_ast.get("exception_type") == return_val.value():
                    catch_statements = catch_ast.get("statements")
                    status, return_val = self.__run_statements(catch_statements)
                    return (status, return_val)
            # No matching catch statement
            super().error(
                ErrorType.FAULT_ERROR,
                "Raise condition is not caught",
            )
        return (status, return_val)
        # return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)
        # !!! any reason i might want above instead of what i have now (similar to do_for and such)

    @debug_logger
    def __do_raise(self, raise_ast):
        # Eagerly evaluate the raise exception type
        value_obj = self.__eval_expr(raise_ast.get("exception_type"))
        # Make sure returned type is of string type
        if value_obj.type() != Type.STRING:
            super().error(
                ErrorType.TYPE_ERROR,
                "Raise condition does not evaluate to a string",
            )
        # Return that raise value with RAISE status
        return (ExecStatus.RAISE, value_obj)


if __name__ == "__main__":
    interpreter = Interpreter()

    # directory = "tests/tests/run_these_now"
    directory = "tests/tests/passed"
    # directory = "tests/intended_errors/run_these_now"

    # Loop through all files in the specified directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            print(f"Processing file: {filename}")
            with open(file_path, "r") as file:
                content = file.read()
                # Run the interpreter on the file content
                interpreter.run(content)
            print()
