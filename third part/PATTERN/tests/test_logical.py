import numpy as np
from models.pair_pattern_net import PairPatternNet
from utils import get_true_class

def run_logical_tests():
    """Тест 1 и 2: Логическая задача"""
    print("=" * 60)
    print("ТЕСТ 1 и 2: Логическая задача")
    print("=" * 60)
    
    X_train = np.array([[7], [14], [11], [13], [2], [4], [6], [9]], dtype=float)
    y_train = np.array([[get_true_class(x[0])] for x in X_train], dtype=float)
    X_test = np.array([[21], [17]], dtype=float)
    y_test = np.array([[get_true_class(x[0])] for x in X_test], dtype=float)
    
    model_binary = PairPatternNet(num_classes=2)
    model_binary.fit(X_train, y_train, max_pairs=1000)
    
    test_acc_binary = model_binary.score(X_test, y_test)
    print(f"\nТест 1 точность: {test_acc_binary:.1%}")
    
    X_new = np.array([[21], [17], [23], [8], [10]], dtype=float)
    true_labels = [get_true_class(x[0]) for x in X_new]
    pred_new = model_binary.predict(X_new)
    correct_count = sum(pred_new[i][0] == true_labels[i] for i in range(5))
    print(f"Тест 2: {correct_count}/5")
    
    return test_acc_binary, correct_count
