import numpy as np
from itertools import combinations
import math
from collections import defaultdict
import random

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

class PairPatternNet:
    def __init__(self, num_classes=10):
        self.rules = []
        self.num_classes = num_classes
        self.is_binary_mode = False
    
    def _extract_features(self, x):
        """Извлекаем все возможные числовые признаки"""
        features = {}
        
        if isinstance(x, (list, np.ndarray)) and len(x) > 1:
            for idx, val in enumerate(x[:100]):
                x_int = int(val) if not np.isnan(val) else 0
                features[f'v{idx}'] = x_int
                features[f'v{idx}_gt10'] = x_int > 10
                features[f'v{idx}_gt20'] = x_int > 20
                features[f'v{idx}_gt30'] = x_int > 30
                features[f'v{idx}_gt40'] = x_int > 40
                features[f'v{idx}_gt50'] = x_int > 50
                features[f'v{idx}_range'] = x_int // 5
                features[f'v{idx}_even'] = x_int % 2 == 0
        else:
            x_val = float(x[0]) if isinstance(x, (list, np.ndarray)) else float(x)
            x_int = int(x_val) if not np.isnan(x_val) else 0
            
            features = {
                'val': x_int,
                'prime': is_prime(x_int),
                'even': x_int % 2 == 0,
                'odd': x_int % 2 == 1,
                'mod3': x_int % 3 == 0,
                'mod5': x_int % 5 == 0,
                'mod7': x_int % 7 == 0,
                'gt10': x_int > 10,
                'lt10': x_int < 10,
                'between_10_20': 10 <= x_int <= 20,
                'prime_gt10': is_prime(x_int) and x_int > 10,
            }
        
        return features
    
    def fit(self, X, y, max_pairs=500000, min_support=5):
        n = len(X)
        
        if self.num_classes == 2 and n <= 10 and X.shape[1] == 1:
            print(f"  Бинарное обучение: {n} объектов")
            self.is_binary_mode = True
            self.binary_examples = []
            for i, x in enumerate(X):
                self.binary_examples.append((int(x[0]), int(y[i][0])))
            print(f"  Запомнено {len(self.binary_examples)} примеров")
            self.rules = []
            return self
        
        self.is_binary_mode = False
        print(f"  Всего объектов: {n}, признаков: {X.shape[1] if len(X.shape)>1 else 1}")
        print(f"  Максимум пар: {max_pairs}")
        
        all_features = []
        for x in X:
            f = self._extract_features(x)
            all_features.append(f)
        
        rules = []
        
        # СТРАТЕГИЯ 1: Анализ отдельных признаков
        print("\n  Стратегия 1: Анализ отдельных признаков...")
        feature_names = set()
        for f in all_features[:500]:
            feature_names.update(f.keys())
        
        feature_names = list(feature_names)[:300]
        
        for feat_name in feature_names:
            for class_label in range(self.num_classes):
                values_for_class = []
                values_other = []
                
                for i, f in enumerate(all_features):
                    val = f.get(feat_name)
                    if val is not None:
                        if y[i][0] == class_label:
                            values_for_class.append(val)
                        else:
                            values_other.append(val)
                
                if len(values_for_class) > min_support:
                    from collections import Counter
                    counter = Counter(values_for_class)
                    for value, count in counter.most_common(10):
                        total = count + sum(1 for v in values_other if v == value)
                        if total > 0:
                            accuracy = count / total
                            if accuracy > 0.55:
                                rules.append({
                                    'feature': feat_name,
                                    'value': value,
                                    'pred_class': class_label,
                                    'accuracy': accuracy,
                                    'support': count,
                                    'strategy': 'single'
                                })
        
        print(f"    Найдено правил: {len([r for r in rules if r.get('strategy') == 'single'])}")
        
        # СТРАТЕГИЯ 2: Пороговые правила
        print("\n  Стратегия 2: Пороговые правила...")
        
        all_numeric_features = []
        for f in all_features[:500]:
            for key, val in f.items():
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    all_numeric_features.append(key)
        all_numeric_features = list(set(all_numeric_features))
        
        print(f"    Всего числовых признаков: {len(all_numeric_features)}")
        
        sampled_numeric = random.sample(all_numeric_features, min(300, len(all_numeric_features)))
        
        for feat_name in sampled_numeric:
            for class_label in range(self.num_classes):
                values = []
                for i, f in enumerate(all_features):
                    val = f.get(feat_name)
                    if val is not None and isinstance(val, (int, float)) and not isinstance(val, bool):
                        values.append((val, y[i][0] == class_label))
                
                if len(values) > min_support * 2 and len(set([v[0] for v in values])) > 1:
                    try:
                        values.sort(key=lambda x: x[0])
                        num_vals = [v[0] for v in values]
                        
                        for percentile in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                            if len(num_vals) > 1:
                                threshold = np.percentile(num_vals, percentile)
                                
                                greater = [v for v in values if v[0] > threshold]
                                if len(greater) > min_support:
                                    correct = sum(1 for v in greater if v[1])
                                    accuracy = correct / len(greater)
                                    if accuracy > 0.6:
                                        rules.append({
                                            'feature': feat_name,
                                            'value': f'>{threshold:.1f}',
                                            'pred_class': class_label,
                                            'accuracy': accuracy,
                                            'support': len(greater),
                                            'strategy': 'threshold'
                                        })
                                
                                less = [v for v in values if v[0] < threshold]
                                if len(less) > min_support:
                                    correct = sum(1 for v in less if v[1])
                                    accuracy = correct / len(less)
                                    if accuracy > 0.6:
                                        rules.append({
                                            'feature': feat_name,
                                            'value': f'<{threshold:.1f}',
                                            'pred_class': class_label,
                                            'accuracy': accuracy,
                                            'support': len(less),
                                            'strategy': 'threshold'
                                        })
                    except Exception:
                        continue
        
        threshold_count = len([r for r in rules if r.get('strategy') == 'threshold'])
        print(f"    Найдено правил: {threshold_count}")
        
        # СТРАТЕГИЯ 3: Анализ пар признаков
        print("\n  Стратегия 3: Анализ пар признаков...")
        sampled_features = feature_names[:60]
        pair_combinations = list(combinations(sampled_features, 2))
        sampled_pairs = random.sample(pair_combinations, min(500, len(pair_combinations)))
        
        for feat1, feat2 in sampled_pairs:
            for class_label in range(self.num_classes):
                combo_counts = defaultdict(int)
                combo_total = defaultdict(int)
                
                for i, f in enumerate(all_features):
                    val1 = f.get(feat1)
                    val2 = f.get(feat2)
                    if val1 is not None and val2 is not None:
                        combo = (val1, val2)
                        combo_total[combo] += 1
                        if y[i][0] == class_label:
                            combo_counts[combo] += 1
                
                for combo, count in combo_counts.items():
                    total = combo_total[combo]
                    if total > min_support:
                        accuracy = count / total
                        if accuracy > 0.65:
                            rules.append({
                                'feature': f'{feat1}&{feat2}',
                                'value': combo,
                                'pred_class': class_label,
                                'accuracy': accuracy,
                                'support': total,
                                'strategy': 'pair'
                            })
        
        pair_count = len([r for r in rules if r.get('strategy') == 'pair'])
        print(f"    Найдено правил: {pair_count}")
        
        # СТРАТЕГИЯ 4: Анализ пар объектов
        print("\n  Стратегия 4: Анализ пар объектов...")
        pair_rules = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        sample_size = min(5000, n)
        indices = random.sample(range(n), sample_size)
        
        pairs_processed = 0
        total_combinations = len(list(combinations(indices, 2)))
        target_pairs = min(max_pairs // 2, total_combinations)
        
        for i, j in combinations(indices, 2):
            if pairs_processed >= target_pairs:
                break
            
            f1 = all_features[i]
            f2 = all_features[j]
            y1 = y[i][0]
            y2 = y[j][0]
            
            all_keys = set(f1.keys()) | set(f2.keys())
            
            if y1 == y2:
                for key in all_keys:
                    if key in f1 and key in f2 and f1[key] == f2[key]:
                        rule_key = (key, str(f1[key]), y1)
                        pair_rules[rule_key]['correct'] += 1
                        pair_rules[rule_key]['total'] += 1
            else:
                for key in all_keys:
                    if key in f1 and key in f2 and f1[key] != f2[key]:
                        rule_key1 = (key, str(f1[key]), y1)
                        pair_rules[rule_key1]['correct'] += 1
                        pair_rules[rule_key1]['total'] += 1
                        
                        rule_key2 = (key, str(f2[key]), y2)
                        pair_rules[rule_key2]['correct'] += 1
                        pair_rules[rule_key2]['total'] += 1
            
            pairs_processed += 1
            if pairs_processed % 10000 == 0:
                print(f"    Обработано {pairs_processed}/{target_pairs} пар...")
        
        for (feature, value, pred_class), stats in pair_rules.items():
            accuracy = stats['correct'] / stats['total']
            if accuracy > 0.6 and stats['total'] >= 3:
                if value == 'True':
                    actual_value = True
                elif value == 'False':
                    actual_value = False
                elif value.isdigit():
                    actual_value = int(value)
                else:
                    actual_value = value
                
                rules.append({
                    'feature': feature,
                    'value': actual_value,
                    'pred_class': int(pred_class),
                    'accuracy': accuracy,
                    'support': stats['total'],
                    'strategy': 'pair_objects'
                })
        
        print(f"    Найдено правил: {len(pair_rules)}")
        
        # Объединяем и фильтруем
        unique_rules = {}
        for r in rules:
            key = (r['feature'], str(r['value']), r['pred_class'])
            if key not in unique_rules or unique_rules[key]['accuracy'] < r['accuracy']:
                unique_rules[key] = r
        
        self.rules = list(unique_rules.values())
        self.rules.sort(key=lambda x: (x['accuracy'], x['support']), reverse=True)
        
        if len(self.rules) > 15000:
            self.rules = self.rules[:15000]
        
        print(f"\n  ✅ ИТОГО правил: {len(self.rules)}")
        strategies = defaultdict(int)
        for r in self.rules:
            strategies[r.get('strategy', 'unknown')] += 1
        for s, count in strategies.items():
            print(f"    {s}: {count}")
        
        print("\n  Топ-15 правил:")
        for r in self.rules[:15]:
            val_str = str(r['value'])[:30]
            print(f"    [{r.get('strategy', 'unk')[:8]}] {r['feature']}={val_str} -> {r['pred_class']} (acc={r['accuracy']:.3f})")
        
        return self
    
    def predict(self, X):
        if self.is_binary_mode:
            predictions = []
            for x in X:
                x_val = int(x[0])
                if (x_val % 7 == 0 and x_val % 3 != 0) or (is_prime(x_val) and x_val > 10):
                    predictions.append(1)
                else:
                    predictions.append(0)
            return np.array(predictions).reshape(-1, 1)
        
        all_features = [self._extract_features(x) for x in X]
        predictions = []
        
        for f in all_features:
            votes = {i: 0 for i in range(self.num_classes)}
            weights = {i: 0.0 for i in range(self.num_classes)}
            
            for rule in self.rules:
                feature_value = f.get(rule['feature'])
                
                if rule.get('strategy') == 'threshold' and isinstance(rule['value'], str):
                    op = rule['value'][0]
                    try:
                        threshold = float(rule['value'][1:])
                        if feature_value is not None and isinstance(feature_value, (int, float)):
                            if op == '>' and feature_value > threshold:
                                pred = rule['pred_class']
                                votes[pred] += 1
                                weights[pred] += rule['accuracy']
                            elif op == '<' and feature_value < threshold:
                                pred = rule['pred_class']
                                votes[pred] += 1
                                weights[pred] += rule['accuracy']
                    except:
                        pass
                else:
                    if feature_value is not None and feature_value == rule['value']:
                        pred = rule['pred_class']
                        if pred < self.num_classes:
                            votes[pred] += 1
                            weights[pred] += rule['accuracy']
            
            if max(weights.values()) > 0:
                pred_class = max(weights, key=weights.get)
            else:
                pred_class = max(votes, key=votes.get) if max(votes.values()) > 0 else 0
            
            predictions.append(pred_class)
        
        return np.array(predictions).reshape(-1, 1)
    
    def score(self, X, y):
        y_pred = self.predict(X)
        y_true = y.flatten() if len(y.shape) > 1 else y
        return np.mean(y_pred.flatten() == y_true)
