import numpy as np
import time
import re
from collections import defaultdict, Counter
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def load_text(filepath='text'):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


class Method1_CharPatterns:
    def __init__(self, pattern_length=5):
        self.pattern_length = pattern_length
        self.pattern_stats = {}
        self.class_examples = {}
        
    def fit(self, X, y):
        all_text = ' '.join(X).lower()
        patterns = defaultdict(list)
        for i in range(len(all_text) - self.pattern_length):
            pattern = all_text[i:i + self.pattern_length]
            next_char = all_text[i + self.pattern_length]
            patterns[pattern].append(next_char)
        
        self.pattern_stats = {}
        for pattern, next_chars in patterns.items():
            counter = Counter(next_chars)
            total = len(next_chars)
            self.pattern_stats[pattern] = {ch: count/total for ch, count in counter.items()}
        
        self.class_examples = defaultdict(list)
        for text, label in zip(X, y):
            self.class_examples[label].append(text.lower())
        print(f"  Паттернов: {len(self.pattern_stats)}")
    
    def generate(self, start_text, length=80):
        result = start_text
        context = start_text
        for _ in range(length):
            context_lower = context.lower()
            if len(context_lower) >= self.pattern_length:
                key = context_lower[-self.pattern_length:]
                if key in self.pattern_stats:
                    stats = self.pattern_stats[key]
                    if stats:
                        next_char = max(stats, key=stats.get)
                        result += next_char
                        context = (context + next_char)[-self.pattern_length:]
                        continue
            break
        return result
    
    def predict(self, X):
        predictions = []
        for text in X:
            text_lower = text.lower()
            best_label = None
            best_sim = -1
            for label, examples in self.class_examples.items():
                for ex in examples[:10]:
                    min_len = min(len(text_lower), len(ex))
                    if min_len == 0:
                        sim = 0
                    else:
                        matches = sum(1 for i in range(min_len) if text_lower[i] == ex[i])
                        sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_label = label
            predictions.append(best_label if best_label is not None else 0)
        return np.array(predictions)


class Method2_StickHierarchy:
    def __init__(self, phrase_len=3):
        self.phrase_len = phrase_len
        self.char_to_code = {}
        self.class_examples = defaultdict(list)
        self.all_phrases = defaultdict(list)
        
    def _char_to_vector(self, char):
        if char not in self.char_to_code:
            self.char_to_code[char] = len(self.char_to_code) + 1
        code = self.char_to_code[char]
        return np.array([code % 255 / 255.0] * 16)
    
    def _word_to_stack(self, word):
        stack = [self._char_to_vector(ch) for ch in word[:10]]
        while len(stack) < 10:
            stack.append(np.zeros(16))
        return np.array(stack)
    
    def _phrase_to_stack(self, words):
        phrase_stack = [self._word_to_stack(w) for w in words[:self.phrase_len]]
        while len(phrase_stack) < self.phrase_len:
            phrase_stack.append(np.zeros((10, 16)))
        return np.array(phrase_stack)
    
    def _sentence_to_stack(self, sentence):
        words = re.findall(r'\b\w+\b', sentence.lower())
        phrases = [words[i:i+self.phrase_len] for i in range(0, len(words), self.phrase_len)]
        sent_stack = [self._phrase_to_stack(p) for p in phrases[:10]]
        while len(sent_stack) < 10:
            sent_stack.append(np.zeros((self.phrase_len, 10, 16)))
        return np.array(sent_stack)
    
    def fit(self, X, y):
        for text, label in zip(X, y):
            text_lower = text.lower()
            self.class_examples[label].append(text_lower)
            words = re.findall(r'\b\w+\b', text_lower)
            for i in range(len(words) - self.phrase_len):
                phrase = ' '.join(words[i:i+self.phrase_len])
                next_word = words[i+self.phrase_len] if i+self.phrase_len < len(words) else None
                if next_word:
                    self.all_phrases[phrase].append(next_word)
        print(f"  Фраз: {len(self.all_phrases)}")
    
    def generate(self, start_text, length=10):
        start_lower = start_text.lower()
        words = start_lower.split()
        result = words.copy()
        for _ in range(length):
            if len(result) < self.phrase_len:
                break
            phrase = ' '.join(result[-self.phrase_len:])
            if phrase in self.all_phrases:
                next_words = self.all_phrases[phrase]
                if next_words:
                    counter = Counter(next_words)
                    next_word = counter.most_common(1)[0][0]
                    result.append(next_word)
                else:
                    break
            else:
                break
        return ' '.join(result)
    
    def predict(self, X):
        predictions = []
        for text in X:
            text_lower = text.lower()
            best_label = None
            best_sim = -1
            for label, examples in self.class_examples.items():
                for ex in examples[:10]:
                    min_len = min(len(text_lower), len(ex))
                    if min_len == 0:
                        sim = 0
                    else:
                        matches = sum(1 for i in range(min_len) if text_lower[i] == ex[i])
                        sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_label = label
            predictions.append(best_label if best_label is not None else 0)
        return np.array(predictions)


class Method3_CodePatterns:
    def __init__(self, window_size=100, pattern_min_len=3, pattern_max_len=10):
        self.window_size = window_size
        self.pattern_min_len = pattern_min_len
        self.pattern_max_len = pattern_max_len
        self.char_to_code = {}
        self.code_to_char = {}
        self.stable_patterns = {}
        self.pattern_next = defaultdict(list)
        self.class_examples = defaultdict(list)
        
    def _char_to_code(self, char):
        if char not in self.char_to_code:
            self.char_to_code[char] = len(self.char_to_code) + 1
            self.code_to_char[len(self.code_to_char) + 1] = char
        return self.char_to_code[char]
    
    def _text_to_codes(self, text):
        return [self._char_to_code(ch) for ch in text]
    
    def _check_pattern_stability(self, pattern, all_codes):
        occurrences = []
        pattern_len = len(pattern)
        for i in range(len(all_codes) - pattern_len):
            if tuple(all_codes[i:i+pattern_len]) == pattern:
                next_code = all_codes[i+pattern_len] if i+pattern_len < len(all_codes) else None
                occurrences.append(next_code)
        if len(occurrences) < 2:
            return 0, {}
        next_counter = Counter([oc for oc in occurrences if oc is not None])
        if not next_counter:
            return 0, {}
        most_common_count = next_counter.most_common(1)[0][1]
        stability = most_common_count / len(occurrences)
        next_chars = {self.code_to_char.get(code, '?'): count/len(occurrences) 
                      for code, count in next_counter.items()}
        return stability, next_chars
    
    def fit(self, X, y):
        all_text = ' '.join(X)
        all_codes = self._text_to_codes(all_text)
        print(f"  Символов: {len(self.char_to_code)}")
        
        for start in range(0, len(all_codes) - self.window_size, self.window_size // 2):
            window = all_codes[start:start + self.window_size]
            for length in range(self.pattern_min_len, min(self.pattern_max_len, len(window)) + 1):
                for i in range(len(window) - length):
                    pattern = tuple(window[i:i+length])
                    stability, next_chars = self._check_pattern_stability(pattern, all_codes)
                    if stability > 0.7 and pattern not in self.stable_patterns:
                        self.stable_patterns[pattern] = stability
                        for ch, prob in next_chars.items():
                            self.pattern_next[pattern].append((ch, prob))
        
        self.stable_patterns = dict(sorted(self.stable_patterns.items(), key=lambda x: -x[1])[:500])
        print(f"  Паттернов: {len(self.stable_patterns)}")
        
        for text, label in zip(X, y):
            self.class_examples[label].append(text.lower())
    
    def generate(self, start_text, length=80):
        context = self._text_to_codes(start_text)
        result = start_text
        for _ in range(length):
            context_len = len(context)
            best_pattern = None
            best_match_len = 0
            best_next_chars = None
            for pattern, stability in self.stable_patterns.items():
                pattern_len = len(pattern)
                if pattern_len > context_len:
                    continue
                if tuple(context[-pattern_len:]) == pattern:
                    if pattern_len > best_match_len:
                        best_match_len = pattern_len
                        best_pattern = pattern
                        best_next_chars = self.pattern_next.get(pattern, [])
            if best_next_chars:
                best_next = max(best_next_chars, key=lambda x: x[1])
                result += best_next[0]
                new_codes = self._text_to_codes(best_next[0])
                context.extend(new_codes)
                if len(context) > 200:
                    context = context[-200:]
            else:
                break
        return result
    
    def predict(self, X):
        predictions = []
        for text in X:
            text_lower = text.lower()
            best_label = None
            best_sim = -1
            for label, examples in self.class_examples.items():
                for ex in examples[:10]:
                    min_len = min(len(text_lower), len(ex))
                    if min_len == 0:
                        sim = 0
                    else:
                        matches = sum(1 for i in range(min_len) if text_lower[i] == ex[i])
                        sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_label = label
            predictions.append(best_label if best_label is not None else 0)
        return np.array(predictions)


class Method4_TrigramPredictor:
    def __init__(self, n=3):
        self.n = n
        self.ngram_stats = {}
        self.class_examples = defaultdict(list)
        
    def fit(self, X, y):
        all_words = []
        for text in X:
            words = re.findall(r'\b\w+\b', text.lower())
            all_words.extend(words)
        print(f"  Слов: {len(all_words)}")
        
        for i in range(len(all_words) - self.n):
            ngram = tuple(all_words[i:i+self.n])
            next_word = all_words[i+self.n]
            if ngram not in self.ngram_stats:
                self.ngram_stats[ngram] = Counter()
            self.ngram_stats[ngram][next_word] += 1
        
        for ngram in self.ngram_stats:
            total = sum(self.ngram_stats[ngram].values())
            self.ngram_stats[ngram] = {word: count/total for word, count in self.ngram_stats[ngram].items()}
        print(f"  {self.n}-грамм: {len(self.ngram_stats)}")
        
        for text, label in zip(X, y):
            self.class_examples[label].append(text.lower())
    
    def generate(self, start_text, length=10):
        start_lower = start_text.lower()
        words = start_lower.split()
        if len(words) < self.n:
            return start_text
        result = words.copy()
        for _ in range(length):
            ngram = tuple(result[-self.n:])
            if ngram in self.ngram_stats:
                stats = self.ngram_stats[ngram]
                if stats:
                    next_word = max(stats, key=stats.get)
                    result.append(next_word)
                else:
                    break
            else:
                break
        return ' '.join(result)
    
    def predict(self, X):
        predictions = []
        for text in X:
            text_lower = text.lower()
            best_label = None
            best_sim = -1
            for label, examples in self.class_examples.items():
                for ex in examples[:10]:
                    min_len = min(len(text_lower), len(ex))
                    if min_len == 0:
                        sim = 0
                    else:
                        matches = sum(1 for i in range(min_len) if text_lower[i] == ex[i])
                        sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_label = label
            predictions.append(best_label if best_label is not None else 0)
        return np.array(predictions)


class Method5_FeatureVector:
    def __init__(self):
        self.stopatwords = set(['и', 'в', 'на', 'с', 'по', 'к', 'у', 'за', 'из', 'о', 'от', 'до', 'для',
                                 'а', 'но', 'или', 'что', 'как', 'так', 'это', 'был', 'его', 'ее'])
        self.classifiers = {}
        self.class_examples = defaultdict(list)
        
    def _extract_features(self, text):
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return np.zeros(20)
        word_lengths = [len(w) for w in words]
        freq = Counter(words)
        features = []
        features.append(len(words))
        features.append(np.mean(word_lengths))
        features.append(np.std(word_lengths))
        features.append(len(text))
        features.append(len(set(words)))
        features.append(len(set(words)) / len(words))
        stopwords_count = sum(1 for w in words if w in self.stopatwords)
        features.append(stopwords_count / len(words))
        features.append(np.mean(list(freq.values())))
        features.append(np.max(list(freq.values())))
        if len(word_lengths) > 1:
            features.append(np.mean([abs(word_lengths[i] - word_lengths[i+1]) for i in range(len(word_lengths)-1)]))
        else:
            features.append(0)
        short_words = sum(1 for w in words if len(w) <= 3)
        long_words = sum(1 for w in words if len(w) >= 7)
        features.append(short_words / len(words))
        features.append(long_words / len(words))
        features.append(1 if '?' in text else 0)
        features.append(1 if '!' in text else 0)
        features.append(text.count(','))
        max_len = max(word_lengths) if word_lengths else 1
        features.append(np.mean(word_lengths) / max_len)
        rare_letters = set(['ъ', 'ь', 'ы', 'э', 'щ', 'ф'])
        holes = sum(1 for ch in text if ch in rare_letters)
        features.append(holes / len(text) if len(text) > 0 else 0)
        return np.array(features[:20])
    
    def fit(self, X, y):
        class_vectors = defaultdict(list)
        for text, label in zip(X, y):
            vec = self._extract_features(text)
            class_vectors[label].append(vec)
            self.class_examples[label].append(text.lower())
        self.classifiers = {}
        for label, vectors in class_vectors.items():
            vectors_array = np.array(vectors)
            self.classifiers[label] = {'mean': np.mean(vectors_array, axis=0)}
        print(f"  Классов: {len(self.classifiers)}")
    
    def generate(self, start_text, length=80):
        start_lower = start_text.lower()
        vec = self._extract_features(start_lower)
        best_match = None
        best_sim = -1
        for label, examples in self.class_examples.items():
            for ex in examples[:20]:
                ex_vec = self._extract_features(ex)
                diff = vec - ex_vec
                distance = np.sqrt(np.sum(diff ** 2))
                similarity = 1 / (1 + distance)
                if similarity > best_sim:
                    best_sim = similarity
                    best_match = ex
        if best_match and len(best_match) > len(start_lower):
            return best_match[len(start_lower):][:length]
        return " [не найдено]"
    
    def predict(self, X):
        predictions = []
        for text in X:
            vec = self._extract_features(text)
            best_label = None
            best_sim = -1
            for label, classifier in self.classifiers.items():
                diff = vec - classifier['mean']
                distance = np.sqrt(np.sum(diff ** 2))
                similarity = 1 / (1 + distance)
                if similarity > best_sim:
                    best_sim = similarity
                    best_label = label
            predictions.append(best_label if best_label is not None else 0)
        return np.array(predictions)


class Method6_CNNPredictor:
    def __init__(self, word_height=8, word_width=32, conv_size=3):
        self.word_height = word_height
        self.word_width = word_width
        self.conv_size = conv_size
        self.char_to_code = {}
        self.conv_patterns_prob = {}
        self.class_examples = defaultdict(list)
        
    def _char_to_code(self, char):
        if char not in self.char_to_code:
            self.char_to_code[char] = len(self.char_to_code) + 1
        return self.char_to_code[char]
    
    def _word_to_image(self, word):
        img = np.zeros((self.word_height, self.word_width))
        for i, ch in enumerate(word[:self.word_width]):
            code = self._char_to_code(ch)
            normalized_code = (code % self.word_height) / self.word_height
            img[:, i] = normalized_code
        return img
    
    def _sentence_to_stack(self, sentence):
        words = re.findall(r'\b\w+\b', sentence.lower())
        stack = [self._word_to_image(w) for w in words[:20]]
        while len(stack) < 20:
            stack.append(np.zeros((self.word_height, self.word_width)))
        return np.array(stack)
    
    def _extract_conv_features(self, stack):
        n_words = stack.shape[0]
        conv_features = []
        for i in range(n_words - self.conv_size + 1):
            window = stack[i:i+self.conv_size]
            conv_feature = np.mean(window, axis=0).flatten()
            conv_features.append(conv_feature)
        return conv_features
    
    def fit(self, X, y):
        all_text = ' '.join(X)
        for ch in all_text:
            self._char_to_code(ch)
        print(f"  Символов: {len(self.char_to_code)}")
        
        all_conv = []
        for text in X:
            stack = self._sentence_to_stack(text)
            conv = self._extract_conv_features(stack)
            all_conv.extend(conv)
        
        patterns = defaultdict(list)
        for i in range(len(all_conv) - 1):
            pattern = tuple([round(x, 3) for x in all_conv[i][:20]])
            next_feature = tuple([round(x, 3) for x in all_conv[i+1][:20]])
            patterns[pattern].append(next_feature)
        
        self.conv_patterns_prob = {}
        for pattern, next_list in patterns.items():
            counter = Counter(next_list)
            total = len(next_list)
            self.conv_patterns_prob[pattern] = {p: count/total for p, count in counter.items()}
        print(f"  Паттернов: {len(self.conv_patterns_prob)}")
        
        for text, label in zip(X, y):
            self.class_examples[label].append(text.lower())
    
    def generate(self, start_text, length=80):
        best_match = None
        best_sim = -1
        for label, examples in self.class_examples.items():
            for ex in examples[:20]:
                min_len = min(len(start_text), len(ex))
                if min_len > 0:
                    matches = sum(1 for i in range(min_len) if start_text[i] == ex[i])
                    sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_match = ex
        if best_match and len(best_match) > len(start_text):
            return best_match[len(start_text):][:length]
        return " [не найдено]"
    
    def predict(self, X):
        predictions = []
        for text in X:
            text_lower = text.lower()
            best_label = None
            best_sim = -1
            for label, examples in self.class_examples.items():
                for ex in examples[:10]:
                    min_len = min(len(text_lower), len(ex))
                    if min_len == 0:
                        sim = 0
                    else:
                        matches = sum(1 for i in range(min_len) if text_lower[i] == ex[i])
                        sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_label = label
            predictions.append(best_label if best_label is not None else 0)
        return np.array(predictions)


class Method7_ColorCoding:
    def __init__(self, word_height=8, word_width=32):
        self.word_height = word_height
        self.word_width = word_width
        self.word_freq = defaultdict(int)
        self.class_examples = defaultdict(list)
        
    def _char_to_code(self, char):
        if char not in self.char_to_code:
            self.char_to_code[char] = len(self.char_to_code) + 1
        return self.char_to_code[char]
    
    def _word_to_color_image(self, word, position, total_words):
        word_lower = word.lower()
        freq = self.word_freq.get(word_lower, 0)
        word_len = min(len(word), self.word_width) / self.word_width
        position_norm = position / total_words if total_words > 0 else 0.5
        img = np.zeros((self.word_height, self.word_width, 3))
        for col in range(min(self.word_width, len(word))):
            img[:, col, 0] = freq
            img[:, col, 1] = word_len
            img[:, col, 2] = position_norm
        return img
    
    def _sentence_to_color_stack(self, sentence):
        words = re.findall(r'\b\w+\b', sentence.lower())
        stack = [self._word_to_color_image(w, i, len(words)) for i, w in enumerate(words[:20])]
        while len(stack) < 20:
            stack.append(np.zeros((self.word_height, self.word_width, 3)))
        return np.array(stack)
    
    def fit(self, X, y):
        for text in X:
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                self.word_freq[word] += 1
        max_freq = max(self.word_freq.values()) if self.word_freq else 1
        for word in self.word_freq:
            self.word_freq[word] = self.word_freq[word] / max_freq
        
        for text, label in zip(X, y):
            self.class_examples[label].append(text.lower())
        print(f"  Слов: {len(self.word_freq)}")
    
    def generate(self, start_text, length=80):
        best_match = None
        best_sim = -1
        for label, examples in self.class_examples.items():
            for ex in examples[:20]:
                min_len = min(len(start_text), len(ex))
                if min_len > 0:
                    matches = sum(1 for i in range(min_len) if start_text[i] == ex[i])
                    sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_match = ex
        if best_match and len(best_match) > len(start_text):
            return best_match[len(start_text):][:length]
        return " [не найдено]"
    
    def predict(self, X):
        predictions = []
        for text in X:
            text_lower = text.lower()
            best_label = None
            best_sim = -1
            for label, examples in self.class_examples.items():
                for ex in examples[:10]:
                    min_len = min(len(text_lower), len(ex))
                    if min_len == 0:
                        sim = 0
                    else:
                        matches = sum(1 for i in range(min_len) if text_lower[i] == ex[i])
                        sim = matches / min_len
                    if sim > best_sim:
                        best_sim = sim
                        best_label = label
            predictions.append(best_label if best_label is not None else 0)
        return np.array(predictions)


class EnsembleOrchestra:
    def __init__(self):
        self.methods = []
        self.weights = []
        self.names = []
    
    def add_method(self, name, method):
        self.methods.append(method)
        self.names.append(name)
    
    def fit(self, X_train, y_train, X_val, y_val):
        val_accuracies = []
        for i, name in enumerate(self.names):
            print(f"\n{name}...")
            start = time.time()
            self.methods[i].fit(X_train, y_train)
            y_pred = self.methods[i].predict(X_val)
            acc = accuracy_score(y_val, y_pred)
            val_accuracies.append(acc)
            print(f"  Точность: {acc:.2%}, Время: {time.time()-start:.1f} сек")
        
        total = sum(val_accuracies)
        self.weights = [acc / total for acc in val_accuracies]
        print("\nВЕСА:", [f"{w:.3f}" for w in self.weights])
        return self
    
    def predict(self, X):
        all_preds = np.array([m.predict(X) for m in self.methods])
        final = []
        for j in range(len(X)):
            votes = {}
            for i in range(len(self.methods)):
                p = all_preds[i][j]
                votes[p] = votes.get(p, 0) + self.weights[i]
            final.append(max(votes, key=votes.get))
        return np.array(final)
    
    def generate(self, start_text, length=80):
        best_idx = np.argmax(self.weights)
        return self.methods[best_idx].generate(start_text, length)


def run_sequence_visual_test():
    print("\n" + "=" * 80)
    print("ТЕСТ 4: ГИБРИД 7 МЕТОДОВ")
    print("=" * 80)
    
    full_text = load_text('text')
    sentences = re.split(r'[.!?]\s+', full_text)
    sentences = [s.strip() for s in sentences if 20 < len(s) < 200]
    
    labels = []
    for sent in sentences:
        sent_lower = sent.lower()
        if "война" in sent_lower or "смерть" in sent_lower or "убить" in sent_lower:
            labels.append(0)
        elif "любовь" in sent_lower or "сердце" in sent_lower or "счастье" in sent_lower:
            labels.append(1)
        else:
            labels.append(2)
    
    X_train, X_temp, y_train, y_temp = train_test_split(sentences, labels, test_size=0.4, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    
    print(f"\nTrain: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    
    m1 = Method1_CharPatterns(pattern_length=5)
    m2 = Method2_StickHierarchy(phrase_len=3)
    m3 = Method3_CodePatterns(window_size=100, pattern_min_len=3, pattern_max_len=10)
    m4 = Method4_TrigramPredictor(n=3)
    m5 = Method5_FeatureVector()
    m6 = Method6_CNNPredictor(word_height=8, word_width=32, conv_size=3)
    m7 = Method7_ColorCoding(word_height=8, word_width=32)
    
    ensemble = EnsembleOrchestra()
    ensemble.add_method("M1_CharPatterns", m1)
    ensemble.add_method("M2_StickHierarchy", m2)
    ensemble.add_method("M3_CodePatterns", m3)
    ensemble.add_method("M4_Trigram", m4)
    ensemble.add_method("M5_FeatureVector", m5)
    ensemble.add_method("M6_CNN", m6)
    ensemble.add_method("M7_ColorCoding", m7)
    
    ensemble.fit(X_train, y_train, X_val, y_val)
    
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ НА ТЕСТЕ")
    print("=" * 80)
    
    p1 = m1.predict(X_test)
    p2 = m2.predict(X_test)
    p3 = m3.predict(X_test)
    p4 = m4.predict(X_test)
    p5 = m5.predict(X_test)
    p6 = m6.predict(X_test)
    p7 = m7.predict(X_test)
    pe = ensemble.predict(X_test)
    
    print(f"M1_CharPatterns:   {accuracy_score(y_test, p1):.2%}")
    print(f"M2_StickHierarchy: {accuracy_score(y_test, p2):.2%}")
    print(f"M3_CodePatterns:   {accuracy_score(y_test, p3):.2%}")
    print(f"M4_Trigram:        {accuracy_score(y_test, p4):.2%}")
    print(f"M5_FeatureVector:  {accuracy_score(y_test, p5):.2%}")
    print(f"M6_CNN:            {accuracy_score(y_test, p6):.2%}")
    print(f"M7_ColorCoding:    {accuracy_score(y_test, p7):.2%}")
    print(f"ОРКЕСТР:           {accuracy_score(y_test, pe):.2%}")
    
    print("\n" + "=" * 80)
    print("ГЕНЕРАЦИЯ ВСЕМИ МЕТОДАМИ")
    print("=" * 80)
    
    starts = ["В лесу родилась", "Он вошел в комнату"]
    
    for start in starts:
        print(f"\nНАЧАЛО: {start}")
        print(f"  M1_CharPatterns:   {m1.generate(start, 60)}")
        print(f"  M2_StickHierarchy: {m2.generate(start, 8)}")
        print(f"  M3_CodePatterns:   {m3.generate(start, 60)}")
        print(f"  M4_Trigram:        {m4.generate(start, 8)}")
        print(f"  M5_FeatureVector:  {m5.generate(start, 60)}")
        print(f"  M6_CNN:            {m6.generate(start, 60)}")
        print(f"  M7_ColorCoding:    {m7.generate(start, 60)}")
        print(f"  ОРКЕСТР:           {ensemble.generate(start, 60)}")
    
    best_single = max(accuracy_score(y_test, p1), accuracy_score(y_test, p2), 
                      accuracy_score(y_test, p3), accuracy_score(y_test, p4),
                      accuracy_score(y_test, p5), accuracy_score(y_test, p6),
                      accuracy_score(y_test, p7))
    
    print("\n" + "=" * 80)
    if accuracy_score(y_test, pe) > best_single:
        print(f"✅ ОРКЕСТР ЛУЧШЕ: {accuracy_score(y_test, pe):.2%} > {best_single:.2%}")
    elif accuracy_score(y_test, pe) == best_single:
        print(f"⚠️ ОРКЕСТР РАВЕН ЛУЧШЕМУ: {accuracy_score(y_test, pe):.2%}")
    else:
        print(f"❌ ОРКЕСТР ХУЖЕ: {accuracy_score(y_test, pe):.2%} < {best_single:.2%}")
    print("=" * 80)
    
    return accuracy_score(y_test, pe)


if __name__ == "__main__":
    run_sequence_visual_test()
