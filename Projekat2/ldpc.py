import random
import numpy as np

n = 15
n_minus_k = 9
k = 6
wr = 5
wc = 3
th0 = 0.5
th1 = 0.5
seed = 42

def construct_ldpc_matrix(n, n_minus_k, wr, wc, seed):
    rows_per_group = n_minus_k // wc

    if n_minus_k % wc != 0 or rows_per_group * wr != n:
        raise ValueError("The parameters do not define a regular LDPC matrix")

    matrix = np.zeros((n_minus_k, n), dtype=int)
    generator = random.Random(seed)

    for group in range(wc):
        columns = list(range(n))
        if group > 0:
            generator.shuffle(columns)

        for row_index in range(rows_per_group):
            row = group * rows_per_group + row_index
            start = row_index * wr
            for column in columns[start:start + wr]:
                matrix[row, column] = 1

    return matrix

def calculate_syndrome(matrix, word):
    return np.dot(matrix, word) % 2

def number_to_vector(number, length):
    binary = bin(number)[2:].zfill(length)
    return np.array([int(bit) for bit in binary])

def numbers_by_weight(length, include_zero=True):
    first_number = 0 if include_zero else 1
    numbers = range(first_number, 2 ** length)
    return sorted(numbers, key=lambda number: bin(number).count("1"))

def build_syndrome_table(matrix):
    n = matrix.shape[1]
    table = {}

    for number in numbers_by_weight(n):
        error = number_to_vector(number, n)
        syndrome = tuple(calculate_syndrome(matrix, error))
        if syndrome not in table:
            table[syndrome] = error

    return table

def decode_with_syndrome(matrix, received, table):
    syndrome = tuple(calculate_syndrome(matrix, received))
    corrector = table[syndrome]
    return (received + corrector) % 2

def find_code_distance(matrix):
    n = matrix.shape[1]

    for number in numbers_by_weight(n, include_zero=False):
        word = number_to_vector(number, n)
        if not np.any(calculate_syndrome(matrix, word)):
            return int(np.sum(word)), word

    return 0, np.zeros(n, dtype=int)

def gallager_b_decode(matrix, received, th0=0.5, th1=0.5, max_iterations=50):
    number_of_columns = matrix.shape[1]
    check_neighbors = []
    variable_neighbors = [[] for _ in range(number_of_columns)]

    for row_index, row in enumerate(matrix):
        neighbors = []
        for column, value in enumerate(row):
            if value == 1:
                neighbors.append(column)
                variable_neighbors[column].append(row_index)
        check_neighbors.append(neighbors)

    original = np.array(received)
    current = original.copy()

    if not np.any(calculate_syndrome(matrix, current)):
        return current, True, 0

    for iteration in range(1, max_iterations + 1):
        updated = np.zeros(number_of_columns, dtype=int)

        for column in range(number_of_columns):
            zero_votes = 0
            one_votes = 0

            for row_index in variable_neighbors[column]:
                message = 0
                for neighbor in check_neighbors[row_index]:
                    if neighbor != column:
                        message += current[neighbor]
                message %= 2

                if message == 0:
                    zero_votes += 1
                else:
                    one_votes += 1

            degree = len(variable_neighbors[column])
            if zero_votes >= th0 * degree:
                updated[column] = 0
            elif one_votes >= th1 * degree:
                updated[column] = 1
            else:
                updated[column] = original[column]

        if not np.any(calculate_syndrome(matrix, updated)):
            return updated, True, iteration

        if np.array_equal(updated, current):
            return updated, False, iteration

        current = updated

    return current, False, max_iterations


def find_smallest_gallager_failure(matrix, th0=0.5, th1=0.5):
    n = matrix.shape[1]
    sent = np.zeros(n, dtype=int)

    for number in numbers_by_weight(n, include_zero=False):
        error = number_to_vector(number, n)
        decoded, valid_codeword, iterations = gallager_b_decode(
            matrix, error, th0, th1
        )
        if not np.array_equal(decoded, sent):
            weight = int(np.sum(error))
            return weight, error, decoded, valid_codeword, iterations

    return None

def bits_to_text(bits):
    return "".join(str(bit) for bit in bits)

def main():
    matrix = construct_ldpc_matrix(n, n_minus_k, wr, wc, seed)

    print("Parity-check matrix H:")
    for row in matrix:
        print(" ".join(str(value) for value in row))

    table = build_syndrome_table(matrix)
    print("\nSyndrome table:")
    print("syndrome  corrector")
    for syndrome in sorted(table):
        print(bits_to_text(syndrome), bits_to_text(table[syndrome]))

    distance = find_code_distance(matrix)[0]
    print("\nCode distance:", distance)

    failure = find_smallest_gallager_failure(matrix, th0, th1)
    weight = failure[0]
    error = failure[1]

    print("\nGallager B, thresholds th0 = th1 = 0.5:")
    print("Smallest failing error weight:", weight)
    print("Error:", bits_to_text(error))

if __name__ == "__main__":
    main()