import numpy as np
import time
from models.super_hybrid import SuperHybridNet
from features.hybrid_features import (
    extract_original_features,
    extract_coordinate_features,
    extract_cnn_features
)
from features.nonogram_features import extract_nonogram_features
from utils import load_mnist


def run_super_hybrid_test():
    print("\n" + "=" * 80)
    print("ТЕСТ: СУПЕР-ГИБРИД (CTF только для Оригинального)")
    print("=" * 80)

    # Загрузка
    X_train_raw, y_train_raw, X_test_raw, y_test_raw = load_mnist(10000, 2000)
    
    X_train_2d = X_train_raw.reshape(-1, 28, 28)
    X_test_2d = X_test_raw.reshape(-1, 28, 28)
    X_train_2d = (X_train_2d * 255).astype(np.uint8)
    X_test_2d = (X_test_2d * 255).astype(np.uint8)
    
    # Создаём супер-гибрид
    model = SuperHybridNet(num_classes=10, confidence_threshold=0.15)
    
    # CTF только для Оригинального (остальные - без CTF)
    model._add_ctf_module("Оригинальный (CTF)", extract_original_features, use_crop=True)
    model._add_ppn_module("Координатный", extract_coordinate_features, use_crop=True)
    model._add_ppn_module("CNN-подобный", extract_cnn_features, use_crop=True)
    model._add_ppn_module("Nonogram", extract_nonogram_features, use_crop=True)
    model._add_edit_module("EditDistance")
    
    # Обучение
    print("\n🎯 Обучение...")
    start_time = time.time()
    model.fit(X_train_2d, y_train_raw.reshape(-1, 1), max_pairs=300000, min_support=3)
    print(f"\n⏱ Время: {time.time()-start_time:.1f} сек")
    
    # Предсказание
    print("\n🔮 Предсказание...")
    y_pred = model.predict(X_test_2d, verbose=True)
    
    test_acc = np.mean(y_pred.flatten() == y_test_raw)
    
    print(f"\n📊 РЕЗУЛЬТАТ:")
    print(f"  Тест: {test_acc:.2%}")
    
    model.print_summary()
    
    return test_acc


if __name__ == "__main__":
    run_super_hybrid_test()
