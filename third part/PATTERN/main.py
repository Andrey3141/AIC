import sys
from tests.test_logical import run_logical_tests
from tests.test_super_hybrid import run_super_hybrid_test
from tests.test_sequence_visual import run_sequence_visual_test


def print_menu():
    print("\n" + "=" * 80)
    print("ГЛАВНОЕ МЕНЮ")
    print("=" * 80)
    print("  1. Тест 1: Логическая задача (простые числа)")
    print("  2. Тест 2: Логическая задача (5 чисел)")
    print("  3. Тест 3: Распознавание цифр MNIST (Супер-гибрид)")
    print("  4. Тест 4: Визуальное сравнение предложений (стопки картинок)")
    print("  0. ЗАПУСТИТЬ ВСЕ ТЕСТЫ")
    print("=" * 80)


def run_test_1():
    print("\n" + "=" * 80)
    print("ТЕСТ 1: ЛОГИЧЕСКАЯ ЗАДАЧА (обучение на 8 числах)")
    print("=" * 80)
    acc, _ = run_logical_tests()
    return {"name": "Логическая задача (8 чисел)", "accuracy": f"{acc:.1%}"}


def run_test_2():
    print("\n" + "=" * 80)
    print("ТЕСТ 2: ЛОГИЧЕСКАДАЧА (5 новых чисел)")
    print("=" * 80)
    _, correct = run_logical_tests()
    return {"name": "Логическая задача (5 чисел)", "accuracy": f"{correct}/5"}


def run_test_3():
    print("\n" + "=" * 80)
    print("ТЕСТ 3: РАСПОЗНАВАНИЕ ЦИФР MNIST")
    print("=" * 80)
    acc = run_super_hybrid_test()
    return {"name": "Распознавание цифр MNIST", "accuracy": f"{acc:.2%}"}


def run_test_4():
    print("\n" + "=" * 80)
    print("ТЕСТ 4: ВИЗУАЛЬНОЕ СРАВНЕНИЕ ПРЕДЛОЖЕНИЙ")
    print("(каждое слово → картинка → стопка → DTW сравнение)")
    print("=" * 80)
    acc = run_sequence_visual_test()
    return {"name": "Визуальное сравнение предложений", "accuracy": f"{acc:.2%}"}


def run_all_tests():
    print("\n" + "=" * 80)
    print("ЗАПУСК ВСЕХ ТЕСТОВ")
    print("=" * 80)
    
    results = []
    results.append(run_test_1())
    results.append(run_test_2())
    results.append(run_test_3())
    results.append(run_test_4())
    
    print("\n" + "=" * 80)
    print("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("=" * 80)
    print("\n┌────┬────────────────────────────────────┬─────────────────────┐")
    print("│ №  │ Тест                               │ Результат           │")
    print("├────┼────────────────────────────────────┼─────────────────────┤")
    
    for i, result in enumerate(results, 1):
        print(f"│ {i}  │ {result['name']:<32} │ {result['accuracy']:>19} │")
    
    print("└────┴────────────────────────────────────┴─────────────────────┘")
    
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            choice = int(sys.argv[1])
        except ValueError:
            print("Ошибка: аргумент должен быть числом")
            print_menu()
            sys.exit(1)
    else:
        print_menu()
        try:
            choice = int(input("\nВыберите тест (0-4): "))
        except ValueError:
            print("Ошибка: введите число")
            sys.exit(1)
    
    if choice == 0:
        run_all_tests()
    elif choice == 1:
        run_test_1()
    elif choice == 2:
        run_test_2()
    elif choice == 3:
        run_test_3()
    elif choice == 4:
        run_test_4()
    else:
        print("Ошибка: неверный выбор. Введите число от 0 до 4.")
        print_menu()
