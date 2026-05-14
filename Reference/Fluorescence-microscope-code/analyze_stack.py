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

def score_tenengrad(image):
    """2. 【Tenengrad】 Sobel 梯度平方和 (梯度類)"""
    gx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    gradient_sq = gx**2 + gy**2
    return np.mean(gradient_sq)

def score_spatial_frequency(image):
    """3. 【Spatial Frequency】 空間頻率"""
    img = image.astype(np.float32)
    rf = np.diff(img, axis=0)
    cf = np.diff(img, axis=1)
    rf_score = np.mean(rf**2)
    cf_score = np.mean(cf**2)
    return np.sqrt(rf_score + cf_score)

def score_fluo_morph_sobel(image):
    """4. 【Fluo (0.1%)】 螢光專用 (Morph + Top 0.1% Peaks)"""
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
    return np.mean(top_gradients ** 2)


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
        "Spatial Frequency": [],
        "Tenengrad": [],
        "Fluo (0.1%)": []
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
        results["Spatial Frequency"].append(score_spatial_frequency(gray))
        results["Tenengrad"].append(score_tenengrad(gray))
        results["Fluo (0.1%)"].append(score_fluo_morph_sobel(gray))

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
        
        print(f"--- 正在繪製 {method_name} ---")
        print(f"    數值範圍: {min_v:.4f} 到 {max_v:.4f}")

        if max_v - min_v == 0:
            norm_scores = scores_arr
        else:
            norm_scores = (scores_arr - min_v) / (max_v - min_v)
        
        ls = linestyles[i % len(linestyles)]
        mk = markers[i % len(markers)]
        
        plt.plot(sorted_positions, norm_scores, label=method_name, 
                 linewidth=2.0,  # 稍微加粗
                 linestyle=ls,
                 marker=mk,
                 markersize=8,   # 稍微加大標記
                 markevery=10,
                 alpha=0.9)

    plt.xlabel("Z Position (um)", fontsize=12)
    plt.ylabel("Normalized Score", fontsize=12)
    
    plt.legend(fontsize=12, loc='best', frameon=True, shadow=True) # 強化圖例顯示
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