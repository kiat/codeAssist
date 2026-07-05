"""
Input: dim is a positive odd integer
Output: function returns a 2-D list of integers arranged in a spiral
"""

import math


def create_spiral(dim):
    """Creates a Spiral given a dimension for the spiral dimeter"""
    lst = [[0 for _ in range(dim)] for _ in range(dim)]

    x_loc = dim - 1
    y_loc = 0
    ctr = dim * dim

    lower_idx = 0
    upper_idx = dim - 1

    while ctr > 0:
        lst[y_loc][x_loc] = ctr

        if get_curr_square(ctr - 1) != get_curr_square(ctr):  # square transition
            x_loc -= 1
            lower_idx += 1
            upper_idx -= 1
        else:
            x_loc, y_loc = traverse_square(x_loc, y_loc, lower_idx, upper_idx)

        ctr -= 1

    return lst


def get_curr_square(ctr_val):
    """Calculates the Square value. """
    curr_square = math.ceil(math.sqrt(ctr_val))

    return curr_square if curr_square % 2 != 0 else curr_square + 1


def traverse_square(x_loc, y_loc, lower_idx, upper_idx):
    """Traverse on the the Spiral on all corners. """
    # At the top of current square but not the top left
    if y_loc == lower_idx and x_loc != lower_idx:
        x_loc -= 1
    # at the left of the current square but not the bottom left
    elif x_loc == lower_idx and y_loc != upper_idx:
        y_loc += 1
    # at the bottom of the current square but not the bottom right
    elif y_loc == upper_idx and x_loc != upper_idx:
        x_loc += 1
    elif x_loc == upper_idx and y_loc != lower_idx:
        y_loc -= 1

    return x_loc, y_loc


def sum_sub_grid(grid, val):
    """
    Input: grid a 2-D list containing a spiral of numbers
           val is a number within the range of numbers in
           the grid
    Output:
    sum_sub_grid returns the sum of the numbers (including val)
    surrounding the parameter val in the grid
    if val is out of bounds, returns 0
    """
    dim = len(grid)
    if not 1 <= val <= dim ** 2:
        return 0

    grid_square = get_curr_square(val)

    lower_idx = (dim - grid_square)//2
    upper_idx = (dim - 1) - lower_idx

    y_loc = lower_idx
    x_loc = lower_idx

    while grid[y_loc][x_loc] != val:
        x_loc, y_loc = traverse_square(x_loc, y_loc, lower_idx, upper_idx)

    tot = 0
    for h_y in range(y_loc - 1, y_loc + 2):
        for h_x in range(x_loc - 1, x_loc + 2):
            if 0 <= h_y < dim and 0 <= h_x < dim:  # valid index
                tot += grid[h_y][h_x]

    return tot - grid[y_loc][x_loc]


def mat_to_str(grid):
    """Matrix to String Conversion."""
    my_string = [[str(e) for e in row] for row in grid]

    lens = [max(map(len, col)) for col in zip(*my_string)]

    # fmt = '  '.join('{{:{}}}'.format(x) for x in lens)
    fmt = '  '.join(f'{{:{x}}}' for x in lens)

    table = [fmt.format(*row) for row in my_string]
    return '\n'.join(table)


def main():
    """
    A Main Function to read the data from input,
    run the program and print to the standard output.
    """

    # read the dimension of the grid and value from input file
    dim = int(input())

    # test that dimension is odd
    if dim % 2 == 0:
        dim += 1

    # create a 2-D list representing the spiral
    mat = create_spiral(dim)

    while True:
        try:
            sum_val = int(input())

            # find sum of adjacent terms
            adj_sum = sum_sub_grid(mat, sum_val)

            # print the sum
            print(adj_sum)
        except EOFError:
            break


if __name__ == "__main__":
    main()
