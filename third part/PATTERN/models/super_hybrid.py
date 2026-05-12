import numpy as np
from models.pair_pattern_net import PairPatternNet
from models.hybrid_recursive import HybridRecursiveNet
from models.coarse_to_fine import CoarseToFineNet
from features.hybrid_features import (
    extract_original_features, 
    extract_coordinate_features, 
    extract_cnn_features, 
    crop_to_digit
)
from features.nonogram_features import extract_nonogram_features
from features.edit_distance_classifier import EditDistanceClassifier
from sklearn.metrics import accuracy_score


class SuperHybridNet:
    """
    Супер-гибрид: CTF только для Оригинального модуля
    """
    
    def __init__(self, num_classes=10, confidence_threshold=0.15):
        self.num_classes = num_classes
        self.confidence_threshold = confidence_threshold
        self.modules = []
        self.module_weights = []
        self.module_names = []
    
    def _add_ctf_module(self, name, feature_func, use_crop=True):
        """Добавляет модуль С CTF (только для Оригинального)"""
        print(f"\n📌 Добавляем Coarse-to-Fine модуль: {name}")
        
        module = CoarseToFineNet(
            num_classes=self.num_classes,
            confidence_threshold=self.confidence_threshold
        )
        
        if use_crop:
            def wrapped_feature_func(img):
                cropped = crop_to_digit(img)
                return feature_func(cropped)
            module.set_feature_extractor(wrapped_feature_func)
        else:
            module.set_feature_extractor(feature_func)
        
        self.modules.append({
            'type': 'ctf',
            'model': module,
            'name': name
        })
        self.module_names.append(name)
    
    def _add_ppn_module(self, name, feature_func, use_crop=True):
        """Добавляет обычный PPN модуль БЕЗ CTF"""
        print(f"\n📌 Добавляем PPN модуль: {name}")
        
        module = HybridRecursiveNet(
            num_classes=self.num_classes,
            min_samples_per_level=50,
            max_levels=1  # без рекурсии
        )
        
        if use_crop:
            def wrapped_feature_func(img):
                cropped = crop_to_digit(img)
                return feature_func(cropped)
            module.set_feature_extractor(wrapped_feature_func)
        else:
            module.set_feature_extractor(feature_func)
        
        self.modules.append({
            'type': 'ppn',
            'model': module,
            'name': name
        })
        self.module_names.append(name)
    
    def _add_edit_module(self, name):
        """Добавляет EditDistance как прямой классификатор БЕЗ CTF"""
        print(f"\n📌 Добавляем прямой классификатор: {name}")
        
        classifier = EditDistanceClassifier()
        
        self.modules.append({
            'type': 'edit',
            'model': classifier,
            'name': name
        })
        self.module_names.append(name)
    
    def fit(self, X, y, max_pairs=300000, min_support=3):
        """
        Обучает все модули
        """
        # Создаём валидационную выборку
        val_size = int(len(X) * 0.2)
        val_indices = np.random.choice(len(X), val_size, replace=False)
        train_indices = [i for i in range(len(X)) if i not in val_indices]
        
        X_train = X[train_indices]
        y_train = y[train_indices]
        X_val = X[val_indices]
        y_val = y[val_indices]
        
        print(f"\n{'='*80}")
        print(f"ОБУЧЕНИЕ СУПЕР-ГИБРИДА")
        print(f"{'='*80}")
        print(f"  Train: {len(X_train)}")
        print(f"  Validation: {len(X_val)}")
        print(f"  Модулей: {len(self.modules)}")
        
        # Обучаем каждый модуль
        val_accuracies = []
        
        for i, module_info in enumerate(self.modules):
            name = module_info['name']
            print(f"\n{'─'*80}")
            print(f"ОБУЧЕНИЕ МОДУЛЯ {i+1}: {name}")
            print(f"{'─'*80}")
            
            if module_info['type'] == 'ctf':
                # Coarse-to-Fine модуль
                module_info['model'].fit(X_train, y_train, max_pairs=max_pairs, min_support=min_support)
                y_val_pred, _, _ = module_info['model'].predict(X_val)
                
            elif module_info['type'] == 'ppn':
                # Обычный PPN модуль
                module_info['model'].fit(X_train, y_train, max_pairs=max_pairs, min_support=min_support)
                y_val_pred, _ = module_info['model'].predict(X_val)
                
            else:  # edit
                # EditDistance прямой классификатор
                module_info['model'].train(X_train, y_train)
                y_val_pred = module_info['model'].predict(X_val)
            
            acc = accuracy_score(y_val.flatten(), y_val_pred.flatten())
            val_accuracies.append(acc)
            print(f"\n  ✅ {name} на валидации: {acc:.2%}")
        
        # Вычисляем веса по точности на валидации
        total = sum(val_accuracies)
        self.module_weights = [acc / total for acc in val_accuracies]
        
        print(f"\n{'='*80}")
        print(f"ВЕСА МОДУЛЕЙ (по валидации)")
        print(f"{'='*80}")
        for i, (module_info, weight, acc) in enumerate(zip(self.modules, self.module_weights, val_accuracies)):
            print(f"  {module_info['name']}: {weight:.3f} (валидация: {acc:.2%})")
        
        print(f"\n  Сумма весов: {sum(self.module_weights):.3f}")
    
    def predict(self, X, verbose=False):
        """
        Предсказание: взвешенное голосование всех модулей
        """
        n_samples = len(X)
        
        # Собираем предсказания от всех модулей
        all_predictions = []
        
        for module_info in self.modules:
            if verbose:
                print(f"  Предсказание модуля {module_info['name']}...")
            
            if module_info['type'] == 'ctf':
                y_pred, _, _ = module_info['model'].predict(X)
            elif module_info['type'] == 'ppn':
                y_pred, _ = module_info['model'].predict(X)
            else:  # edit
                y_pred = module_info['model'].predict(X)
            
            all_predictions.append(y_pred.flatten())
        
        all_predictions = np.array(all_predictions)
        
        # Взвешенное голосование
        final_predictions = []
        for sample_idx in range(n_samples):
            votes = {c: 0.0 for c in range(self.num_classes)}
            for module_idx in range(len(self.modules)):
                pred_class = all_predictions[module_idx][sample_idx]
                votes[pred_class] += self.module_weights[module_idx]
            best_class = max(votes, key=votes.get)
            final_predictions.append(best_class)
        
        return np.array(final_predictions).reshape(-1, 1)
    
    def score(self, X, y):
        y_pred = self.predict(X)
        y_true = y.flatten() if len(y.shape) > 1 else y
        return np.mean(y_pred.flatten() == y_true)
    
    def print_summary(self):
        print("\n" + "=" * 80)
        print("СТРУКТУРА СУПЕР-ГИБРИДА")
        print("=" * 80)
        
        total_rules = 0
        for i, (module_info, weight) in enumerate(zip(self.modules, self.module_weights)):
            print(f"\n  Модуль {i+1}: {module_info['name']} (вес: {weight:.3f})")
            if module_info['type'] == 'ctf':
                total_rules += sum(len(m['model'].rules) for m in module_info['model'].scale_models)
            elif module_info['type'] == 'ppn':
                total_rules += sum(len(m['model'].rules) for m in module_info['model'].levels)
        
        print(f"\n  Всего правил: {total_rules}")
