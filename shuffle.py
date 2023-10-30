from random import randint

# TODO:
#   - either prove the algorithm's correctness or give an example when it's wrong


def check(arr: list):
    old = []
    i = 0
    while True and len(arr) > 0:
        if i in old:
            break
        old.append(i)
        i = arr[i]
    return len(old) == len(arr)


def shuffle(names: list):
    n = len(names)
    L = [x for x in range(n)]
    M = list(L)
    for i in range(n - 1):
        k = randint(i + 1, n - 1)
        M[i], M[k] = M[k], M[i]
    if check(M):
        print('OK', end=' ')
        for x in range(n):
            names[M[x]] = str(names[M[x]])
            M[x] = names[M[x]]
        return dict(zip(names, M))
    print()
    print(L)
    return shuffle(n)


if __name__ == '__main__':
    print(shuffle(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o']))
    for i in range(100000 * 0):
        shuffle([x for x in range(100)])
