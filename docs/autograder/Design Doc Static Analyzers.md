<a name="br1"></a>**Code Assist Static Code Analyzers**

The **purpose** of this design document is to ensure the use and development of static code analyzers for the use in code assist

To ensure the quality and maintainability of Python code, various static code analyzers havebeen developed to detect potential bugs, code smells, and security vulnerabilities. MyPy: Mypywill flag any variables or expressions with inconsistent or mismatched types, such as using aninteger where a string is expected. Mypy will check that types are compatible with theoperations being performed, such as checking that a list is being used with the correct indextype.

PyLint: PyLint is a widely used Python static code analyzer that checks code for potential bugsand style issues. It is designed to work with the abstract syntax tree of Python code, and candetect issues such as unused variables, undefined names, and code that is too complex. PyLintalso provides suggestions for how to improve the code.

Flake8: Flake8 is another popular Python static code analyzer that combines the functionality ofthree other Python tools: PyFlakes, McCabe, and pep8. Like PyLint, Flake8 checks code forpotential bugs and style issues, but it also checks for compliance with the PEP 8 style guide forPython code. This makes it a useful tool for enforcing coding standards in Python projects.

Bandit: Bandit is a security-focused Python static code analyzer that checks code for potentialsecurity vulnerabilities. It uses a set of plugins to check for issues such as code that issusceptible to SQL injection, cross-site scripting (XSS), and other common security issues.Bandit is designed to be easy to use, and provides clear, actionable results that can be used toimprove the security of Python code.

Prospector is a Python static code analyzer that combines the capabilities of multiple tools into asingle, easy-to-use package. It can perform linting, style checking, and complexity analysis all inone run. Prospector uses tools such as PyLint, Flake8, and McCabe to analyze the code andprovide recommendations for improvement. Additionally, Prospector can be easily integratedinto other tools, such as code editors or continuous integration platforms, to streamline thedevelopment process. With its combination of functionality and ease of use, Prospector is apopular choice for Python developers looking to improve the quality of their code and probablythe best for us.

This is why I suggest the use should use PyLint for checking style issues and Bandit forchecking security vulnerabilities via Prospector.

Tool Purpose Mypy Type checking PyLint Linting Flake8 Linting, style checking PyFlakes LintingProspector Linting, style checking, complexity analysis




<a name="br2"></a>Above we can see the output for a sample submission for project 1, CS313E.

This is all done through the run\_autograder file within the assignment folders as depicted below.

From the sample tests we open the file and print each line:

A rating is displayed that may correspond to styling points. However, there are limitations andexcessive scrutiny may be applied. Additional, filters may be added to set lesser security.




<a name="br3"></a>Pylint and Bandit are two popular static code analyzers that can be used as autograders. Pylintis a tool that checks for errors in Python code and can also enforce coding standards and bestpractices. Bandit, on the other hand, is a security-focused static code analyzer that detectspotential security vulnerabilities in Python code.

By incorporating both Pylint and Bandit into the autograder, instructors can ensure that studentassignments not only meet coding standards and best practices but also adhere to securityguidelines. This is particularly important for cybersecurity-focused classes or upper division CSelectives where security concerns are paramount.

The run\_autograder file is the main script that runs the autograder and generates the feedbackfor students. By expanding the functionality of this file, instructors can customize the autograderto fit their specific needs and preferences. In addition, the run\_autograder file can serve as atemplate for future autograders and other static code analyzers.

Overall, autograders are valuable tools for both instructors and students in computer scienceand programming-related courses. They can help to improve coding skills, promote bestpractices, and provide timely and consistent feedback.

**Pyreverse**

Pyreverse is an excellent tool that can make learning Python coding a lot easier andcomprehensible for students. It can create visual diagrams, called UML diagrams, that show therelationships between different parts of the code. This can be a big help for students who mightfind coding difficult or overwhelming at first.

For example, if you're just starting out in a programming course, codeassist might have you usePyreverse to generate UML diagrams from your code. This can help you better understand thedifferent concepts, like functions and classes, and how they all fit together.




<a name="br4"></a>However, pyreverse can be expanded to advanced advanced programming courses or projects.As your codebase gets more complex, it can be hard to keep track of everything. Pyreverse canhelp you see the big picture and identify areas that might need some work.

Pyreverse imay also help students compare designs after a project has been submitted andgraded. By creating UML diagrams, instructors may be able to incorporate different structuresand perhaps even understand the methods the students used. It can be used to expand thesocial aspects of CS and created different design documents as in the normal softwaredevelopment cycle.

Pyreverse is a great tool that can make learning and working with Python code more fun andsummarized. Whether you're just starting out or already an experienced coder, Pyreverse canhelp you better understand the code you're working with and collaborate more effectively withyour peers.




<a name="br5"></a>In additon a docker account is being set up to run autograder files faster based off base images.




<a name="br6"></a>**Next steps**

● Integrating the autograder with code assist and perhaps displaying html images instead of pngs, for a clearer photo opened in google chrome

● Expanding the number of code analyzers to bandit and perspective● Finishing docker container and harness issues

● Implement a way for students to download results and pyreverse output● Create model uml diagrams
