"""
DNA
"""


def longest_subsequence(string_1, string_2):
    """
    # Input: string_1 and string_2 are two strings that represent strands of DNA
    # Output: returns a sorted list of substrings that are the longest
    #         common subsequence. The list is empty if there are no
    #         common subsequences.
    """
    subsequences = []
    for i in range(0, len(string_1) - 1):
        for j in range(i + 1, len(string_1)):
            current_subsequence = string_1[i:j+1]
            if current_subsequence in string_2 and current_subsequence not in subsequences:
                if not subsequences or len(current_subsequence) > len(subsequences[0]):
                    subsequences = [current_subsequence]
                elif len(current_subsequence) == len(subsequences[0]):
                    subsequences += [current_subsequence]

    subsequences.sort()
    return subsequences


def main():
    """
    This main function reads the data input files and
    prints to the standard output
    """

    # read the data
    # number of lines
    n_lines = int(input())

    # for each pair
    for _ in range(0, n_lines):
        str_1 = input()
        str_2 = input()

        # call longest_subsequence
        subsequences = longest_subsequence(str_1, str_2)

        # write out result(s)
        if not subsequences:
            print("No Common Sequence Found")

        for subsequence in subsequences:
            print(f"{subsequence}")

        # insert blank line
        print()


if __name__ == "__main__":
    main()
