import numpy as np
from scipy import ndimage, fftpack
from skimage.transform import resize
import warnings
warnings.filterwarnings('ignore')


def crop_to_digit(img):
    """Каскад Хаара: обрезка фона до границ цифры"""
    binary = img > 128
    y_coords, x_coords = np.where(binary)
    
    if len(y_coords) == 0:
        return img
    
    y_min, y_max = y_coords.min(), y_coords.max()
    x_min, x_max = x_coords.min(), x_coords.max()
    
    y_min = max(0, y_min - 2)
    y_max = min(27, y_max + 2)
    x_min = max(0, x_min - 2)
    x_max = min(27, x_max + 2)
    
    cropped = img[y_min:y_max+1, x_min:x_max+1]
    scaled = resize(cropped, (28, 28), mode='constant', preserve_range=True)
    
    return scaled.astype(np.uint8)


# ========== МЕТОД 1: ОРИГИНАЛЬНЫЕ ПРИЗНАКИ ==========
def extract_original_features(img):
    """Оригинальные признаки (плотности, моменты, HOG, LBP, FFT)"""
    binary = img > 128
    gray = img / 255.0
    
    y_coords, x_coords = np.where(binary)
    if len(y_coords) == 0:
        return np.zeros(543)
    
    features = []
    
    # 1. Плотности в сетках
    for size in [8, 4, 2]:
        step = 28 // size
        for i in range(size):
            for j in range(size):
                y_start, y_end = i*step, (i+1)*step
                x_start, x_end = j*step, (j+1)*step
                density = np.sum(binary[y_start:y_end, x_start:x_end]) / (step*step)
                features.append(density)
    
    # 2. Проекции
    hor_proj = np.sum(binary, axis=1) / 28
    ver_proj = np.sum(binary, axis=0) / 28
    features.extend(hor_proj)
    features.extend(ver_proj)
    
    # 3. Моменты до 5 порядка
    for p in range(6):
        for q in range(6-p):
            if len(y_coords) > 0:
                mu = np.mean((y_coords - np.mean(y_coords))**p * (x_coords - np.mean(x_coords))**q)
            else:
                mu = 0
            features.append(mu)
    
    # 4. HU моменты
    if len(y_coords) > 0:
        m00 = len(y_coords)
        cy = np.mean(y_coords)
        cx = np.mean(x_coords)
        
        mu20 = np.sum((y_coords - cy)**2) / m00
        mu02 = np.sum((x_coords - cx)**2) / m00
        mu11 = np.sum((y_coords - cy) * (x_coords - cx)) / m00
        mu30 = np.sum((y_coords - cy)**3) / m00
        mu03 = np.sum((x_coords - cx)**3) / m00
        mu12 = np.sum((y_coords - cy) * (x_coords - cx)**2) / m00
        mu21 = np.sum((y_coords - cy)**2 * (x_coords - cx)) / m00
        
        hu = [0]*7
        hu[0] = mu20 + mu02
        hu[1] = (mu20 - mu02)**2 + 4*mu11**2
        hu[2] = (mu30 - 3*mu12)**2 + (3*mu21 - mu03)**2
        hu[3] = (mu30 + mu12)**2 + (mu21 + mu03)**2
        hu[4] = (mu30 - 3*mu12)*(mu30 + mu12)*((mu30 + mu12)**2 - 3*(mu21 + mu03)**2) + (3*mu21 - mu03)*(mu21 + mu03)*(3*(mu30 + mu12)**2 - (mu21 + mu03)**2)
        hu[5] = (mu20 - mu02)*((mu30 + mu12)**2 - (mu21 + mu03)**2) + 4*mu11*(mu30 + mu12)*(mu21 + mu03)
        hu[6] = (3*mu21 - mu03)*(mu30 + mu12)*((mu30 + mu12)**2 - 3*(mu21 + mu03)**2) - (mu30 - 3*mu12)*(mu21 + mu03)*(3*(mu30 + mu12)**2 - (mu21 + mu03)**2)
        features.extend(hu)
    else:
        features.extend([0]*7)
    
    # 5. FFT радиальный спектр
    fft_img = np.fft.fft2(gray)
    fft_shift = np.fft.fftshift(fft_img)
    fft_energy = np.abs(fft_shift)
    center = 14
    for r in range(1, 15):
        mask = (np.arange(28)[:, None] - center)**2 + (np.arange(28) - center)**2 <= r**2
        mask_prev = (np.arange(28)[:, None] - center)**2 + (np.arange(28) - center)**2 <= (r-1)**2
        ring = ~mask_prev & mask
        if np.any(ring):
            features.append(np.mean(fft_energy[ring]))
        else:
            features.append(0)
    
    # 6. DCT коэффициенты
    dct_full = fftpack.dct(gray, type=2, norm='ortho')
    dct_low = dct_full[:7, :7].flatten()
    features.extend(dct_low)
    
    # 7. FFT амплитуды
    fft_amp = np.abs(np.fft.fft2(gray))
    fft_features = fft_amp[:5, :5].flatten()
    features.extend(fft_features)
    
    # 8. LBP гистограмма
    lbp_hist = np.zeros(256)
    for i in range(1, 27):
        for j in range(1, 27):
            if binary[i, j]:
                pattern = 0
                neighbors = [(-1,-1), (-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1)]
                for k, (di, dj) in enumerate(neighbors):
                    if binary[i+di, j+dj]:
                        pattern |= (1 << k)
                lbp_hist[pattern] += 1
    lbp_norm = lbp_hist / (np.sum(lbp_hist) + 1e-6)
    features.extend(lbp_norm[:50])
    
    # 9. HOG
    grad_y = np.gradient(gray)[0]
    grad_x = np.gradient(gray)[1]
    magnitude = np.sqrt(grad_x**2 + grad_y**2)
    orientation = np.arctan2(grad_y, grad_x)
    
    for cell_i in range(4):
        for cell_j in range(4):
            hist = np.zeros(9)
            for i in range(cell_i*7, (cell_i+1)*7):
                for j in range(cell_j*7, (cell_j+1)*7):
                    if i < 28 and j < 28:
                        ang = orientation[i, j] + np.pi
                        bin_idx = int(ang / (2*np.pi) * 9) % 9
                        hist[bin_idx] += magnitude[i, j]
            hist_norm = hist / (np.sum(hist) + 1e-6)
            features.extend(hist_norm)
    
    # 10. GLCM
    gray_8bit = (gray * 7).astype(int)
    glcm = np.zeros((8, 8))
    for i in range(27):
        for j in range(27):
            glcm[gray_8bit[i,j], gray_8bit[i+1,j]] += 1
            glcm[gray_8bit[i,j], gray_8bit[i,j+1]] += 1
    glcm_norm = glcm / (np.sum(glcm) + 1e-6)
    
    contrast = np.sum((np.arange(8)[:, None] - np.arange(8))**2 * glcm_norm)
    entropy = -np.sum(glcm_norm * np.log(glcm_norm + 1e-12))
    energy = np.sum(glcm_norm**2)
    features.extend([contrast, entropy, energy])
    
    # 11-20. Остальные признаки (дырки, компоненты, скелет, симметрии, пересечения, градиенты)
    labeled_inv, num_features = ndimage.label(~binary)
    features.append(max(0, num_features - 1))  # holes
    
    labeled, n_components = ndimage.label(binary)
    features.append(n_components)  # компоненты
    
    skeleton = binary.copy()
    for _ in range(15):
        eroded = ndimage.binary_erosion(skeleton)
        if np.array_equal(eroded, skeleton):
            break
        skeleton = eroded
    features.append(np.sum(skeleton))  # скелет
    
    # Симметрии
    left = binary[:, :14]
    right = np.fliplr(binary[:, 14:])
    min_w = min(left.shape[1], right.shape[1])
    if min_w > 0:
        features.append(np.mean(left[:, :min_w] == right[:, :min_w]))
    else:
        features.append(0)
    
    top = binary[:14, :]
    bottom = np.flipud(binary[14:, :])
    min_h = min(top.shape[0], bottom.shape[0])
    if min_h > 0:
        features.append(np.mean(top[:min_h, :] == bottom[:min_h, :]))
    else:
        features.append(0)
    
    features.append(np.trace(binary) / 28)
    features.append(np.trace(np.fliplr(binary)) / 28)
    
    # Радиальный и угловой профиль
    center = 14
    for r in range(1, 15):
        if len(y_coords) > 0:
            dists = np.sqrt((y_coords - center)**2 + (x_coords - center)**2)
            features.append(np.sum(dists <= r) / len(y_coords))
        else:
            features.append(0)
    
    if len(y_coords) > 0:
        angles = np.arctan2(y_coords - center, x_coords - center)
        for sector in range(32):
            angle_min = sector * 2 * np.pi / 32
            angle_max = (sector + 1) * 2 * np.pi / 32
            mask = (angles >= angle_min) & (angles < angle_max)
            features.append(np.sum(mask) / len(angles))
    else:
        features.extend([0]*32)
    
    # Периметр и компактность
    eroded = ndimage.binary_erosion(binary)
    perimeter = np.sum(binary) - np.sum(eroded)
    area = np.sum(binary)
    features.append(perimeter)
    features.append((perimeter**2) / (4 * np.pi * area + 1e-6))
    features.append(area / (28*28))
    
    # Ориентация
    if len(y_coords) > 2:
        coords = np.column_stack([x_coords, y_coords])
        cov = np.cov(coords.T)
        eigvals, eigvecs = np.linalg.eig(cov)
        major_idx = np.argmax(eigvals)
        features.append(np.arctan2(eigvecs[1, major_idx], eigvecs[0, major_idx]))
        features.append(np.sqrt(1 - eigvals[1-major_idx] / (eigvals[major_idx] + 1e-6)))
    else:
        features.extend([0, 0])
    
    # Пересечения
    for y in range(0, 28, 2):
        row = binary[y, :]
        transitions = np.sum(np.abs(np.diff(row.astype(int))))
        features.append(transitions // 2)
    for x in range(0, 28, 2):
        col = binary[:, x]
        transitions = np.sum(np.abs(np.diff(col.astype(int))))
        features.append(transitions // 2)
    
    # Градиенты
    grad_mag = np.sqrt(np.gradient(gray)[0]**2 + np.gradient(gray)[1]**2)
    features.append(np.mean(grad_mag))
    features.append(np.std(grad_mag))
    features.append(np.max(grad_mag))
    
    return np.array(features[:543])


# ========== МЕТОД 2: КООРДИНАТНЫЕ ПРИЗНАКИ ==========
def extract_coordinate_features(img):
    """Координаты точек, гистограммы, статистики"""
    binary = img > 128
    y_coords, x_coords = np.where(binary)
    
    if len(y_coords) == 0:
        return np.zeros(100)
    
    features = []
    
    y_norm = (y_coords - 14) / 14.0
    x_norm = (x_coords - 14) / 14.0
    
    # Статистики
    features.append(np.mean(x_norm))
    features.append(np.mean(y_norm))
    features.append(np.std(x_norm))
    features.append(np.std(y_norm))
    
    if len(x_norm) > 1:
        corr = np.corrcoef(x_norm, y_norm)[0, 1]
        features.append(corr if not np.isnan(corr) else 0)
    else:
        features.append(0)
    
    # Моменты
    features.append(np.mean((x_norm - np.mean(x_norm))**3) / (np.std(x_norm)**3 + 1e-6))
    features.append(np.mean((y_norm - np.mean(y_norm))**3) / (np.std(y_norm)**3 + 1e-6))
    features.append(np.mean((x_norm - np.mean(x_norm))**4) / (np.std(x_norm)**4 + 1e-6))
    features.append(np.mean((y_norm - np.mean(y_norm))**4) / (np.std(y_norm)**4 + 1e-6))
    
    # Расстояния от центра
    radii = np.sqrt(x_norm**2 + y_norm**2)
    features.append(np.mean(radii))
    features.append(np.std(radii))
    features.append(np.max(radii))
    features.append(np.percentile(radii, 90))
    
    # Углы
    angles = np.arctan2(y_norm, x_norm)
    features.append(np.mean(angles))
    features.append(np.std(angles))
    
    # Гистограммы
    x_hist, _ = np.histogram(x_norm, bins=8, range=(-1, 1))
    features.extend(x_hist / len(x_norm))
    y_hist, _ = np.histogram(y_norm, bins=8, range=(-1, 1))
    features.extend(y_hist / len(y_norm))
    r_hist, _ = np.histogram(radii, bins=8, range=(0, 1.5))
    features.extend(r_hist / len(radii))
    a_hist, _ = np.histogram(angles, bins=8, range=(-np.pi, np.pi))
    features.extend(a_hist / len(angles))
    
    # Квадранты
    quadrants = [
        (x_norm >= 0) & (y_norm >= 0),
        (x_norm < 0) & (y_norm >= 0),
        (x_norm < 0) & (y_norm < 0),
        (x_norm >= 0) & (y_norm < 0),
    ]
    for q in quadrants:
        features.append(np.sum(q) / len(x_norm))
    
    # Плотность и bounding box
    area = (np.max(x_norm) - np.min(x_norm)) * (np.max(y_norm) - np.min(y_norm))
    features.append(len(x_norm) / (area + 1e-6))
    features.append(np.max(x_norm) - np.min(x_norm))
    features.append(np.max(y_norm) - np.min(y_norm))
    features.append((np.max(x_norm) - np.min(x_norm)) / (np.max(y_norm) - np.min(y_norm) + 1e-6))
    
    return np.array(features[:100])


# ========== МЕТОД 3: CNN-ПОДОБНЫЕ ПРИЗНАКИ ==========
def extract_cnn_features(img):
    """Свёрточные фильтры, скользящие окна"""
    gray = img / 255.0
    
    features = []
    
    # Свёртка с ядрами
    kernels = [
        np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]]),
        np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]),
        np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]]),
        np.array([[-1, -1, 0], [-1, 0, 1], [0, 1, 1]]),
        np.array([[0, -1, -1], [1, 0, -1], [1, 1, 0]]),
        np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]]) / 9,
    ]
    
    for kernel in kernels:
        conv = ndimage.convolve(gray, kernel)
        features.append(np.mean(conv))
        features.append(np.std(conv))
        features.append(np.max(conv))
        features.append(np.min(conv))
    
    # Скользящие окна
    for i in range(0, 28, 4):
        for j in range(0, 28, 4):
            window = gray[i:i+4, j:j+4]
            if window.shape == (4, 4):
                features.append(np.mean(window))
                features.append(np.std(window))
                features.append(np.max(window))
    
    # Глобальные статистики
    features.append(np.mean(gray))
    features.append(np.std(gray))
    features.append(np.max(gray) - np.min(gray))
    features.append(np.percentile(gray, 25))
    features.append(np.percentile(gray, 50))
    features.append(np.percentile(gray, 75))
    
    # Частотные квадранты
    fft = np.fft.fft2(gray)
    fft_mag = np.abs(fft)
    features.append(np.mean(fft_mag[:14, :14]))
    features.append(np.mean(fft_mag[14:, 14:]))
    features.append(np.mean(fft_mag[:14, 14:]))
    features.append(np.mean(fft_mag[14:, :14]))
    
    return np.array(features[:500])


# ========== МЕТОД 4: ГОРИЗОНТАЛЬНО-ВЕРТИКАЛЬНЫЙ (относительное расположение) ==========
def extract_hv_features(img):
    """
    Анализ строк и столбцов:
    - Длина каждой строки (максимальный непрерывный отрезок)
    - Отношение текущей строки к следующей
    - Смещение центра строки относительно центра предыдущей
    - Вертикальный анализ аналогично
    """
    binary = img > 128
    
    # ===== ГОРИЗОНТАЛЬНЫЙ АНАЛИЗ =====
    row_info = []  # (длина, центр_x)
    for y in range(28):
        row = binary[y, :]
        
        # Находим непрерывные чёрные отрезки
        segments = []
        in_segment = False
        start = 0
        for x in range(28):
            if row[x] and not in_segment:
                in_segment = True
                start = x
            elif not row[x] and in_segment:
                end = x - 1
                length = end - start + 1
                center = (start + end) / 2
                segments.append((length, center))
                in_segment = False
        if in_segment:
            end = 27
            length = end - start + 1
            center = (start + end) / 2
            segments.append((length, center))
        
        if segments:
            # Берём самый длинный сегмент в строке
            max_seg = max(segments, key=lambda s: s[0])
            row_info.append(max_seg)
        else:
            row_info.append((0, 14))
    
    # Нормализуем длины строк (масштабная инвариантность)
    max_row_len = max(l for l, _ in row_info) if row_info else 1
    row_lengths_norm = [l / max_row_len for l, _ in row_info]
    
    # Вычисляем относительные признаки
    features = []
    
    # Длины строк (14 значений - сжимаем)
    for i in range(0, 28, 2):
        avg_len = (row_lengths_norm[i] + row_lengths_norm[min(i+1, 27)]) / 2
        features.append(avg_len)
    
    # Отношение текущей строки к следующей (соотношение соседних)
    for i in range(27):
        ratio = row_lengths_norm[i] / (row_lengths_norm[i+1] + 1e-6)
        features.append(min(ratio, 10))  # ограничиваем
    
    # Смещение центра строки относительно центра предыдущей
    centers = [c for _, c in row_info]
    for i in range(27):
        shift = (centers[i+1] - centers[i]) / 28
        features.append(shift)
    
    # ===== ВЕРТИКАЛЬНЫЙ АНАЛИЗ =====
    col_info = []
    for x in range(28):
        col = binary[:, x]
        
        segments = []
        in_segment = False
        start = 0
        for y in range(28):
            if col[y] and not in_segment:
                in_segment = True
                start = y
            elif not col[y] and in_segment:
                end = y - 1
                length = end - start + 1
                center = (start + end) / 2
                segments.append((length, center))
                in_segment = False
        if in_segment:
            end = 27
            length = end - start + 1
            center = (start + end) / 2
            segments.append((length, center))
        
        if segments:
            max_seg = max(segments, key=lambda s: s[0])
            col_info.append(max_seg)
        else:
            col_info.append((0, 14))
    
    max_col_len = max(l for l, _ in col_info) if col_info else 1
    col_lengths_norm = [l / max_col_len for l, _ in col_info]
    
    # Длины столбцов (14 значений)
    for i in range(0, 28, 2):
        avg_len = (col_lengths_norm[i] + col_lengths_norm[min(i+1, 27)]) / 2
        features.append(avg_len)
    
    # Отношение текущего столбца к следующему
    for i in range(27):
        ratio = col_lengths_norm[i] / (col_lengths_norm[i+1] + 1e-6)
        features.append(min(ratio, 10))
    
    # Смещение центра столбца
    col_centers = [c for _, c in col_info]
    for i in range(27):
        shift = (col_centers[i+1] - col_centers[i]) / 28
        features.append(shift)
    
    # ===== ОБЩИЕ ПРИЗНАКИ =====
    # Соотношение максимальной ширины к высоте
    max_width = max(row_lengths_norm)
    max_height = max(col_lengths_norm)
    features.append(max_width / (max_height + 1e-6))
    
    # Где находятся максимумы?
    features.append(np.argmax(row_lengths_norm) / 28)
    features.append(np.argmax(col_lengths_norm) / 28)
    
    # Количество пиков (длина > 0.5 от максимума)
    row_peaks = sum(1 for l in row_lengths_norm if l > 0.5)
    col_peaks = sum(1 for l in col_lengths_norm if l > 0.5)
    features.append(row_peaks / 28)
    features.append(col_peaks / 28)
    
    # Симметрия
    row_sym = 0
    for i in range(14):
        row_sym += abs(row_lengths_norm[i] - row_lengths_norm[27-i])
    features.append(row_sym / 14)
    
    col_sym = 0
    for i in range(14):
        col_sym += abs(col_lengths_norm[i] - col_lengths_norm[27-i])
    features.append(col_sym / 14)
    
    return np.array(features[:100])
