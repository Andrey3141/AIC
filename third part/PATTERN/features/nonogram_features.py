import numpy as np

def extract_nonogram_features(img):
    """
    Японский кроссворд (Nonogram) как признак
    Превращаем картинку в последовательность чисел:
    - сколько подряд чёрных пикселей в каждой строке
    - сколько подряд чёрных пикселей в каждом столбце
    """
    binary = img > 128
    h, w = 28, 28
    
    # ============================================
    # 1. Nonogram по ГОРИЗОНТАЛИ (для каждой строки)
    # ============================================
    row_sequences = []
    for y in range(h):
        row = binary[y, :]
        lengths = []
        count = 0
        for x in range(w):
            if row[x]:
                count += 1
            else:
                if count > 0:
                    lengths.append(count)
                    count = 0
        if count > 0:
            lengths.append(count)
        
        if not lengths:
            lengths = [0]
        row_sequences.append(lengths)
    
    # ============================================
    # 2. Nonogram по ВЕРТИКАЛИ (для каждого столбца)
    # ============================================
    col_sequences = []
    for x in range(w):
        col = binary[:, x]
        lengths = []
        count = 0
        for y in range(h):
            if col[y]:
                count += 1
            else:
                if count > 0:
                    lengths.append(count)
                    count = 0
        if count > 0:
            lengths.append(count)
        
        if not lengths:
            lengths = [0]
        col_sequences.append(lengths)
    
    features = []
    
    # ============================================
    # 3. Статистики по всем длинам серий
    # ============================================
    all_row_lengths = []
    for seq in row_sequences:
        all_row_lengths.extend(seq)
    
    all_col_lengths = []
    for seq in col_sequences:
        all_col_lengths.extend(seq)
    
    if all_row_lengths:
        features.append(np.mean(all_row_lengths))      # средняя длина серии по горизонтали
        features.append(np.std(all_row_lengths))       # разброс
        features.append(np.max(all_row_lengths))       # максимальная серия
        features.append(np.median(all_row_lengths))    # медиана
    else:
        features.extend([0, 0, 0, 0])
    
    if all_col_lengths:
        features.append(np.mean(all_col_lengths))      # средняя длина серии по вертикали
        features.append(np.std(all_col_lengths))
        features.append(np.max(all_col_lengths))
        features.append(np.median(all_col_lengths))
    else:
        features.extend([0, 0, 0, 0])
    
    # ============================================
    # 4. Количество серий (сколько отрезков)
    # ============================================
    total_row_segments = sum(len(seq) for seq in row_sequences)
    total_col_segments = sum(len(seq) for seq in col_sequences)
    features.append(total_row_segments)
    features.append(total_col_segments)
    features.append(total_row_segments + total_col_segments)
    
    # ============================================
    # 5. Гистограмма длин серий (10 бинов)
    # ============================================
    hist_row, _ = np.histogram(all_row_lengths, bins=10, range=(1, 29))
    hist_col, _ = np.histogram(all_col_lengths, bins=10, range=(1, 29))
    
    hist_row_norm = hist_row / (len(all_row_lengths) + 1)
    hist_col_norm = hist_col / (len(all_col_lengths) + 1)
    
    features.extend(hist_row_norm)
    features.extend(hist_col_norm)
    
    # ============================================
    # 6. Первая серия в каждой строке (верхняя часть)
    # ============================================
    first_row_lengths = [seq[0] for seq in row_sequences if seq[0] > 0]
    first_col_lengths = [seq[0] for seq in col_sequences if seq[0] > 0]
    
    if first_row_lengths:
        features.append(np.mean(first_row_lengths))
        features.append(np.std(first_row_lengths))
        features.append(np.max(first_row_lengths))
    else:
        features.extend([0, 0, 0])
    
    if first_col_lengths:
        features.append(np.mean(first_col_lengths))
        features.append(np.std(first_col_lengths))
        features.append(np.max(first_col_lengths))
    else:
        features.extend([0, 0, 0])
    
    # ============================================
    # 7. Последняя серия (нижняя часть)
    # ============================================
    last_row_lengths = [seq[-1] for seq in row_sequences if seq[-1] > 0]
    last_col_lengths = [seq[-1] for seq in col_sequences if seq[-1] > 0]
    
    if last_row_lengths:
        features.append(np.mean(last_row_lengths))
        features.append(np.std(last_row_lengths))
    else:
        features.extend([0, 0])
    
    if last_col_lengths:
        features.append(np.mean(last_col_lengths))
        features.append(np.std(last_col_lengths))
    else:
        features.extend([0, 0])
    
    # ============================================
    # 8. Симметрия Nonogram (сравнение строк сверху и снизу)
    # ============================================
    sym_row = 0
    for i in range(14):
        top_len = len(row_sequences[i])
        bot_len = len(row_sequences[27 - i])
        if top_len == bot_len:
            sym_row += 1
    
    sym_col = 0
    for i in range(14):
        left_len = len(col_sequences[i])
        right_len = len(col_sequences[27 - i])
        if left_len == right_len:
            sym_col += 1
    
    features.append(sym_row / 14.0)
    features.append(sym_col / 14.0)
    
    # ============================================
    # 9. Сжатое представление Nonogram (как строка чисел)
    # ============================================
    flat = []
    for seq in row_sequences:
        flat.extend(seq[:4])  # первые 4 серии из каждой строки
    
    for seq in col_sequences:
        flat.extend(seq[:4])  # первые 4 серии из каждого столбца
    
    # Дополняем до 200 нулями
    if len(flat) > 200:
        flat = flat[:200]
    else:
        flat.extend([0] * (200 - len(flat)))
    
    features.extend(flat[:100])  # берём 100 признаков
    
    return np.array(features[:200])  # всего ~200 признаков
