import numpy as np
from collections import defaultdict, Counter
import re

class WordToImageConverter:
    def __init__(self, img_size=16):
        self.img_size = img_size
        self.char_to_code = {}
        self.code_to_char = {}
        self.next_code = 1
    
    def _get_char_code(self, char):
        if char not in self.char_to_code:
            self.char_to_code[char] = self.next_code
            self.code_to_char[self.next_code] = char
            self.next_code += 1
        return self.char_to_code[char]
    
    def word_to_image(self, word, max_len=10):
        word = word[:max_len]
        img = np.zeros((max_len, self.img_size), dtype=np.float32)
        for i, char in enumerate(word):
            code = self._get_char_code(char)
            normalized = (code % 255) / 255.0
            img[i, :] = normalized
        return img
    
    def sentence_to_stack(self, sentence, max_words=20, max_word_len=10):
        words = re.findall(r'\b\w+\b', sentence.lower())
        words = words[:max_words]
        stack = []
        for word in words:
            img = self.word_to_image(word, max_word_len)
            stack.append(img)
        if len(stack) == 0:
            return np.zeros((1, max_word_len, self.img_size))
        return np.array(stack)
    
    def compare_stacks(self, stack1, stack2):
        n1 = len(stack1)
        n2 = len(stack2)
        
        dist_matrix = np.zeros((n1, n2))
        for i in range(n1):
            for j in range(n2):
                mse = np.mean((stack1[i] - stack2[j]) ** 2)
                dist_matrix[i, j] = mse
        
        dtw = np.full((n1 + 1, n2 + 1), np.inf)
        dtw[0, 0] = 0
        
        for i in range(1, n1 + 1):
            for j in range(1, n2 + 1):
                cost = dist_matrix[i-1, j-1]
                dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
        
        similarity = 1 / (1 + dtw[n1, n2])
        return similarity, dist_matrix, dtw[n1, n2]


class WordSequenceAnalyzer:
    def __init__(self):
        self.converter = WordToImageConverter()
        self.sequences = []
    
    def add_sentence(self, sentence):
        stack = self.converter.sentence_to_stack(sentence)
        words = re.findall(r'\b\w+\b', sentence.lower())
        self.sequences.append({
            'text': sentence,
            'stack': stack,
            'words': words
        })
    
    def find_similar(self, query_sentence, top_k=3):
        """Находит похожие предложения"""
        query_stack = self.converter.sentence_to_stack(query_sentence)
        
        similarities = []
        for i, seq in enumerate(self.sequences):
            sim, _, _ = self.converter.compare_stacks(query_stack, seq['stack'])
            similarities.append((i, sim, seq['text']))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def extract_features(self, sentence):
        stack = self.converter.sentence_to_stack(sentence)
        features = []
        flat = stack.flatten()[:100]
        features.extend(flat)
        while len(features) < 100:
            features.append(0)
        return np.array(features[:100])


class SequenceSimilarityClassifier:
    def __init__(self):
        self.analyzer = WordSequenceAnalyzer()
        self.class_examples = defaultdict(list)
    
    def fit(self, texts, labels):
        for text, label in zip(texts, labels):
            self.analyzer.add_sentence(text)
            self.class_examples[label].append(text)
        return self
    
    def predict(self, text):
        query_stack = self.analyzer.converter.sentence_to_stack(text)
        best_class = None
        best_similarity = -1
        
        for label, examples in self.class_examples.items():
            for example in examples:
                example_stack = self.analyzer.converter.sentence_to_stack(example)
                sim, _, _ = self.analyzer.converter.compare_stacks(query_stack, example_stack)
                if sim > best_similarity:
                    best_similarity = sim
                    best_class = label
        return best_class if best_class is not None else 0
