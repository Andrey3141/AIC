import numpy as np
from collections import defaultdict
import re

class PatternStickAnalyzer:
    """
    Сравнение предложений через палочки
    """
    
    def __init__(self):
        self.char_to_code = {}
        self.next_code = 1
        self.sequences = []  # храним все предложения
    
    def sentence_to_sticks(self, sentence):
        """
        Предложение → массив высот палочек (коды букв)
        "маша ела кашу" → [13, 1, 18, 1, 6, 13, 1, 12, 1, 18, 21]
        """
        sentence = sentence.lower()
        sticks = []
        for char in sentence:
            if char.isalpha():
                if char not in self.char_to_code:
                    self.char_to_code[char] = self.next_code
                    self.next_code += 1
                sticks.append(self.char_to_code[char])
        return np.array(sticks)
    
    def add_sentence(self, sentence):
        """Добавляет предложение в базу для поиска"""
        sticks = self.sentence_to_sticks(sentence)
        self.sequences.append({
            'text': sentence,
            'sticks': sticks
        })
    
    def compare_sticks(self, sticks1, sticks2):
        """
        Сравнивает два набора палочек
        Возвращает схожесть (0-1)
        """
        # DTW расстояние
        dtw = np.full((len(sticks1)+1, len(sticks2)+1), np.inf)
        dtw[0, 0] = 0
        
        for i in range(1, len(sticks1)+1):
            for j in range(1, len(sticks2)+1):
                cost = abs(sticks1[i-1] - sticks2[j-1])
                dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
        
        distance = dtw[len(sticks1), len(sticks2)]
        normalized = distance / max(len(sticks1), len(sticks2))
        similarity = 1 / (1 + normalized)
        
        return similarity
    
    def find_similar(self, query_sentence, top_k=3):
        """
        Находит похожие предложения
        """
        query_sticks = self.sentence_to_sticks(query_sentence)
        
        similarities = []
        for i, seq in enumerate(self.sequences):
            sim = self.compare_sticks(query_sticks, seq['sticks'])
            similarities.append((i, sim, seq['text']))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def extract_features(self, sentence):
        """
        Извлекает признаки из палочек для PairPatternNet
        """
        sticks = self.sentence_to_sticks(sentence)
        
        features = []
        features.append(len(sticks))        # длина
        features.append(np.mean(sticks))     # средняя высота
        features.append(np.std(sticks))      # разброс
        features.append(np.max(sticks))      # максимальная
        
        # Первые 30 значений
        features.extend(sticks[:30])
        
        # Дополняем до 100
        while len(features) < 100:
            features.append(0)
        
        return np.array(features[:100])
