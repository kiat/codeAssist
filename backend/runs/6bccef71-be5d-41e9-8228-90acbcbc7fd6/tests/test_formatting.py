# Main documentation is here 
# https://docs.python.org/3/library/unittest.html 

# Run it using the following command. 
# TEST_FILENAME="YOURFILE.py" python3 -m unittest pylint_test.py
# 
# Run in Gradescope like the following 
# in run_autograder 
# FILENAME="/autograder/source/YOURFILE.py" python3 run_tests.py


# https://peps.python.org/pep-0008/


import unittest
import os
from io import StringIO

from gradescope_utils.autograder_utils.decorators import weight, visibility, tags, partial_credit


# from pylint import epylint as lint
from pylint.lint import Run
from pylint.reporters.text import TextReporter

# from pylint import run_pylint

# According to pylint's man page there are 5 different classes of errors:

# (C) convention, for programming standard violation
# (R) refactor, for bad code smell
# (W) warning, for python specific problems
# (E) error, for probable bugs in the code
# (F) fatal, if an error occurred which prevented pylint from doing further processing.


# https://docs.pylint.org/output.html

# The message type can be:

# [R]efactor for a “good practice” metric violation
# [C]onvention for coding standard violation
# [W]arning for stylistic problems, or minor programming issues
# [E]rror for important programming issues (i.e. most probably bug)
# [F]atal for errors which prevented further processing

class Test1(unittest.TestCase):

    FILENAME = os.environ["FILENAME"]
    # FILENAME = "spider.py"

    def setUp(self):        
        self.pylint_output = StringIO()  # Custom open stream
        self.reporter = TextReporter(self.pylint_output)

    @weight(4)
    @partial_credit(4)
    def test_formating_errors_and_fatal(self, set_score=None):
        print("\n\nChecking for ...\n[E]rror for important programming issues (i.e. most probably bug)")
        print("[F]atal for errors which prevented further processing")

        results = Run(["--disable=C,R,W ", self.FILENAME], reporter=self.reporter, exit=False)

        print(self.pylint_output.getvalue())
        score = round(results.linter.stats.global_note, 2)
        print("This is ", score/2, " out of 5 point of this Formatting Test.")
        
        set_score(score/2.5)
        self.assertAlmostEqual(score/2.5, 4.0)
        
        

    @weight(4)
    @partial_credit(4)
    def test_formating_convention(self, set_score=None):
        print("\n\nChecking for ...\n [C]onvention for coding standard violation")

        results = Run(["--disable=R,W,E,F ", self.FILENAME], reporter=self.reporter, exit=False)

        print(self.pylint_output.getvalue())
        score = round(results.linter.stats.global_note, 2)
        print("This is ", score/2.5, " out of 4 point of this Formatting Test.")
        
        set_score(score/2.5)
        self.assertAlmostEqual(score/2.5, 4.0)

    @weight(1)
    @partial_credit(1)
    def test_formating_refactor(self, set_score=None):
        print("\n\nChecking for ...\n[R]efactor for a “good practice” metric violation")

        results = Run(["--disable=W,C,E,F ", self.FILENAME], reporter=self.reporter, exit=False)

        print(self.pylint_output.getvalue())

        score = round(results.linter.stats.global_note, 2)        
        print("This is ", score/10, " out of 1 point of this Formatting Test.")
      
        
        set_score(score/10)
        self.assertAlmostEqual(score/10, 1.0)

    @weight(1)
    @partial_credit(1)
    def test_formating__warnings(self, set_score=None):
        print("\n\nChecking for ...\n(W) warning, for python specific problems")

        results = Run(["--disable=R,C,E,F ", self.FILENAME], reporter=self.reporter, exit=False)

        print(self.pylint_output.getvalue())

        score = round(results.linter.stats.global_note, 2)        
        print("This is ", score/10, " out of 1 point of this Formatting Test.")
      
        
        set_score(score/10)
        self.assertAlmostEqual(score/10, 1.0)