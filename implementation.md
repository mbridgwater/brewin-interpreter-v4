# Implementation Details

## Error Handling
- We add an ExecStatus.RAISE type
- When we hit a raise, we eagerly evaluate its expression and return (ExecStatus.RAISE, raise_val_obj)
- We must make sure that this status is propagated across function calls and scopes
    - A raise can occur when evaluating an expression (if part of expression is function that raises something), calling a function, p much anytime etc (won't happen for __assign or __var_def)
    - Alter the eval_expr to also return a status and if that status is RAISE, return (model it like run_statement)
    - Within __eval_expr, only the FCALL_NODE elem type will actually result in a RAISE status. Then check every eval_expr call and __call_func call and return if raise status
    - Had to add this status tp __call_print as well

## Lazy evaluation

### Value Object
- Stays almost the same as before, but now supports a new type `THUNK` that corresponds to a thunk value which is a `Thunk` object
- Member variables:
    - self.__t
        - initialized to `Nil`
        - stores the type of the evaluated value or `THUNK`
    - self.__v 
        - initialized to `None`
        - stores an evaluated value OR a `Thunk` object

### Thunk Object
- self.__env_snapshot
    - The entire environment at that moment captured via a custom copy method to ensure values can be cached but also won't be updated on reassignment
- self.__expr
    - The expression ast for the object
    - When we do evaluate the expression, we will have to call set_value() within the value class and pass the evaluated expression to that and type to set_type() (or a function that does both, for example called evaluate)
- NOTE: we no longer need a self.evaluated type because we can check the type of the Value() object. If it is thunk, we know it is not evaluated. Otherwise, it is evaluated and value_obj.value will be a valid non-thunk value

### Unchanged Functionality
- Variable definitions
- Scoping

### Environment searching
- When evaluating the thunk object, we pass its snapshot as the environment to search for eval_expr. Thus, every function within eval_expr must also take this parameter (except __force_thunk_evaluation and __check_if_thunk). This includes:
    - self.env.get()
    - __call_func
    - __eval_unary
    - __eval_op
    - Recursively, all sub functions of these above functions must also take the snapshot param, including
        - __call_func_aux
        - __call_print

- INSTEAD OF ABOVE APPROACH: have a global environment pointer that points to the correct environment




### Assignments
- As soon as we assign, set the variable type to THUNK and value to a thunk object that calls thunks constructor
- Capturing variables
    - When we assign, we need to capture the variables its being assigned to and pass this to the Thunk constructor. Approach:
        - make a snapshot of the environment which is a special/custom copy of it. Code for this is along the lines of:
            ```
            def special_copy(env):
                ret_env = []
                for func_block in env:
                    ret_env.append([])
                    for block in func_block:
                        ret_env[-1].append({})
                        for var, val in block.items():
                            ret_env[-1][-1][var] = val
                return ret_env
            ```
        

### Expressions
- Some specific expressions should be eagerly evaluated. Those are:
    - standalone print() calls
    - standalone inputi()/inputs() calls
    - raise     // for raising errors
    - if and for conditions
- All other expressions should not be eagerly evaluated
- Function calls, including calls to inputi() and inputs(), within expressions are also evaluated lazily unless they are in an eager evaluation context.
    - This should be handled by making __eval_expr lazy for assignments (so when we assign, we do not call __eval_expr) but not making __call_func itself lazy (it runs as soon as called)
- Need to change call func to not evaluate its parameters until they are used do to a situation like:
    ```
    func f(x) {
        print("running f");
        return 1;
    }

    func g(x) {
        print("running g");
        return x;
    }

    func main() {
        var x;
        var y;
        y = 5;
        f(g(5));
        print("ending");
    }
    ```
- Same as above for returns 
- For the __eval_expr function, we want to guarentee that it will NEVER return a Thunk Object

### NOTE FOR LAZY EVAL
- Only really need to change assign to not call eval_expr unless in the case of an eager evaluation
- Need to change eval_expr to handle the new value objects appropriately
- Once an expression has been evaluated, its result is cached, so it does not need to be re-evaluated again