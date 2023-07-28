#  File: Spiral.py

#  Description: Assignment 1 - Infinite Spiral of Numbers

#  Student Name: Victor Nguyen

#  Student UT EID: vbn88

#  Course Name: CS 313E

#  Unique Number: 52025

#  Date Created: January 10, 2023

#  Date Last Modified: January 10, 2023

import sys


# Input: n is an odd integer between 1 and 100
# Output: returns a 2-D list representing a spiral
#         if n is even add one to n
def create_spiral(n):
    """
    Creates a 2-D list containing a clockwise spiral starting at the center at value 1 and going outward, incrementing
    values by 1. The spiral's side length is n if n is odd and n + 1 if n is even.

    :param n: Proposed side length of the spiral
    :type n: int
    :return: 2-D list containing the outward spiral
    :rtype: list
    """
    # Add 1 to n if it is even to make it odd
    if n % 2 == 0:
        n += 1
    # Create 2-D list
    spiral = [[0 for j in range(n)] for i in range(n)]
    # Set directions to add to the current position and an index for it
    dirs = [[0, 1, 0, -1], [1, 0, -1, 0]]
    d = 0
    # Set starting position at center and starting value at 1
    r = c = n // 2
    curr = 1
    # Iterate through the last value
    while curr <= n * n:
        # Set value
        spiral[r][c] = curr
        # Check if the direction should be changed and change it if needed
        d_next = (d + 1) % 4
        if curr != 1 and spiral[r + dirs[0][d_next]][c + dirs[1][d_next]] == 0:
            d = d_next
        # Move to the next position
        r += dirs[0][d]
        c += dirs[1][d]
        # Increment value
        curr += 1
    return spiral


# Input: spiral is a 2-D list and n is an integer
# Output: returns an integer that is the sum of the
#         numbers adjacent to n in the spiral
#         if n is outside the range return 0
def sum_adjacent_numbers(spiral, n):
    """
    Returns the sum of numbers adjacent (including diagonals) to a value in a spiral, not including this value. If n is
    outside the range, the function returns 0.

    :param spiral: Spiral to be searched
    :type spiral: list
    :param n: Value to find the adjacent sum
    :type n: int
    :return: Sum of numbers adjacent (including diagonals) to the value in the spiral, not including the value
    :rtype: int
    """
    dim = len(spiral)
    # Return 0 if n is out of the range
    if n <= 0 or n > dim * dim:
        return 0
    # Iterate through every position in the spiral
    for r in range(dim):
        for c in range(dim):
            # Check if the current position is the location of the wanted value
            if spiral[r][c] == n:
                sum_adj = 0
                # Loop through adjacent (including diagonals) positions
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        # Exclude the wanted value and account for Python's negative index wrapping
                        if (dr, dc) == (0, 0) or r + dr < 0 or c + dc < 0:
                            continue
                        # Attempt to add the adjacent value to the sum, will do nothing if out of bounds
                        try:
                            sum_adj += spiral[r + dr][c + dc]
                        except:
                            pass
                # No need to continue searching
                return sum_adj


def main():
    # Read in data
    data = sys.stdin.read().split('\n')
    # Remove blank lines at the end of the file
    while not data[-1]:
        data = data[:len(data) - 1]
    # Create the spiral
    n = int(data[0])
    spiral = create_spiral(n)
    # Print the sum of adjacent numbers for the rest of the data
    for i in range(1, len(data)):
        print(sum_adjacent_numbers(spiral, int(data[i])))


if __name__ == "__main__":
    main()
