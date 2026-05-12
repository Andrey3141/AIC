import numpy as np
import gzip
import pickle
import urllib.request
import os

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def get_true_class(x):
    if (x % 7 == 0 and x % 3 != 0):
        return 1
    if (is_prime(x) and x > 10):
        return 1
    return 0

def load_mnist(n_train=30000, n_test=5000):
    """Загрузка MNIST с увеличенной выборкой (30k train, 5k test)"""
    mnist_file = 'mnist.pkl.gz'
    if not os.path.exists(mnist_file):
        print("📥 Скачиваем MNIST...")
        urllib.request.urlretrieve(
            'https://github.com/mnielsen/neural-networks-and-deep-learning/raw/master/data/mnist.pkl.gz', 
            mnist_file
        )
    
    with gzip.open(mnist_file, 'rb') as f:
        train_set, valid_set, test_set = pickle.load(f, encoding='latin1')
    
    # Объединяем train и valid для максимальной выборки
    X_full = np.vstack([train_set[0], valid_set[0]])
    y_full = np.hstack([train_set[1], valid_set[1]])
    
    n_train = min(n_train, len(X_full))
    n_test = min(n_test, len(test_set[0]))
    
    return (X_full[:n_train], y_full[:n_train],
            test_set[0][:n_test], test_set[1][:n_test])
