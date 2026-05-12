import numpy as np
from collections import defaultdict, Counter
import re

class VoiceStickConverter:
    """
    Превращает слово в "голосовые палочки"
    Каждый символ → число (код) → палочка высотой = число
    Предложение → спектрограмма из палочек
    """
    
    def __init__(self, max_height=50):
        self.max_height = max_height
        self.char_to_code = {}
        self.code_to_char = {}
        self.next_code = 1  # 0 для пустоты
    
    def _get_char_code(self, char):
        """Получает код символа (цифру)"""
        if char not in self.char_to_code:
            self.char_to_code[char] = self.next_code
            self.code_to_char[self.next_code] = char
            self.next_code += 1
        return self.char_to_code[char]
    
    def word_to_sticks(self, word, max_len=10):
        """
        Превращает слово в набор палочек
        Каждый символ → палочка высотой = код символа
        Возвращает: массив высот палочек
        """
        word = word[:max_len]
        sticks = []
        
        for char in word:
            code = self._get_char_code(char)
            # Нормализуем высоту, чтобы не выходила за пределы
            height = min(code, self.max_height)
            sticks.append(height)
        
        # Если слово короткое, добавляем нули
        while len(sticks) < max_len:
            sticks.append(0)
        
        return np.array(sticks)
    
    def sentence_to_spectrogram(self, sentence, max_words=20, max_word_len=10):
        """
        Превращает предложение в спектрограмму (матрицу из палочек)
        По вертикали - палочки слова, по горизонтали - слова
        """
        words = re.findall(r'\b\w+\b', sentence.lower())
        words = words[:max_words]
        
        spectrogram = []
        for word in words:
            sticks = self.word_to_sticks(word, max_word_len)
            spectrogram.append(sticks)
        
        if len(spectrogram) == 0:
            return np.zeros((1, max_word_len))
        
        # Транспонируем: строки = позиции в слове, столбцы = слова
        return np.array(spectrogram).T
    
    def compare_spectrograms(self, spec1, spec2):
        """
        Сравнивает две спектрограммы (два предложения)
        Использует DTW для нахождения схожести
        """
        h1, w1 = spec1.shape
        h2, w2 = spec2.shape
        
        # DTW матрица
        dtw = np.full((w1 + 1, w2 + 1), np.inf)
        dtw[0, 0] = 0
        
        for i in range(1, w1 + 1):
            for j in range(1, w2 + 1):
                # Сравниваем столбцы (слова)
                col1 = spec1[:, i-1]
                col2 = spec2[:, j-1]
                # Евклидово расстояние между палочками
                cost = np.sqrt(np.mean((col1 - col2) ** 2))
                
                dtw[i, j] = cost + min(
                    dtw[i-1, j],     # удаление
                    dtw[i, j-1],     # вставка
                    dtw[i-1, j-1]    # совпадение
                )
        
        distance = dtw[w1, w2]
        similarity = 1 / (1 + distance)
        
        return similarity, distance
    
    def visualize_spectrogram(self, sentence, ax=None):
        """
        Визуализирует спектрограмму предложения
        """
        spec = self.sentence_to_spectrogram(sentence)
        
        if ax is None:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(12, 6))
        
        im = ax.imshow(spec, aspect='auto', cmap='viridis', origin='lower')
        ax.set_xlabel('Позиция слова в предложении', fontsize=10)
        ax.set_ylabel('Позиция символа в слове', fontsize=10)
        ax.set_title('Спектрограмма предложения (голосовые палочки)', fontsize=12)
        
        return spec


class VoiceStickAnalyzer:
    """
    Анализирует последовательности через сравнение спектрограмм
    """
    
    def __init__(self):
        self.converter = VoiceStickConverter()
        self.sequences = []  # храним все спектрограммы
    
    def add_sentence(self, sentence):
        """Добавляет предложение в анализ"""
        spec = self.converter.sentence_to_spectrogram(sentence)
        words = re.findall(r'\b\w+\b', sentence.lower())
        
        self.sequences.append({
            'text': sentence,
            'spectrogram': spec,
            'words': words
        })
    
    def find_similar(self, query_sentence, top_k=3):
        """
        Находит похожие предложения по форме спектрограммы
        """
        query_spec = self.converter.sentence_to_spectrogram(query_sentence)
        
        similarities = []
        for i, seq in enumerate(self.sequences):
            sim, _ = self.converter.compare_spectrograms(query_spec, seq['spectrogram'])
            similarities.append((i, sim, seq['text']))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def extract_features(self, sentence):
        """
        Извлекает признаки из спектрограммы для PairPatternNet
        """
        spec = self.converter.sentence_to_spectrogram(sentence)
        h, w = spec.shape
        
        features = []
        
        # 1. Средняя высота палочек
        features.append(np.mean(spec))
        features.append(np.std(spec))
        features.append(np.max(spec))
        
        # 2. Энергия спектрограммы (сумма квадратов)
        features.append(np.sum(spec ** 2))
        
        # 3. Градиенты (как меняются палочки)
        if w > 1:
            grad = np.diff(spec, axis=1)
            features.append(np.mean(np.abs(grad)))
            features.append(np.std(grad))
        else:
            features.extend([0, 0])
        
        # 4. Первые 50 значений спектрограммы как признаки
        flat = spec.flatten()[:50]
        features.extend(flat)
        
        # Дополняем до 100
        while len(features) < 100:
            features.append(0)
        
        return np.array(features[:100])


class SequenceSimilarityClassifierV2:
    """
    Классификатор на основе спектрограмм (голосовые палочки)
    """
    
    def __init__(self):
        self.analyzer = VoiceStickAnalyzer()
        self.class_examples = defaultdict(list)
    
    def fit(self, texts, labels):
        """Обучает: запоминает спектрограммы каждого класса"""
        print(f"\n📚 ОБУЧЕНИЕ (голосовые палочки)")
        print(f"   Всего текстов: {len(texts)}")
        
        for text, label in zip(texts, labels):
            self.analyzer.add_sentence(text)
            self.class_examples[label].append(text)
        
        print(f"   Классов: {len(self.class_examples)}")
        return self
    
    def predict(self, text):
        """Предсказывает класс по схожести спектрограмм"""
        query_spec = self.analyzer.converter.sentence_to_spectrogram(text)
        
        best_class = None
        best_similarity = -1
        
        for label, examples in self.class_examples.items():
            for example in examples:
                example_spec = self.analyzer.converter.sentence_to_spectrogram(example)
                sim, _ = self.analyzer.converter.compare_spectrograms(query_spec, example_spec)
                
                if sim > best_similarity:
                    best_similarity = sim
                    best_class = label
        
        return best_class
    
    def find_similar_sentences(self, query, top_k=3):
        """Находит похожие предложения"""
        return self.analyzer.find_similar(query, top_k)
