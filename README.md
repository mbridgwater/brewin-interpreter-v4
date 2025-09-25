# CS 131 Fall 2024: Project 4

Hey there! This project was developed from starter code (developed by the UCLA CS 131 teaching team led by Carey Nachenberg). The starter code contained the necessary bootstrapping code:
- `ply/lex.py`, `ply/yacc.py`, `brewlex.py`, `brewparse.py`, responsible for taking in a string representing a Brewin program and outputting an AST (parser logic)
- `elements.py`, defines the return type of the parser
- `intbase.py`, the base class and enum definitions for the interpreter
- released solutions to previous stages of the project when applicable

This interpreter supports the following major functions/operations (among others) and was developed in four stages (the spec per each stage is upload in specs folder):
1. build an interpreter with simple functionality, including supporting variable definition, variable assignment, and printing
2. add support for functions, boolean variables, null values, binary arithmetic operators, integer comparisons, boolean/string comparisons, boolean operations, string concatenation, if/else statements, loops
3. alter interpreter to expect and support static typing, add support for default return types, add support for structs, 
4. need semantics, lazy evaluation, and exception handling for the interpreter

## Licensing and Attribution

This is an unlicensed repository; even though the source code is public, it is **not** governed by an open-source license.

The starter code was primarily written by [Carey Nachenberg](http://careynachenberg.weebly.com/), with support from his TAs for the [Fall 2024 iteration of CS 131](https://ucla-cs-131.github.io/fall-24-website/).
