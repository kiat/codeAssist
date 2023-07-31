#  File: Spiral.py

#  Description:

#  Student Name: Lawrence Park

#  Student UT EID: lp28245

#  Course Name: CS 313E

#  Unique Number: 52020

#  Date Created: 1/13/2023

#  Date Last Modified: 1/23/2023

# Input: n is an odd integer between 1 and 100
# Output: returns a 2-D list representing a spiral
#         if n is even add one to n

def create_spiral(n):
    n = int(n)
    if n % 2 == 0: 
      n += 1
  
    spiral_array = [[0]*n for i in range(0,n)]

    #start with the highest number in the spiral, and the index of highest number in spiral would be [0][n-1]
    #variable will be used to locate the current number on the spiral
    row = 0
    column = n-1

    #variables created so the loop does not go to columns/rows of the array that is already filled out
    start_column = 0
    end_column = n-1
    end_row = n - 1
    start_row = 0

    #loop through odd squared numbers / start off with the odd squared numbers
    for dist in range(n,-1,-2):
        #start with the highest number and repeat going left, down, right, up
        start_number = dist ** 2
        #left
        if dist > dist - 1 and dist > 1:
            for left in range(0,dist):
                spiral_array[row][column] = start_number
                start_number -= 1
                if column > start_column:
                    column -= 1
        start_number += 1
        #down
        if dist > dist-1:
            for down in range(0, dist):
                spiral_array[row][column] = start_number
                start_number -= 1
                if row < end_row:
                    row += 1
        start_number += 1
        #right
        if dist > dist - 1:
            for right in range(0, dist):
                spiral_array[row][column] = start_number
                start_number -= 1
                if column < end_column:
                    column += 1
        start_number += 1
        #up
        if dist > dist - 1:
            for up in range(0, dist-1):
                spiral_array[row][column] = start_number
                start_number -= 1
                if row > start_row:
                    row -= 1
            #allows the loop to start at the position where the odd-squared numbers are located
            row += 1
            column -= 1
            #allows the loop to not go to columns/rows of the array that is already filled out
            start_column += 1
            end_column -= 1
            end_row -= 1
            start_row += 1
    #hardcode the middle of the array to be 1
    spiral_array[n//2][n//2] = 1
    return spiral_array
    
# Input: spiral is a 2-D list and n is an integer
# Output: returns an integer that is the sum of the
#         numbers adjacent to n in the spiral
#         if n is outside the range return 0
def sum_adjacent_numbers(spiral, n):
  n  = int(n)
  if n < 1 or n > n ** 2: return 0
    
  for i in range(0, len(spiral)):
    if n in spiral[i]:
      #c and r used to find column/row of "n", which will help figure out numbers adjacent to "n"
      c = spiral[i].index(n)
      r = i
  sum_num = 0
  if r > 0:
    sum_num += spiral[r-1][c]
    #diagnoal_right_up_number
    if c < len(spiral) - 1: sum_num += spiral[r-1][c+1]
    #diagonal_left_up
    if c > 0: sum_num += spiral[r-1][c-1]

  if r < len(spiral)-1:
    sum_num += spiral[r+1][c]
    #diagonal_right_down
    if c < len(spiral) - 1: sum_num += spiral[r+1][c+1]
    #diagonal_left_down
    if c > 0: sum_num += spiral[r+1][c-1]
  if c > 0: sum_num += spiral[r][c-1]
  if c < len(spiral) - 1: sum_num += spiral[r][c+1]
  
  return sum_num

def main():
  import sys
  spiral_reading = sys.stdin.read()
  spiral_list = spiral_reading.split("\n")
  spiral_arbitrary_value = spiral_list[0]
  spiral_list.pop(0)

  space = "" #there is a "" in spiral_list; remove "" to successfully iterate through list
  if space in spiral_list:
    spiral_list.remove("")

  for i in spiral_list:
    spiral_pattern = create_spiral(spiral_arbitrary_value)
    print(sum_adjacent_numbers(spiral_pattern,i))

if __name__ == "__main__":
    main()