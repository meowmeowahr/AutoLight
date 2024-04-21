def surround_list(input: list[bool], radius=1):
    padded_lst = input.copy()  # Create a copy of the original list
    for i in range(len(input)):
        if input[i]:
            for j in range(1, radius + 1):
                if i - j >= 0:
                    padded_lst[i - j] = 1
                if i + j < len(input):
                    padded_lst[i + j] = 1
    return padded_lst

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)