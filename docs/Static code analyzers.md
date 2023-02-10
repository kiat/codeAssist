To ensure the quality and maintainability of Python code, various static
code analyzers have been developed to detect potential bugs, code
smells, and security vulnerabilities. MyPy: Mypy will flag any variables
or expressions with inconsistent or mismatched types, such as using an
integer where a string is expected. Mypy will check that types are
compatible with the operations being performed, such as checking that a
list is being used with the correct index type.

PyLint: PyLint is a widely used Python static code analyzer that checks
code for potential bugs and style issues. It is designed to work with
the abstract syntax tree of Python code, and can detect issues such as
unused variables, undefined names, and code that is too complex. PyLint
also provides suggestions for how to improve the code.

Flake8: Flake8 is another popular Python static code analyzer that
combines the functionality of three other Python tools: PyFlakes,
McCabe, and pep8. Like PyLint, Flake8 checks code for potential bugs and
style issues, but it also checks for compliance with the PEP 8 style
guide for Python code. This makes it a useful tool for enforcing coding
standards in Python projects.

Bandit: Bandit is a security-focused Python static code analyzer that
checks code for potential security vulnerabilities. It uses a set of
plugins to check for issues such as code that is susceptible to SQL
injection, cross-site scripting (XSS), and other common security issues.
Bandit is designed to be easy to use, and provides clear, actionable
results that can be used to improve the security of Python code.

Prospector is a Python static code analyzer that combines the
capabilities of multiple tools into a single, easy-to-use package. It
can perform linting, style checking, and complexity analysis all in one
run. Prospector uses tools such as PyLint, Flake8, and McCabe to analyze
the code and provide recommendations for improvement. Additionally,
Prospector can be easily integrated into other tools, such as code
editors or continuous integration platforms, to streamline the
development process. With its combination of functionality and ease of
use, Prospector is a popular choice for Python developers looking to
improve the quality of their code and probably the best for us.

We should use PyLint for checking style issues and Bandit for checking
security vulnerabilities via prospector.

Tool Purpose Mypy Type checking PyLint Linting Flake8 Linting, style
checking PyFlakes Linting Prospector Linting, style checking, complexity
analysis
