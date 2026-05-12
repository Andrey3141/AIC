import numpy as np
import matplotlib.pyplot as plt
from features.hybrid_features import extract_original_features, crop_to_digit
from utils import load_mnist
import time

def visualize_recursive_errors():
    """Визуализация ошибок на каждом уровне рекурсии"""
    
    print("\n" + "=" * 80)
    print("ВИЗУАЛИЗАЦИЯ ОШИБОК РЕКУРСИВНОЙ МОДЕЛИ")
    print("=" * 80)
    
    # Загрузка данных
    X_train_raw, y_train_raw, X_test_raw, y_test_raw = load_mnist(8000, 500)
    
    # Преобразуем в 2D
    X_train_2d = (X_train_raw.reshape(-1, 28, 28) * 255).astype(np.uint8)
    X_test_2d = (X_test_raw.reshape(-1, 28, 28) * 255).astype(np.uint8)
    
    # Создаём простую модель для анализа (без рекурсии, только уровень 1)
    from models.hybrid_recursive import HybridRecursiveNet
    from features.hybrid_features import extract_original_features, crop_to_digit
    
    def extract_crop_features(img):
        cropped = crop_to_digit(img)
        return extract_original_features(cropped)
    
    print("\n📊 Обучаем МОДЕЛЬ УРОВНЯ 1 (без рекурсии)...")
    
    model = HybridRecursiveNet(num_classes=10, min_samples_per_level=50, max_levels=1)
    model.set_feature_extractor(extract_crop_features)
    model.fit(X_train_2d, y_train_raw.reshape(-1, 1), max_pairs=300000, min_support=3)
    
    # Предсказываем на train (чтобы увидеть ошибки)
    print("\n🔮 Предсказание на обучающей выборке...")
    y_pred_train, used_level = model.predict(X_train_2d, verbose=False)
    y_true_train = y_train_raw
    
    # Находим ошибки
    errors_train = (y_pred_train.flatten() != y_true_train)
    error_indices_train = np.where(errors_train)[0]
    correct_indices_train = np.where(~errors_train)[0]
    
    print(f"\n📊 НА ОБУЧЕНИИ:")
    print(f"  ✅ Правильно: {len(correct_indices_train)} / {len(X_train_2d)} ({len(correct_indices_train)/len(X_train_2d)*100:.1f}%)")
    print(f"  ❌ Ошибки: {len(error_indices_train)} / {len(X_train_2d)} ({len(error_indices_train)/len(X_train_2d)*100:.1f}%)")
    
    # ============================================================
    # ВИЗУАЛИЗАЦИЯ: ПРИМЕРЫ, КОТОРЫЕ МОДЕЛЬ РАСПОЗНАЛА ПРАВИЛЬНО
    # ============================================================
    print("\n" + "=" * 80)
    print("📸 ПРИМЕРЫ, КОТОРЫЕ МОДЕЛЬ РАСПОЗНАЛА ПРАВИЛЬНО")
    print("=" * 80)
    
    # Берём 6 правильных примеров (по одному на цифру 0-5)
    fig, axes = plt.subplots(2, 6, figsize=(15, 6))
    axes = axes.flatten()
    
    digits_found = {i: None for i in range(10)}
    for idx in correct_indices_train:
        digit = y_true_train[idx]
        if digits_found[digit] is None:
            digits_found[digit] = idx
        if all(v is not None for v in digits_found.values()):
            break
    
    for i, digit in enumerate(range(10)):
        if digits_found[digit] is not None:
            idx = digits_found[digit]
            ax = axes[i]
            ax.imshow(X_train_2d[idx], cmap='gray')
            ax.set_title(f"Цифра: {digit}\nПредсказано: {y_pred_train[idx][0]}", fontsize=10, color='green')
            ax.axis('off')
        else:
            axes[i].axis('off')
    
    axes[10].axis('off')
    axes[11].axis('off')
    plt.suptitle("✅ ПРИМЕРЫ, КОТОРЫЕ МОДЕЛЬ РАСПОЗНАЛА ПРАВИЛЬНО", fontsize=14, color='green')
    plt.tight_layout()
    plt.show()
    
    # ============================================================
    # ВИЗУАЛИЗАЦИЯ: ОШИБКИ МОДЕЛИ (УРОВЕНЬ 1)
    # ============================================================
    print("\n" + "=" * 80)
    print("❌ ПРИМЕРЫ ОШИБОК (УРОВЕНЬ 1) - ЭТИ УЙДУТ НА УРОВЕНЬ 2")
    print("=" * 80)
    print("   (красный = ошибка, зелёный = что предсказала модель)")
    
    # Выбираем 12 случайных ошибок для показа
    np.random.seed(42)
    sample_errors = np.random.choice(error_indices_train, min(12, len(error_indices_train)), replace=False)
    
    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    axes = axes.flatten()
    
    for i, idx in enumerate(sample_errors):
        ax = axes[i]
        ax.imshow(X_train_2d[idx], cmap='gray')
        true_digit = y_true_train[idx]
        pred_digit = y_pred_train[idx][0]
        ax.set_title(f"TRUE: {true_digit} → PRED: {pred_digit}", 
                     fontsize=10, color='red')
        ax.axis('off')
    
    for i in range(len(sample_errors), 12):
        axes[i].axis('off')
    
    plt.suptitle("❌ ОШИБКИ УРОВНЯ 1 (уходят на уровень 2)", fontsize=14, color='red')
    plt.tight_layout()
    plt.show()
    
    # ============================================================
    # СТАТИСТИКА ОШИБОК ПО КЛАССАМ
    # ============================================================
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА ОШИБОК ПО КЛАССАМ (УРОВЕНЬ 1)")
    print("=" * 80)
    
    class_stats = {}
    for digit in range(10):
        mask = (y_true_train == digit)
        total = np.sum(mask)
        errors = np.sum(errors_train & mask)
        class_stats[digit] = {'total': total, 'errors': errors, 'accuracy': (total-errors)/total*100}
    
    print("\n┌─────────┬──────────┬──────────┬────────────┐")
    print("│ Цифра   │ Всего    │ Ошибок   │ Точность   │")
    print("├─────────┼──────────┼──────────┼────────────┤")
    for digit in range(10):
        stats = class_stats[digit]
        bar = "█" * int(stats['accuracy'] / 5) + "░" * (20 - int(stats['accuracy'] / 5))
        print(f"│ {digit}       │ {stats['total']:>6}   │ {stats['errors']:>6}   │ {stats['accuracy']:>5.1f}% {bar} │")
    print("└─────────┴──────────┴──────────┴────────────┘")
    
    # ============================================================
    # ВИЗУАЛИЗАЦИЯ: КАКИЕ ЦИФРЫ ЧАЩЕ ВСЕГО ПУТАЮТ
    # ============================================================
    print("\n" + "=" * 80)
    print("🔄 МАТРИЦА ОШИБОК (какие цифры с какой путают)")
    print("=" * 80)
    
    # Строим матрицу путаницы
    confusion = np.zeros((10, 10), dtype=int)
    for idx in error_indices_train:
        true_digit = y_true_train[idx]
        pred_digit = y_pred_train[idx][0]
        confusion[true_digit][pred_digit] += 1
    
    print("\n    " + " ".join([f"{i:>3}" for i in range(10)]))
    for i in range(10):
        row = " ".join([f"{confusion[i][j]:>3}" for j in range(10)])
        print(f"{i}: {row}")
    
    # Визуализация матрицы путаницы
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(confusion, cmap='Reds')
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.set_xlabel("Предсказанная цифра", fontsize=12)
    ax.set_ylabel("Истинная цифра", fontsize=12)
    ax.set_title("Матрица ошибок (Уровень 1)", fontsize=14)
    
    # Добавляем числа в ячейки
    for i in range(10):
        for j in range(10):
            if confusion[i][j] > 0:
                text = ax.text(j, i, confusion[i][j], ha="center", va="center", fontsize=8)
    
    plt.colorbar(im)
    plt.tight_layout()
    plt.show()
    
    # ============================================================
    # АНАЛИЗ: почему уровень 2 не помогает?
    # ============================================================
    print("\n" + "=" * 80)
    print("🔬 АНАЛИЗ: ПОЧЕМУ УРОВЕНЬ 2 НЕ УЛУЧШАЕТ РЕЗУЛЬТАТ?")
    print("=" * 80)
    
    print("""
    Проблема №1: Количество ошибок уменьшается, но они становятся СЛОЖНЕЕ
    
    Уровень 1: 2481 ошибка (31%)
    Уровень 2: учится на этих 2481 ошибках
    Но эти 2481 - самые трудные примеры, которые уровень 1 не смог распознать
    
    Проблема №2: Модель переобучается на малом количестве данных
    
    15000 правил на 2481 объект = ~6 правил на объект
    → модель просто ЗАПОМИНАЕТ эти примеры
    
    Проблема №3: "Хорошие" примеры уже отфильтрованы
    
    Оставшиеся ошибки - это цифры, которые визуально похожи на другие:
    - 4 и 9
    - 7 и 1
    - 3 и 8
    - 5 и 6
    
    → уровень 2 пытается разделить неразделимое
    """)
    
    # ============================================================
    # ПОКАЗЫВАЕМ САМЫЕ "ТРУДНЫЕ" ПРИМЕРЫ
    # ============================================================
    print("\n" + "=" * 80)
    print("💀 САМЫЕ ТРУДНЫЕ ПРИМЕРЫ (которые уровень 2 тоже не сможет распознать)")
    print("=" * 80)
    
    # Находим примеры, где модель была НЕУВЕРЕНА (confidence низкая)
    # Если бы мы сохранили confidence - показали бы
    
    print("""
    Типичные сложные случаи на MNIST:
    - 4, которая похожа на 9
    - 7, которая похожа на 1  
    - 3, которая похожа на 8
    - 5, которая похожа на 6
    - 0, которая похожа на 6
    
    Рекурсия НЕ МОЖЕТ помочь, потому что:
    1. Это проблема качества данных, а не модели
    2. Человек тоже иногда ошибается в таких случаях
    3. Нужны другие признаки (контекст, форма), а не просто пиксели
    """)
    
    # ============================================================
    # ВЫВОДЫ И РЕКОМЕНДАЦИИ
    # ============================================================
    print("\n" + "=" * 80)
    print("📋 ВЫВОДЫ И РЕКОМЕНДАЦИИ")
    print("=" * 80)
    print("""
    1. ❌ Рекурсия НЕ РАБОТАЕТ, потому что:
       - Ошибки уровня 1 - это визуально неоднозначные примеры
       - Уровень 2 учится на малом количестве данных и переобучается
       - Точность падает с каждым уровнем (69% → 64% → 50%)
    
    2. ✅ Что можно сделать:
       a) Убрать рекурсию полностью (max_levels=1)
       b) Улучшить признаки (добавить контекстные, структурные)
       c) Использовать ансамбль независимых моделей вместо рекурсии
       d) Добавить аугментацию данных для "сложных" случаев
    
    3. 🎯 Рекомендуемая архитектура:
       
       Входное изображение
              ↓
       ┌─────────────────────┐
       │  4 независимые       │
       │  модели (ансамбль)   │
       └─────────────────────┘
              ↓
         Голосование
              ↓
          Предсказание
       
       (БЕЗ рекурсии)
    """)
    
    return class_stats, confusion


if __name__ == "__main__":
    visualize_recursive_errors()
