from math import log2


def byte_entropy(data):
    if len(data) == 0:
        return 0.0

    counts = [0] * 256

    for byte in data:
        counts[byte] += 1

    entropy = 0.0
    data_size = len(data)

    for count in counts:
        if count > 0:
            probability = count / data_size
            entropy -= probability * log2(probability)

    return entropy
