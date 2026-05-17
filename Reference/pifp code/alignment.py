import cv2
import numpy as np
import os
import glob
import shutil

def clear_or_create_folder(folder_path):
    """
    清空資料夾內的舊檔案。如果資料夾不存在，則建立它。
    """
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"警告：無法刪除 {file_path}，原因: {e}")
    else:
        os.makedirs(folder_path)

def preprocess_image_for_alignment(img):
    """
    形態學過濾預處理：消除背景微小雜訊，保留大面積特徵 (圓圈)。
    """
    # 1. 輕微的高斯模糊，柔化邊緣雜訊
    img_blur1 = cv2.GaussianBlur(img, (3, 3), 0)
    
    # 2. 形態學開運算 (設定為測試成功的 21x21)
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))
    img_opened = cv2.morphologyEx(img_blur1, cv2.MORPH_OPEN, kernel)
    
    # 3. 強化對比度
    img_float = img_opened.astype(np.float32)
    img_norm = cv2.normalize(img_float, None, 0, 1, cv2.NORM_MINMAX)
    
    # 4. 再次模糊，讓相位相關法尋找峰值時更平滑穩定
    img_final = cv2.GaussianBlur(img_norm, (5, 5), 0)
    
    return img_final

def get_shift_phase_correlation(ref_img, target_img):
    """
    使用相位相關法 (Phase Correlation) 計算位移
    """
    h, w = ref_img.shape
    hann = cv2.createHanningWindow((w, h), cv2.CV_32F)
    shift, response = cv2.phaseCorrelate(ref_img, target_img, window=hann)
    return shift, response

def main():
    # ================= 參數設定 =================
    input_folder = r"C:\Users\chen0\Documents\fluorescence\pifp_algorithm\database\pifp_data_0507_10x_A549_2"
    output_folder = r"C:\Users\chen0\Documents\fluorescence\pifp_algorithm\alignment"
    check_folder = r"C:\Users\chen0\Documents\fluorescence\pifp_algorithm\diff"
    save_shifts_file = "pattern_shifts.npy"
    upscale_factor = 2.0
    # ===========================================

    # 執行前先清空輸出資料夾，避免舊檔案殘留
    print("正在初始化與清空舊資料...")
    clear_or_create_folder(output_folder)
    clear_or_create_folder(check_folder)

    image_paths = sorted(glob.glob(os.path.join(input_folder, "*.tif")) + 
                         glob.glob(os.path.join(input_folder, "*.jpg")) + 
                         glob.glob(os.path.join(input_folder, "*.png")))
    
    if not image_paths:
        print("錯誤：找不到圖片，請檢查 input_folder 路徑是否正確。")
        return

    num_images = len(image_paths)
    mid_idx = num_images // 2
    print(f"共發現 {num_images} 張圖片，選取第 {mid_idx} 張作為基準面 (Reference Frame)...")
    
    # --- 處理基準影像 (Reference) ---
    ref_path = image_paths[mid_idx]
    ref_img_raw = cv2.imread(ref_path, cv2.IMREAD_GRAYSCALE)
    h, w = ref_img_raw.shape
    new_w, new_h = int(w * upscale_factor), int(h * upscale_factor)
    
    # 基準影像預處理
    ref_proc = preprocess_image_for_alignment(ref_img_raw)
    ref_img_rescaled = cv2.resize(ref_img_raw, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    pifp_shifts = [] 
    
    # --- 開始逐張對齊 ---
    for idx, path in enumerate(image_paths):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        
        if idx == mid_idx:
            dx, dy = 0.0, 0.0
            response = 1.0
            aligned_img = ref_img_rescaled
        else:
            # 1. 預處理 Target
            target_proc = preprocess_image_for_alignment(img)
            
            # 2. 計算相對於中間基準張的位移
            (dx, dy), response = get_shift_phase_correlation(ref_proc, target_proc)
            
            # 3. 執行配準
            M = np.float32([[upscale_factor, 0, -dx * upscale_factor], 
                            [0, upscale_factor, -dy * upscale_factor]])
            aligned_img = cv2.warpAffine(img, M, (new_w, new_h), flags=cv2.INTER_CUBIC)

        # 儲存位移資訊 (y, x)
        pifp_shifts.append((-dy * upscale_factor, -dx * upscale_factor))
        
        print(f"[{idx:03d}] Shift: (x={dx:6.2f}, y={dy:6.2f}), Conf: {response:.4f} {'(REF)' if idx==mid_idx else ''}")

        # 儲存對齊後的影像
        cv2.imwrite(os.path.join(output_folder, f"aligned_{idx:04d}.tif"), aligned_img)
        
        # 產生並儲存差異圖檢查 (Check)
        diff_img = cv2.absdiff(ref_img_rescaled, aligned_img)
        diff_vis = cv2.normalize(diff_img, None, 0, 255, cv2.NORM_MINMAX)
        combined_view = np.hstack((aligned_img, diff_vis))
        cv2.imwrite(os.path.join(check_folder, f"check_{idx:04d}.jpg"), combined_view)

    # 儲存最終位移矩陣
    np.save(os.path.join(output_folder, save_shifts_file), np.array(pifp_shifts))
    print(f"\n配準完成！所有檔案已更新至 {output_folder} 與 {check_folder} 資料夾。")

if __name__ == "__main__":
    main()