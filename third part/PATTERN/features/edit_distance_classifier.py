import numpy as np

class EditDistanceClassifier:
    """
    Классификатор на основе edit distance.
    НИКАКОГО ОБУЧЕНИЯ! Просто сравнивает с эталонами.
    """
    
    def __init__(self):
        self.prototypes = []
        self.is_trained = False
    
    def _make_prototype(self, images):
        """
        Создаёт эталон: пиксель чёрный, если он есть в >50% картинок
        Это даёт ЧЁТКОЕ изображение без размытия
        """
        if len(images) == 0:
            return np.zeros((28, 28), dtype=np.uint8)
        
        # Бинаризуем все картинки
        binary_images = np.array([(img > 128).astype(np.uint8) for img in images])
        
        # Считаем частоту чёрных пикселей
        frequency = np.mean(binary_images, axis=0)
        
        # Порог >50% - пиксель считается чёрным
        prototype = (frequency > 0.5).astype(np.uint8) * 255
        
        return prototype
    
    def train(self, X, y):
        """
        Создаёт эталоны из обучающей выборки
        X: изображения, y: метки
        """
        print("\n📊 СОЗДАНИЕ ЭТАЛОНОВ ДЛЯ EDIT DISTANCE")
        print("   (без обучения, только усреднение)")
        
        self.prototypes = []
        for digit in range(10):
            digit_images = X[y.flatten() == digit]
            if len(digit_images) > 0:
                prototype = self._make_prototype(digit_images)
                self.prototypes.append(prototype)
                black_pixels = np.sum(prototype > 128)
                print(f"  Цифра {digit}: эталон из {len(digit_images)} картинок, {black_pixels} чёрных пикселей")
            else:
                self.prototypes.append(np.zeros((28, 28), dtype=np.uint8))
                print(f"  Цифра {digit}: нет данных")
        
        self.is_trained = True
        print("  ✅ Эталоны созданы")
    
    def _hamming_distance(self, img, prototype):
        """
        Расстояние Хэмминга = количество разных пикселей
        Это и есть минимальное количество операций!
        """
        binary_img = (img > 128).astype(np.uint8)
        binary_proto = (prototype > 128).astype(np.uint8)
        
        # Количество пикселей, которые отличаются
        diff = np.sum(binary_img != binary_proto)
        
        return diff
    
    def _weighted_distance(self, img, prototype):
        """
        Взвешенное расстояние: 
        - ошибки на границе цифры важнее (штраф больше)
        - ошибки внутри цифры или на фоне - меньше
        """
        binary_img = (img > 128).astype(np.uint8)
        binary_proto = (prototype > 128).astype(np.uint8)
        
        # Находим границу эталона
        from scipy import ndimage
        boundary = ndimage.binary_erosion(binary_proto) ^ binary_proto
        
        # Веса: граница = 3, остальное = 1
        weights = np.ones_like(binary_proto, dtype=np.float32)
        weights[boundary] = 3.0
        
        # Взвешенная разница
        diff = np.sum(weights * (binary_img != binary_proto))
        
        return diff
    
    def predict(self, X, use_weighted=True):
        """
        Предсказание: находим эталон с минимальным расстоянием
        """
        if not self.is_trained:
            raise ValueError("Сначала вызовите train()")
        
        predictions = []
        
        for img in X:
            distances = []
            for digit, prototype in enumerate(self.prototypes):
                if np.sum(prototype) == 0:
                    distances.append(999)  # нет эталона
                elif use_weighted:
                    dist = self._weighted_distance(img, prototype)
                    distances.append(dist)
                else:
                    dist = self._hamming_distance(img, prototype)
                    distances.append(dist)
            
            # Выбираем цифру с минимальным расстоянием
            predictions.append(np.argmin(distances))
        
        return np.array(predictions).reshape(-1, 1)
    
    def predict_with_distances(self, X):
        """
        Возвращает предсказания и все расстояния
        """
        if not self.is_trained:
            raise ValueError("Сначала вызовите train()")
        
        all_distances = []
        predictions = []
        
        for img in X:
            distances = []
            for digit, prototype in enumerate(self.prototypes):
                if np.sum(prototype) == 0:
                    distances.append(999)
                else:
                    dist = self._weighted_distance(img, prototype)
                    distances.append(dist)
            
            all_distances.append(distances)
            predictions.append(np.argmin(distances))
        
        return np.array(predictions).reshape(-1, 1), np.array(all_distances)
    
    def score(self, X, y):
        y_pred = self.predict(X)
        y_true = y.flatten() if len(y.shape) > 1 else y
        return np.mean(y_pred.flatten() == y_true)
