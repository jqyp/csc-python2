from collections import Counter
from itertools import combinations


def shape(m):
    assert m, "map must be not empty"
    return len(m), len(m[0])


def print_map(m, pos):
    for i, row in enumerate(m):
        for j, cell in enumerate(row):
            if (i, j) == pos:
                print('@', end='')
            elif cell:
                print('.', end='')
            else:
                print('#', end='')
        print()


def is_free(m, pos):
    i, j = pos
    n_rows, n_cols = shape(m)
    return i in range(0, n_rows) and j in range(0, n_cols) and m[i][j]


def neighbours(m, pos):
    result = []
    i, j = pos

    diffs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    for i_diff, j_diff in diffs:
        candidate = (i + i_diff, j + j_diff)
        if is_free(m, candidate):
            result.append(candidate)
    return result


def is_exit(m, pos):
    i, j = pos
    n_rows, n_cols = shape(m)

    return (i in {0, n_rows - 1} or j in {0, n_cols - 1}) and m[i][j]


def find_route(m, initial):
    stack = [([], initial)]
    while stack:
        route, pos = stack.pop()
        route.append(pos)
        if is_exit(m, pos):
            return route
        for neighbor in neighbours(m, pos):
            if neighbor not in route:
                stack.append((list(route), neighbor))
    assert False


def escape(m, initial):
    route = find_route(m, initial)
    for pos in route:
        print_map(m, pos)
        print()


def hamming(seq1, seq2):
    assert len(seq1) == len(seq2), (
        f"Sequences are of unequal lengths: {len(seq1)} != {len(seq2)}"
    )
    return sum(ch1 != ch2 for ch1, ch2 in zip(seq1, seq2))


def hba1(path, distance):
    line1, line2 = -1, -1
    min_distance = float('inf')
    with open(path) as file:
        sequences = file.read().splitlines()
        for (i, seq1), (j, seq2) in combinations(enumerate(sequences), 2):
            current_distance = distance(seq1, seq2)
            if current_distance < min_distance:
                min_distance = current_distance
                line1, line2 = i + 1, j + 1
    return line1, line2


def kmers(seq, k):
    return Counter(seq[i:i + k] for i in range(len(seq) - k + 1))


def distance1(seq1, seq2, k=2):
    freqs1 = kmers(seq1, k)
    freqs2 = kmers(seq2, k)
    return sum(
        abs(freqs1[key] - freqs2[key]) for key in freqs1.keys() | freqs2.keys()
    )
