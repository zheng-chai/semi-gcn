import numpy as np

def onehot(y, c):
    res = np.zeros((len(y), c))
    for i, j in enumerate(y):
        res[i, j] = 1
    return res

def softmax(X):
    exp_x = np.exp(X)
    sum_x = np.sum(exp_x, axis=1).reshape(-1, 1)
    softmax_x = exp_x / sum_x
    return softmax_x

def _loss(X, Y):
    return np.sum(-Y * np.log(X))

def backward(X, Y):
    dX = softmax(X) - Y
    return dX

def main():
    n, c = 4, 3
    X = np.random.random((n, c))
    y = np.random.randint(0, c, (n,))
    Y = onehot(y, c)

    # forward
    softmax_X = softmax(X)
    loss = _loss(softmax_X, Y)

    print(loss)
    # grad
    grad = backward(X, Y)

    # check-grad
    h = 1e-5
    X_copy = np.copy(X)
    check_grad = np.zeros((n, c))
    for i in range(n):
        for j in range(c):
            X_copy[i, j] += h
            loss1 = _loss(softmax(X_copy), Y)
            X_copy[i, j] -= 2 * h
            loss2 = _loss(softmax(X_copy), Y)
            check_grad[i, j] = (loss1 - loss2) / (2*h)
            # recover
            X_copy[i, j] += h

    print(grad)
    print(check_grad)

if __name__ == '__main__':
    main()
