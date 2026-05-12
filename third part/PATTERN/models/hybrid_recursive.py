import numpy as np
from models.pair_pattern_net import PairPatternNet
from sklearn.preprocessing import StandardScaler, KBinsDiscretizer


class HybridRecursiveNet:
    """
    Рекурсивная модель (может быть отключена через max_levels=1)
    """
    
    def __init__(self, num_classes=10, min_samples_per_level=50, max_levels=3):
        self.num_classes = num_classes
        self.min_samples_per_level = min_samples_per_level
        self.max_levels = max_levels
        self.levels = []
        self.feature_func = None
    
    def set_feature_extractor(self, feature_func):
        self.feature_func = feature_func
    
    def _extract_features_batch(self, images, batch_size=100):
        """Извлекает признаки из изображений"""
        all_features = []
        for i in range(0, len(images), batch_size):
            batch = images[i:i+batch_size]
            for img in batch:
                features = self.feature_func(img)
                all_features.append(features)
        return np.array(all_features)
    
    def _preprocess_features(self, features):
        """Нормализация и дискретизация"""
        scaler = StandardScaler()
        features_norm = scaler.fit_transform(features)
        discretizer = KBinsDiscretizer(n_bins=15, encode='ordinal', strategy='uniform')
        features_disc = discretizer.fit_transform(features_norm).astype(int)
        return features_disc
    
    def _get_model_predictions(self, model, X_disc):
        """Предсказания и уверенность"""
        predictions = []
        confidences = []
        
        for x in X_disc:
            features = model._extract_features(x)
            
            weights = {c: 0.0 for c in range(self.num_classes)}
            
            for rule in model.rules:
                feature_value = features.get(rule['feature'])
                
                if rule.get('strategy') == 'threshold' and isinstance(rule['value'], str):
                    op = rule['value'][0]
                    try:
                        threshold = float(rule['value'][1:])
                        if feature_value is not None and isinstance(feature_value, (int, float)):
                            if op == '>' and feature_value > threshold:
                                pred = rule['pred_class']
                                if pred < self.num_classes:
                                    weights[pred] += rule['accuracy']
                            elif op == '<' and feature_value < threshold:
                                pred = rule['pred_class']
                                if pred < self.num_classes:
                                    weights[pred] += rule['accuracy']
                    except:
                        pass
                else:
                    if feature_value is not None and feature_value == rule['value']:
                        pred = rule['pred_class']
                        if pred < self.num_classes:
                            weights[pred] += rule['accuracy']
            
            if max(weights.values()) > 0:
                pred_class = max(weights, key=weights.get)
                confidence = max(weights.values()) / (sum(weights.values()) + 1e-6)
            else:
                pred_class = 0
                confidence = 0.0
            
            predictions.append(pred_class)
            confidences.append(confidence)
        
        return np.array(predictions), np.array(confidences)
    
    def fit(self, X, y, max_pairs=300000, min_support=3, level=1):
        """
        Обучает модель. Если max_levels=1, то без рекурсии.
        """
        print(f"\n{'='*70}")
        print(f"УРОВЕНЬ {level}: {len(X)} картинок")
        print(f"{'='*70}")
        
        # Если достигли лимита - останавливаемся
        if level > self.max_levels:
            print(f"  Достигнут max_levels={self.max_levels}")
            return
        
        if len(X) < self.min_samples_per_level:
            print(f"  Мало данных: {len(X)} < {self.min_samples_per_level}")
            return
        
        # Извлекаем признаки
        print("  Извлечение признаков...")
        X_features = self._extract_features_batch(X)
        X_disc = self._preprocess_features(X_features)
        
        print(f"  Признаки: {X_disc.shape}")
        
        # Обучаем модель
        model = PairPatternNet(num_classes=self.num_classes)
        model.fit(X_disc, y, max_pairs=max_pairs, min_support=min_support)
        
        # Оцениваем
        y_pred, confidences = self._get_model_predictions(model, X_disc)
        y_true = y.flatten()
        
        correct_mask = (y_pred == y_true)
        correct_count = np.sum(correct_mask)
        rework_count = len(X) - correct_count
        
        print(f"  ✓ Правильно: {correct_count} ({correct_count/len(X):.1%})")
        print(f"  ✗ Ошибки: {rework_count} ({rework_count/len(X):.1%})")
        print(f"  Правил: {len(model.rules)}")
        
        self.levels.append({
            'model': model,
            'level': level
        })
        
        # Рекурсия ТОЛЬКО если включена (max_levels > 1) И есть ошибки
        if self.max_levels > 1 and rework_count >= self.min_samples_per_level and level < self.max_levels:
            X_rework = X[~correct_mask]
            y_rework = y_true[~correct_mask]
            self.fit(X_rework, y_rework.reshape(-1, 1), max_pairs, min_support, level + 1)
    
    def predict(self, X, verbose=False):
        """
        Предсказание: последовательное применение уровней
        Если уровней > 1, то ошибки уровня 1 идут на уровень 2 и т.д.
        """
        n_samples = len(X)
        predictions = np.zeros(n_samples, dtype=int)
        used_level = np.zeros(n_samples, dtype=int)
        
        remaining = np.ones(n_samples, dtype=bool)
        
        for level_info in self.levels:
            if not np.any(remaining):
                break
            
            model = level_info['model']
            X_remaining = X[remaining]
            
            X_features = self._extract_features_batch(X_remaining)
            X_disc = self._preprocess_features(X_features)
            
            y_pred, _ = self._get_model_predictions(model, X_disc)
            
            # Если это последний уровень или рекурсия отключена - предсказываем всё
            if level_info['level'] == self.max_levels or self.max_levels == 1:
                confident_indices = np.where(remaining)[0]
                predictions[confident_indices] = y_pred
                used_level[confident_indices] = level_info['level']
                remaining_mask = np.ones(n_samples, dtype=bool)
                remaining_mask[confident_indices] = False
                remaining = remaining & remaining_mask
            else:
                # Если есть следующие уровни - предсказываем только уверенные
                # (но для простоты пока предсказываем всё)
                confident_indices = np.where(remaining)[0]
                predictions[confident_indices] = y_pred
                used_level[confident_indices] = level_info['level']
                remaining_mask = np.ones(n_samples, dtype=bool)
                remaining_mask[confident_indices] = False
                remaining = remaining & remaining_mask
            
            if verbose:
                print(f"  Уровень {level_info['level']}: предсказано {len(confident_indices)}")
        
        return predictions.reshape(-1, 1), used_level
    
    def score(self, X, y):
        y_pred, _ = self.predict(X)
        y_true = y.flatten() if len(y.shape) > 1 else y
        return np.mean(y_pred.flatten() == y_true)
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print(f"СТРУКТУРА МОДЕЛИ (max_levels={self.max_levels})")
        print("=" * 70)
        total_rules = 0
        for level_info in self.levels:
            model = level_info['model']
            level = level_info['level']
            num_rules = len(model.rules)
            total_rules += num_rules
            print(f"  Уровень {level}: {num_rules} правил")
        print(f"\n  Всего правил: {total_rules}")
