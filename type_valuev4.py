from intbase import InterpreterBase


# Enumerated type for our different language data types
class Type:
    INT = "int"
    BOOL = "bool"
    STRING = "string"
    NIL = "nil"
    THUNK = "thunk"


# Represents a thunk object, which is an unevaluated object to support lazy evaluation
class Thunk:
    def __init__(self, expr_ast, env):
        self.__expr = expr_ast
        self.__env_snapshot = self.custom_copy(env)

    def expr(self):
        return self.__expr

    def env_snapshot(self):
        return self.__env_snapshot

    def custom_copy(self, env):
        ret_env = []
        for func_block in env:
            ret_env.append([])
            for block in func_block:
                ret_env[-1].append({})
                for var, val in block.items():
                    ret_env[-1][-1][var] = val
        return ret_env


# Represents a value, which has a type and its value
class Value:
    def __init__(self, type, value=None):
        # maybe have a thunk object. Set type to thunk and value to the thunk object when needed
        # consider capturing the whole environment
        self.__t = type
        self.__v = value

    def value(self):
        # if self.__t == Type.THUNK:
        #     # !!! force evaluation
        #     pass
        return self.__v

    def type(self):
        return self.__t

    def set_value_type(self, val, type):
        self.__v = val
        self.__t = type


def create_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type.BOOL, True)
    elif val == InterpreterBase.FALSE_DEF:
        return Value(Type.BOOL, False)
    elif val == InterpreterBase.NIL_DEF:
        return Value(Type.NIL, None)
    elif isinstance(val, str):
        return Value(Type.STRING, val)
    elif isinstance(val, int):
        return Value(Type.INT, val)
    else:
        raise ValueError("Unknown value type")


def get_printable(val):
    if val.type() == Type.INT:
        return str(val.value())
    if val.type() == Type.STRING:
        return val.value()
    if val.type() == Type.BOOL:
        if val.value() is True:
            return "true"
        return "false"
    return None


# def get_printable_debug(val):
#     return (
#         f"(t: {val.type()}, v: {val.value()})"
#         if val.type() != Type.THUNK
#         else f"(t: {val.type()}, v: (expr: {val.value().expr()}), (env_snapshot: {get_printable_env(val.value().env_snapshot())}))"
#     )


# def get_printable_env(env_snapshot):
#     my_str = "["
#     blk_cnt = 0
#     for block in env_snapshot:
#         my_str += "["
#         func_cnt = 0

#         for func_scope in block:
#             my_str += "{"
#             for key, val in func_scope.items():
#                 # !!! if having issues turning in, make sure to remove this
#                 my_str += "'" + key + "': "
#                 my_str += get_printable_debug(val)
#                 if key != list(func_scope.keys())[-1]:
#                     my_str += ", "
#             my_str += "}"
#             if func_cnt != len(block) - 1:
#                 my_str += ", "
#             func_cnt += 1

#         my_str += "]"
#         if blk_cnt != len(env_snapshot) - 1:
#             my_str += ", "
#         blk_cnt += 1
#     my_str += "]"
#     return my_str
