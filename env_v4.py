# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
from type_valuev4 import get_printable_debug


class EnvironmentManager:
    def __init__(self):
        self.environment = []
        self.nested_trys = 0

    # returns a VariableDef object
    def get(self, symbol, env_snapshot=None):
        cur_func_env = (
            self.environment[-1] if env_snapshot is None else env_snapshot[-1]
        )
        for env in reversed(cur_func_env):
            if symbol in env:
                return env[symbol]

        return None

    def set(self, symbol, value):
        cur_func_env = self.environment[-1]
        for env in reversed(cur_func_env):
            if symbol in env:
                env[symbol] = value
                return True

        return False

    # create a new symbol in the top-most environment, regardless of whether that symbol exists
    # in a lower environment
    def create(self, symbol, value):
        cur_func_env = self.environment[-1]
        if symbol in cur_func_env[-1]:  # symbol already defined in current scope
            return False
        cur_func_env[-1][symbol] = value
        return True

    # used when we enter a new function - start with empty dictionary to hold parameters.
    def push_func(self):
        self.environment.append([{}])  # [[...]] -> [[...], [{}]]

    def push_block(self):
        cur_func_env = self.environment[-1]
        cur_func_env.append({})  # [[...],[{....}] -> [[...],[{...}, {}]]

    def pop_block(self):
        cur_func_env = self.environment[-1]
        cur_func_env.pop()

    # used when we exit a nested block to discard the environment for that block
    def pop_func(self):
        self.environment.pop()

    def get_printable_env(self):
        my_str = "["
        blk_cnt = 0
        for block in self.environment:
            my_str += "["
            func_cnt = 0

            for func_scope in block:
                my_str += "{"
                for key, val in func_scope.items():
                    # !!! if having issues turning in, make sure to remove this
                    my_str += "'" + key + "': "
                    my_str += get_printable_debug(val)
                    if key != list(func_scope.keys())[-1]:
                        my_str += ", "
                my_str += "}"
                if func_cnt != len(block) - 1:
                    my_str += ", "
                func_cnt += 1

            my_str += "]"
            if blk_cnt != len(self.environment) - 1:
                my_str += ", "
            blk_cnt += 1
        my_str += "]"
        return my_str
