# analyze_stack.py
import cv2
import numpy as np
import os
import csv
import matplotlib.pyplot as plt
# 移除了 tkinter

# --- 各種對焦演算法 (Metrics) ---

def score_variance(image):
    """1. 【Variance】 標準變異數法 (統計類)"""
    return np.var(image)

def score_sobel_energy(image):
    """2. 【Sobel Energy】 梯度能量 (梯度類)"""
    image = image.astype(np.float32)
    gx = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    return np.mean(magnitude ** 2)

def score_laplacian_variance(image):
    """3. 【Laplacian Variance】 二階微分變異數 (二階導數類)"""
    lap = cv2.Laplacian(image, cv2.CV_64F, ksize=3)
    return np.var(lap)

def score_tenengrad(image):
    """4. 【Tenengrad】 Sobel 梯度平方和 (梯度類)"""
    gx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    gradient_sq = gx**2 + gy**2
    return np.mean(gradient_sq)

def score_brenner(image):
    """5. 【Brenner】 相隔兩點差分平方和 (計算快速)"""
    image = image.astype(np.float32)
    diff_x = image[:, 2:] - image[:, :-2]
    return np.mean(diff_x ** 2)

def score_fluo_morph_sobel(image):
    """
    6. 【Fluo Original】 (螢光專用)
    邏輯: Morphological Opening (去鬼影) + Sobel Edge + Top 0.1% Peaks
    """
    img_float = image.astype(np.float32)

    # 去鬼影
    kernel_size = 13 
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    structure_only = cv2.morphologyEx(img_float, cv2.MORPH_OPEN, kernel)
    blurred = cv2.GaussianBlur(structure_only, (5, 5), 0)

    # Sobel
    gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    
    # 取前 0.1%
    flat_mag = magnitude.flatten()
    total_pixels = len(flat_mag)
    if total_pixels == 0: return 0.0
    
    top_n_count = int(total_pixels * 0.001) 
    if top_n_count < 10: top_n_count = 10
    
    top_gradients = np.partition(flat_mag, -top_n_count)[-top_n_count:]
    score = np.mean(top_gradients ** 2)

    return score

def score_bandpass_var(image):
    """
    7. 【Bandpass Var】 帶通變異數
    過濾掉超大型光暈(大於31x31像素)，只保留中小型細胞結構的變異數，可用於克服大光暈造成的錯誤全局巔峰。
    """
    img_float = image.astype(np.float32)
    blurred = cv2.GaussianBlur(img_float, (31, 31), 0)
    bandpass = np.abs(img_float - blurred)
    return np.var(bandpass)

def score_sobel_var(image):
    """
    8. 【Sobel Var】 梯度變異數
    與單純算 Sobel 總量不同，此計算梯度的「變異程度」，能展現強烈的單峰特性。
    """
    img_float = image.astype(np.float32)
    gx = cv2.Sobel(img_float, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(img_float, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    return np.var(mag)

def score_vollath_f4(image):
    """
    9. 【Vollath F4】 相關性類指標
    公式: sum(I(x,y)*I(x+1,y)) - sum(I(x,y)*I(x+2,y))
    在顯微鏡中以大範圍捕捉且穩定單峰著稱。
    """
    img = image.astype(np.float64)
    item1 = img[:, :-1] * img[:, 1:]
    item2 = img[:, :-2] * img[:, 2:]
    return np.mean(item1[:, :-1]) - np.mean(item2)

def score_spatial_frequency(image):
    """
    10. 【Spatial Frequency】 空間頻率
    結合水平與垂直方向的一階差分，對於大範圍離焦仍有殘餘信號。
    """
    img = image.astype(np.float32)
    rf = np.diff(img, axis=0)
    cf = np.diff(img, axis=1)
    rf_score = np.mean(rf**2)
    cf_score = np.mean(cf**2)
    return np.sqrt(rf_score + cf_score)

def score_sobel_l1(image):
    """
    11. 【Sobel L1】 絕對值梯度
    使用絕對值而非平方，通常能減緩雙峰效應並保有較寬的捕捉範圍。
    """
    img = image.astype(np.float32)
    gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.abs(gx) + np.abs(gy)
    return np.mean(mag)

# --- 主程式邏輯 ---

def analyze_folder(folder_path):
    print(f"=== 正在處理 {folder_path} ===")
    if not os.path.exists(folder_path):
        print(f"錯誤：找不到資料夾 {folder_path}")
        return

    csv_path = os.path.join(folder_path, "data_log.csv")
    if not os.path.exists(csv_path):
        print("錯誤：找不到 data_log.csv")
        return

    # 讀取 CSV
    data_map = {} 
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fname = row.get('Filename')
                pos_str = row.get('Position_um')
                if fname and pos_str:
                    data_map[fname] = float(pos_str)
    except Exception as e:
        print(f"讀取失敗: {e}")
        return

    sorted_files = sorted(data_map.keys(), key=lambda k: data_map[k])
    sorted_positions = [data_map[f] for f in sorted_files]

    print(f"開始分析 {len(sorted_files)} 張圖片...")

    # 初始化結果容器
    results = {
        "Variance": [],
        "Spatial Freq": []
    }

    total_files = len(sorted_files)
    for i, fname in enumerate(sorted_files):
        img_path = os.path.join(folder_path, fname)
        img = cv2.imread(img_path)
        
        if img is None:
            for k in results: results[k].append(0)
            continue

        gray = img[:, :, 1] # 使用綠色通道
        
        results["Variance"].append(score_variance(gray))
        results["Spatial Freq"].append(score_spatial_frequency(gray))

        if (i + 1) % 10 == 0:
            print(f"進度: {i + 1}/{total_files}...")

    # --- 繪圖設定 ---
    print("正在繪製圖表...")
    
    # 1. 設定字體系列 (使用 fallback 機制避免報錯)
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'Liberation Serif', 'serif']
    
    # 2. 設定全域字體大小為 12 (修改處)
    plt.rcParams['font.size'] = 12

    plt.figure(figsize=(14, 8))
    
    linestyles = ['-']
    markers = ['o', 's', '^', 'x', 'D', '*']
    
    for i, (method_name, scores) in enumerate(results.items()):
        scores_arr = np.array(scores, dtype=float)
        min_v = np.min(scores_arr)
        max_v = np.max(scores_arr)
        
        if max_v - min_v == 0:
            norm_scores = scores_arr
        else:
            norm_scores = (scores_arr - min_v) / (max_v - min_v)
        
        ls = linestyles[i % len(linestyles)]
        mk = markers[i % len(markers)]
        
        plt.plot(sorted_positions, norm_scores, label=method_name, 
                 linewidth=1.5,
                 linestyle=ls,
                 marker=mk,
                 markersize=6,
                 markevery=10,
                 alpha=0.8)

    # 修改：移除了 plt.title
    # 修改：字體大小 fontsize 改為 12
    plt.xlabel("Z Position (um)", fontsize=12)
    plt.ylabel("Normalized Score", fontsize=12)
    
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.axvline(x=0, color='k', linestyle=':', alpha=0.3)
    
    save_path = os.path.join(folder_path, "analysis_spaced_markers.png")
    plt.savefig(save_path)
    print(f"完成！圖表已存至: {save_path}\n")
    plt.close() # 關閉當前圖表以免堆疊

def analyze_all_folders():
    base_dir = r"/home/pi/Desktop/GUI/z_stack"
    if not os.path.exists(base_dir):
        print(f"找不到 base directory: {base_dir}")
        return
        
    for item in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, item)
        if os.path.isdir(folder_path):
            analyze_folder(folder_path)

if __name__ == "__main__":
    analyze_all_folders()