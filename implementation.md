# Implementation Details

## Lazy evaluation

### Value Object
- Modify the value object class to support capturing variables and lazy evalution
- Member variables:
    - self.captured
        - initialized to empty dictionary
        - stores captured variables relevant to the current value
    - self.type
        - initialized to `Nil` // ??? have to check this
        - stores the type of the evaluated value (if self.evaluated is false, then self.type is garbage and should not be read)
        - As soon as something is evaluated, type must be updated and checked
        - !!! THINK ABOUT TYPES AGAIN
    - self.value 
        - initialized to `None`
        - stores an EVALUATED value
        - should only be read if self.evalutated is True
    - self.expr_ast 
        - initialized to `None`
        - stores an expression ast for whatever the variable has been assigned to
        - ??? !!! maybe combine this with self.value
    - self.evaluated
        - initialized to True
        - Upon assignment, should be set to expr_ast for most expressions (see Expressions header for more)

### Thunk Object
- self.captured
    - The entire environment at that moment captured via a custom copy method to ensure values can be cached but also won't be updated on reassignment
- self.expr
    - The expression ast for the object
    - When we do evaluate the expression, we will have to call set_value() within the value class and pass the evaluated expression to that and type to set_type() (or a function that does both, for example called evaluate)
- NOTE: we no longer need a self.evaluated type because we can check the type of the Value() object. If it is thunk, we know it is not evaluated. Otherwise, it is evaluted and value_obj.value will be a valid non-thunk value

### Unchanged Functionality
- Variable definitions

### Assignments
- As soon as we assign, set the variable type to THUNK and value to a thunk object that calls thunks constructor

- When assigning a variable to some expression statement, ex `x = y + 5 - f(x)`, create a new Value object for the assigned variable, here `x`
    - so we create a new Value() object where the expression ast for `y + 5 - f(x)` is stored
    - ??? Need to think about how want to handle types
- Capturing variables
    - When we assign, we need to capture the variables its being assigned to. Approach:
        - Scan through the current function environment until you find the variable/parameter in question.
            - Ex. in `x = y + 5 - f(x)`, we scan until we find `y` and `x`
        - Store a pointer to that value. Approach:
            - `self.captured = {y: find(y), x: find(x)}`
            - `find(var) { for env in func_env: if var in env: return var }`
            - Maybe just take a snapshot of whole env at that point --> probably easiest
            - By storing a pointer to the original, 

### Expressions
- Some specific expressions should be eagerly evaluated. Those are:
    - standalone print() calls
    - standalone inputi()/inputs() calls
    - raise     // for raising errors
    - if and for conditions
- All other expressions should not be eagerly evaluated

### Scoping


### NOTE FOR LAZY EVAL
- Only really need to change assign to not call eval_expr unless in the case of an eager evaluation
- Need to change eval_expr to handle the new value objects appropriately
- Once an expression has been evaluated, its result is cached, so it does not need to be re-evaluated again