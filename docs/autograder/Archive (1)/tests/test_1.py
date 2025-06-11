import unittest
from gradescope_utils.autograder_utils.decorators import weight, tags
import subprocess
import sys
import os
import pylint
from pylint import epylint as lint
from pylint.reporters.text import TextReporter
from pathlib import Path
import webbrowser
# import cv2


class WritableObject(object):
    def __init__(self):
        self.content = []
    def write(self, st):
        self.content.append(st)
    def read(self):
        return self.content
class TestDiffs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        '''This is run once before all tests'''
        print("Python version: " + sys.version + "\n")

    def setUp(self):
        '''This is run before each individual test'''
        pass

    @weight(100)
    def test_1(self):
        expected, output = run_test_case('test_cases/test_1.in', 'test_cases/test_1.out')
        self.assertEqual(output, expected)

    
    @weight(5)
    def test_2(self):
        """extra credit"""
        expected, output = run_test_case('test_cases/test_ec.in', 'test_cases/test_ec.out')
        script_name = 'DNA.py'     #example test.py
        output_file = 'pylint.txt' #example test.txt
        print(Path('./pylint.txt').is_file())
        with open('pylint.txt', "r") as fileToProcess:
            for line in fileToProcess:
                print(str(line))
        #img = Image.open("./classes.png")
        # cv2.imshow("displayh", "./classes.png")

        #img.show()
        # to open/create a new html file in the write mode

    # 1st method how to open html files in chrome using

    
        

 


    @weight(0)
    def possible_errors(self):
        # '''possible errors/style issues'''
        # ARGS = ["-r","n"]  # put your own here "--rcfile=rcpylint"
        # pylint_output = WritableObject()
        
        # print(Run([ 'python -u DNA.py']+ARGS, exit=False))
        # # os.system('pyreverse -o html python3 -u DNA.py')
        # # print(open(f'{classes}.html', 'r').read())
        # print('hello world')   
        script_name = 'DNA.py'     #example test.py
        output_file = 'pylint.txt' #example test.txt
        param1 = 'python -m pylint --max-line-length=400 -d relative-beyond-top-level,wildcard-import --msg-template="{abspath}||{path}||{symbol}||{msg_id}||{line}||{column}||{msg}" --reports=y '+ script_name
        param2 = ' > '+output_file
        param = param1 + param2
        os.system(param)
        path = os.getcwd()
        print(path)
        print(Path(path+'pylint.txt').is_file())
        f = open(path+'pylint.txt', 'r')
        print(f.read())



        

def run_test_case(test_file, output_file):
    # start the subprocess
    proc = subprocess.Popen('python3 -u DNA.py'.split(),
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)

    # output the test case
    in_file = open(test_file, 'r')
    for line in in_file:
        proc.stdin.write(line)
        proc.stdin.flush()
    in_file.close()
    proc.stdin.write('\n')
    proc.stdin.flush()
    # close stdin
    proc.stdin.close()
    
    # read the submitted output
    output = proc.stdout.read()
    proc.terminate()

    # get the expected output
    expected_file = open(output_file, 'r')
    expected = expected_file.read()
    expected_file.close()

    # return the expected and actual output
    return output.strip(), expected.strip()