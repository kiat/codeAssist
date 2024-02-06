"""
    Input: tuples_list is an unsorted list of tuples denoting intervals
    Output: a list of merged tuples sorted by the lower number of the
    interval
"""
import sys


def merge_tuples (tuples_list):
    """Sort tuples in list."""

    tuples_list.sort()
    new_list = []

    # From tuples to 2D-list.
    for interval in tuples_list:
        tuple_to_list = list(interval)
        new_list.append(tuple_to_list)

    merged_list = []
    start = 0
    end = 1

    # Merge intervals.
    for interval in new_list:
        if not merged_list:
            merged_list.append(interval)
        elif interval[start] <= merged_list[-1][end] and merged_list[-1][end] >= interval[end]:
            continue
        elif interval[start] <= merged_list[-1][end] and merged_list[-1][end] < interval[end]:
            merged_list[-1][end] = interval[end]
        else:
            merged_list.append(interval)

    new_merged_list = []
    # From 2D-list to tuples.
    for interval in merged_list:
        list_to_tuple = tuple(interval)
        new_merged_list.append(list_to_tuple)

    return new_merged_list

def sort_by_interval_size (tuples_list):
    """
    Input: tuples_list is a list of tuples of denoting intervals
    Output: a list of tuples sorted by ascending order of the
    size of the interval if two intervals have the size then it will sort by the
    lower number in the interval
    """
    tuples_list.sort()

    # Creates a list with size values.
    size_list = []
    for element in tuples_list:
        size_list.append(element[1] - element[0])

    # Creates a new list with tuple values sorted by size.
    sorted_list = []
    for _ in range(0, len(tuples_list)):
        index_of_min = size_list.index(min(size_list))
        sorted_list.append(tuples_list[index_of_min])
        size_list.remove(min(size_list))
        tuples_list.remove(tuples_list[index_of_min])

    return sorted_list


def main():
    """
    Open file intervals.in and read the data and create a list of tuples
    """
    sys.stdin.readline()

    tup_list = []
    tup_list = sys.stdin.readlines()

    tuples_list = []
    for m_tuple in tup_list:
        tup = m_tuple.split()
        tuples_list.append(tuple((int(tup[0]), int(tup[1]))))

    # merge the list of tuples
    merged = merge_tuples(tuples_list)

    # sort the list of tuples according to the size of the interval
    sorted_merge = sort_by_interval_size(merge_tuples(tuples_list))

    # write the output list of tuples from the two functions
    print(merged)
    print(sorted_merge)

if __name__ == "__main__":
    main()
