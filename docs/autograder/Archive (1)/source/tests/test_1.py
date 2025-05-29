import unittest
from gradescope_utils.autograder_utils.decorators import weight, visibility, tags
import subprocess
import sys
import difflib

get_tc_num = lambda tc_name: tc_name[tc_name.index('_') + 1:]
TIMEOUT = 10

class TestDiffs(unittest.TestCase):

    
    @classmethod
    def setUpClass(cls):
        '''This is run once before all tests'''
        print("Python version: " + sys.version + "\n")

    def setUp(self):
        '''This is run before each individual test'''
        pass

    def run_cur_test(self, inpt, outpt):
        proc = subprocess.Popen('python3 -u Spiral.py'.split(),
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)
        for line in inpt:
            proc.stdin.write(f'{line.strip()}\n')
            proc.stdin.flush()
        try:
            output = proc.communicate(timeout=TIMEOUT)[0].strip().split('\n')
        except subprocess.TimeoutExpired as e:
            print('Time Limit Exceeded')
        finally:
            proc.kill()

        diff_lines = list(difflib.unified_diff(output, [line.strip() for line in outpt.readlines()], fromfile='actual output', tofile='expected output', n=0))
        inpt.close()
        outpt.close()
        return diff_lines, output
    
    @weight(4.5)
    def test_00(self):
        cur_num = get_tc_num(self.test_00.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))
        
        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Expected Output:')
        print(open(f'a1_test_cases/output{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
        
    @weight(4.5)
    def test_01(self):
        cur_num = get_tc_num(self.test_01.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Expected Output:')
        print(open(f'a1_test_cases/output{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_02(self):
        cur_num = get_tc_num(self.test_02.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_03(self):
        cur_num = get_tc_num(self.test_03.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_04(self):
        cur_num = get_tc_num(self.test_04.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_05(self):
        cur_num = get_tc_num(self.test_05.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_06(self):
        cur_num = get_tc_num(self.test_06.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_07(self):
        cur_num = get_tc_num(self.test_07.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))
        
        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_08(self):
        cur_num = get_tc_num(self.test_08.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))
        
        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_09(self):
        cur_num = get_tc_num(self.test_09.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_010(self):
        cur_num = get_tc_num(self.test_010.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_011(self):
        cur_num = get_tc_num(self.test_011.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_012(self):
        cur_num = get_tc_num(self.test_012.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_013(self):
        cur_num = get_tc_num(self.test_013.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_014(self):
        cur_num = get_tc_num(self.test_014.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))
        if len(diff_lines) > 0:
            for line in diff_lines:
                print(line)
        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_015(self):
        cur_num = get_tc_num(self.test_015.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_016(self):
        cur_num = get_tc_num(self.test_016.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_017(self):
        cur_num = get_tc_num(self.test_017.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)
    
    @weight(4.5)
    def test_018(self):
        cur_num = get_tc_num(self.test_018.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)

    @weight(4.5)
    def test_019(self):
        cur_num = get_tc_num(self.test_019.__name__)
        diff_lines, output = self.run_cur_test(open(f'a1_test_cases/input{cur_num}.txt', 'r'), open(f'a1_test_cases/output{cur_num}.txt', 'r'))

        print('Input:')
        print(open(f'a1_test_cases/input{cur_num}.txt', 'r').read())
        print()
        print('Your Output:')
        print('\n'.join(output))

        self.assertEqual(len(diff_lines), 0)


