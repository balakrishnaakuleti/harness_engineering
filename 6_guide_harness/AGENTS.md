# AGENTS.md

Instructions for any agent generating Python code in this workspace.
The harness reads this file directly and injects it into the prompt as a
**feedforward control (Guide)** — steering the model before it ever runs,
instead of only catching mistakes afterward.

## Coding Standards (must follow)

- Include a docstring on every function.
- Include type hints on every function signature.
- Do not use any external/third-party libraries, only the Python standard library.
- Wrap user input parsing in a try/except and print a friendly error on failure.

## Sprint Contract (Definition of Done)

The code is only "Done" when every item below is true:

- Program takes input from the user and prints the result.
- At least one function has a docstring.
- At least one function has type hints.
- Code compiles with no syntax errors.
