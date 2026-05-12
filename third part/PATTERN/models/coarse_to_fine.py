import numpy as np
from models.pair_pattern_net import PairPatternNet
from scipy import ndimage
from sklearn.preprocessing import StandardScaler, KBinsDiscretizer


class CoarseToFineNet:
    """
    Coarse-to-Fine классификация (БЕЗ рекурсии)
    """
    
    def __init__(self, num_classes=10, confidence_threshold=0.6):
        self.num_classes = num_classes
        self.confidence_threshold = confidence_threshold
        self.scale_models = []
        self.feature_func = None
    
    def set_feature_extractor(self, feature_func):
        self.feature_func = feature_func
    
    def _extract_features_batch(self, images, batch_size=100):
        """Извлекает признаки, приводя все к одинаковой длине"""
        all_features = []
        for i in range(0, len(images), batch_size):
            batch = images[i:i+batch_size]
            for img in batch:
                features = self.feature_func(img)
                # Принудительно приводим к numpy array
                if not isinstance(features, np.ndarray):
                    features = np.array(features)
                all_features.append(features)
        
        # Находим минимальную длину признаков
        min_len = min(len(f) for f in all_features)
        # Обрезаем все до минимальной длины
        all_features = [f[:min_len] for f in all_features]
        
        return np.array(all_features, dtype=np.float32)
    
    def _preprocess_features(self, features):
        scaler = StandardScaler()
        features_norm = scaler.fit_transform(features)
        discretizer = KBinsDiscretizer(n_bins=15, encode='ordinal', strategy='uniform')
        features_disc = discretizer.fit_transform(features_norm).astype(int)
        return features_disc
    
    def _get_confidence(self, model, X_disc):
        """Получает уверенность предсказания"""
        confidences = []
        predictions = []
        
        for x in X_disc:
            features = model._extract_features(x)
            
            weights = {c: 0.0 for c in range(self.num_classes)}
            
            for rule in model.rules:
                feature_value = features.get(rule['feature'])
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
    
    def fit(self, X, y, max_pairs=300000, min_support=3):
        """
        Обучаем ОТДЕЛЬНЫЕ модели на разных масштабах (НЕ рекурсивно)
        """
        print(f"\n{'='*70}")
        print(f"ОБУЧЕНИЕ COARSE-TO-FINE (БЕЗ РЕКУРСИИ)")
        print(f"{'='*70}")
        
        # Масштабы: от самого размытого до чёткого
        scales = [
            ('ultra_blur', 3.0),
            ('high_blur', 2.0),
            ('med_blur', 1.0),
            ('sharp', 0.0),
        ]
        
        for scale_name, sigma in scales:
            print(f"\n📌 Масштаб: {scale_name} (sigma={sigma})")
            
            # Создаём размытые копии ВСЕХ картинок
            if sigma > 0:
                X_scaled = np.array([ndimage.gaussian_filter(img, sigma=sigma) for img in X])
            else:
                X_scaled = X
            
            # Извлекаем признаки
            print("  Извлечение признаков...")
            X_features = self._extract_features_batch(X_scaled)
            X_disc = self._preprocess_features(X_features)
            
            # Обучаем модель
            model = PairPatternNet(num_classes=self.num_classes)
            model.fit(X_disc, y, max_pairs=max_pairs, min_support=min_support)
            
            # Оцениваем
            y_pred, confidences = self._get_confidence(model, X_disc)
            y_true = y.flatten()
            acc = np.mean(y_pred == y_true)
            
            print(f"  Точность: {acc:.2%}")
            print(f"  Средняя уверенность: {np.mean(confidences):.2%}")
            print(f"  Правил: {len(model.rules)}")
            
            self.scale_models.append({
                'name': scale_name,
                'model': model,
                'sigma': sigma
            })
    
    def predict(self, X, verbose=False):
        n_samples = len(X)
        final_predictions = np.zeros(n_samples, dtype=int)
        final_confidences = np.zeros(n_samples)
        used_scale = np.zeros(n_samples, dtype=int)
        
        remaining = np.ones(n_samples, dtype=bool)
        
        for scale_idx, scale_info in enumerate(self.scale_models):
            if not np.any(remaining):
                break
            
            scale_name = scale_info['name']
            model = scale_info['model']
            sigma = scale_info['sigma']
            
            X_remaining = X[remaining]
            
            # Размытие
            if sigma > 0:
                X_scaled = np.array([ndimage.gaussian_filter(img, sigma=sigma) for img in X_remaining])
            else:
                X_scaled = X_remaining
            
            # Извлекаем признаки
            X_features = self._extract_features_batch(X_scaled)
            X_disc = self._preprocess_features(X_features)
            
            # Предсказываем
            y_pred, confidences = self._get_confidence(model, X_disc)
            
            # Уверенные предсказания
            is_confident = (confidences >= self.confidence_threshold)
            
            confident_indices = np.where(remaining)[0][is_confident]
            final_predictions[confident_indices] = y_pred[is_confident]
            final_confidences[confident_indices] = confidences[is_confident]
            used_scale[confident_indices] = scale_idx
            
            # Обновляем маску
            remaining_mask = np.ones(n_samples, dtype=bool)
            remaining_mask[confident_indices] = False
            remaining = remaining & remaining_mask
            
            if verbose:
                print(f"  {scale_name}: предсказано {len(confident_indices)}, осталось {np.sum(remaining)}")
        
        # Fallback для оставшихся
        if np.any(remaining):
            if verbose:
                print(f"  fallback: {np.sum(remaining)} картинок")
            last_model = self.scale_models[-1]['model']
            X_remaining = X[remaining]
            X_features = self._extract_features_batch(X_remaining)
            X_disc = self._preprocess_features(X_features)
            y_pred, _ = self._get_confidence(last_model, X_disc)
            final_predictions[remaining] = y_pred
            used_scale[remaining] = len(self.scale_models)
        
        return final_predictions.reshape(-1, 1), final_confidences, used_scale
    
    def score(self, X, y):
        y_pred, _, _ = self.predict(X)
        y_true = y.flatten() if len(y.shape) > 1 else y
        return np.mean(y_pred.flatten() == y_true)
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("СТРУКТУРА COARSE-TO-FINE (БЕЗ РЕКУРСИИ)")
        print("=" * 70)
        total_rules = 0
        for scale_info in self.scale_models:
            name = scale_info['name']
            model = scale_info['model']
            sigma = scale_info['sigma']
            num_rules = len(model.rules)
            total_rules += num_rules
            print(f"  {name} (sigma={sigma}): {num_rules} правил")
        print(f"\n  Всего правил: {total_rules}")
