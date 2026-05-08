import numpy as np
import cv2
from scipy.fft import fft2, ifft2
import matplotlib.pyplot as plt
import os
import glob

class PatternIlluminatedFP:
    def __init__(self, img_shape, pixel_size, na, wavelength):
        """
        初始化 PIFP 重建器
        """
        self.img_shape = img_shape
        self.pixel_size = pixel_size
        self.na = na
        self.wavelength = wavelength
        
        # 預先計算非相干光學轉換函數 (Incoherent OTF)
        self.otf = self._generate_incoherent_otf()

    def _generate_incoherent_otf(self):
        ny, nx = self.img_shape
        ky = np.fft.fftfreq(ny, d=self.pixel_size)
        kx = np.fft.fftfreq(nx, d=self.pixel_size)
        KX, KY = np.meshgrid(kx, ky)
        
        rho = np.sqrt(KX**2 + KY**2)
        
        # 截止頻率 (Cutoff frequency)
        k0 = 2 * self.na / self.wavelength
        rho_norm = rho / k0
        
        otf = np.zeros_like(rho)
        mask = rho_norm <= 1.0
        otf[mask] = (2 / np.pi) * (np.arccos(rho_norm[mask]) - rho_norm[mask] * np.sqrt(1 - rho_norm[mask]**2))
        
        otf = otf / (otf.max() + 1e-10)
        return otf

    def _shift_pattern(self, pattern, shift):
        """在頻域進行圖案平移"""
        dy, dx = shift
        ny, nx = pattern.shape
        ky = np.fft.fftfreq(ny)
        kx = np.fft.fftfreq(nx)
        KX, KY = np.meshgrid(kx, ky)
        
        phase_shift = np.exp(-1j * 2 * np.pi * (KX * dx + KY * dy))
        
        f_pattern = fft2(pattern)
        return np.abs(ifft2(f_pattern * phase_shift))

    def reconstruct(self, measurements, shifts, iterations=20, tolerance=1e-4, patience=3, min_improvement=0.002):
        """
        執行迭代重建
        """
        # --- 初始化 ---
        I_obj = np.mean(measurements, axis=0)
        # 初始猜測：照明圖案為均勻光
        P = np.mean(measurements) * np.ones(self.img_shape)
        
        errors = []
        patience_counter = 0
        prev_mse = float('inf')
        
        print(f"開始重建 (Max Iterations: {iterations}, Tolerance: {tolerance}, Min Improvement: {min_improvement:.2%})...")
        
        for it in range(iterations):
            current_mse = 0
            I_obj_prev = I_obj.copy()
            
            for n, (meas, shift) in enumerate(zip(measurements, shifts)):
                
                # Step 1: 產生當前照明圖案 Pn
                Pn = self._shift_pattern(P, shift)
                
                # Step 2.1: 目標影像估計
                Itn = I_obj * Pn
                
                # Step 2.2: 頻域更新
                F_Itn = fft2(Itn)
                F_meas = fft2(meas)
                
                model_spectrum = F_Itn * self.otf
                diff_spectrum = F_meas - model_spectrum
                F_Itn_updated = F_Itn + self.otf * diff_spectrum
                
                Itn_updated = np.real(ifft2(F_Itn_updated))
                
                # Step 2.3: 空間域更新物體
                Pn_max2 = np.max(Pn)**2 + 1e-8
                diff_spatial = Itn_updated - I_obj * Pn
                
                alpha = Pn / Pn_max2
                I_obj = I_obj + alpha * diff_spatial
                I_obj = np.maximum(I_obj, 0)
                
                # Step 2.4: 更新照明圖案 (Blind Update)
                Iobj_max2 = np.max(I_obj)**2 + 1e-8
                beta = I_obj / Iobj_max2
                
                Pn_updated = Pn + beta * diff_spatial
                Pn_updated = np.maximum(Pn_updated, 0)
                
                # 更新全域照明 P
                P = self._shift_pattern(Pn_updated, (-shift[0], -shift[1]))

                current_mse += np.mean(diff_spatial**2)

            errors.append(current_mse)
            
            # 計算改善率 (Relative Improvement)
            improvement = (prev_mse - current_mse) / prev_mse if prev_mse != float('inf') else 1.0
            
            # 相對變化量 (Relative Change of Object)
            diff_norm = np.linalg.norm(I_obj - I_obj_prev) / (np.linalg.norm(I_obj_prev) + 1e-9)
            
            print(f"Iter {it+1:02d}/{iterations:02d}, MSE: {current_mse:.6f}, Rel. Change: {diff_norm:.6f}, Improv: {improvement:.4%}")
            
            # 收斂檢測 1: 若變化量極小，直接停止
            if diff_norm < tolerance:
                print(f"已收斂 (Rel. Change < {tolerance})，停止迭代。")
                break
            
            # 收斂檢測 2: 若進步緩慢 (板塊檢測)，連扣耐心值
            if improvement < min_improvement:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"進步微乎其微 (連續 {patience} 次沒達標)，觸發收斂停止。")
                    break
            else:
                # 若有顯著改善，重置耐心點數
                patience_counter = 0
                
            prev_mse = current_mse
                
        return I_obj, P, errors

def main():
    # =========================================================================
    #                                參數配置區
    # =========================================================================
    
    # 1. 檔案路徑設定
    config_paths = {
        "aligned_folder": r"C:\Users\chen0\Documents\fluorescence\pifp_algorithm\alignment",
        "shift_filename": "pattern_shifts.npy",
        "valid_extensions": ('.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp')
    }

    # 2. 硬體與光學參數
    config_hardware = {
        # Pi Camera v2 (IMX219) Native pixel = 1.12um
        # 1640x1232 解析度為 2x2 Binning 模式 -> 2.24um
        "sensor_pixel_size_um": 1.12*4,

        "alignment_upscale": 1.0,
        "magnification": 20,         # 物鏡放大倍率
        "na": 0.46,                    # 物鏡數值孔徑
        "wavelength_um": 0.525         # 發射波長 (例如 GFP=0.525)
    }

    # 3. 演算法重建參數
    config_algo = {
        "max_iterations": 10,          # 最大迭代次數
        "tolerance": 1e-4,             # 相對變化量容許值
        "patience": 3,                 # 耐心次數 (連續 N 次沒進步才停)
        "min_improvement": 0.002       # 最小進步率 (0.2%)
    }
    
    # =========================================================================
    
    # 計算樣品平面的有效像素大小
    pixel_size = (config_hardware["sensor_pixel_size_um"] / config_hardware["magnification"]) / config_hardware["alignment_upscale"]
    print(f"硬體參數確認:")
    print(f"  - Sensor Pixel (Binned): {config_hardware['sensor_pixel_size_um']} um")
    print(f"  - Magnification: {config_hardware['magnification']}x")
    print(f"  - Effective Pixel Size: {pixel_size:.4f} um")
    print("-" * 30)

    # 讀取數據
    folder = config_paths["aligned_folder"]
    print(f"讀取資料夾: {folder}")
    
    image_paths = sorted([
        os.path.join(folder, f) 
        for f in os.listdir(folder) 
        if f.lower().endswith(config_paths["valid_extensions"])
    ])

    if not image_paths:
        print("錯誤：找不到任何影像檔案。")
        return

    images = []
    for p in image_paths:
        # 讀取影像 (保持原始灰階數據)
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            continue

        # 正規化到 0.0 ~ 1.0
        img = img.astype(np.float32) / 255.0
        
        # [備註]：不執行 De-hazing，保留 Raw 數據特徵
        images.append(img)
    
    if not images:
        print("沒有成功讀取到任何影像。")
        return

    h, w = images[0].shape
    print(f"影像尺寸: {h}x{w}, 數量: {len(images)}")
    
    # 讀取位移
    shift_path = os.path.join(folder, config_paths["shift_filename"])
    if not os.path.exists(shift_path):
        print("錯誤：找不到 pattern_shifts.npy 位移檔。")
        return
    shifts = np.load(shift_path)
    
    # 執行重建
    solver = PatternIlluminatedFP(
        (h, w), 
        pixel_size, 
        config_hardware["na"], 
        config_hardware["wavelength_um"]
    )
    
    recon_obj, recon_pattern, errors = solver.reconstruct(
        images, 
        shifts, 
        iterations=config_algo["max_iterations"],
        tolerance=config_algo["tolerance"],
        patience=config_algo["patience"],
        min_improvement=config_algo["min_improvement"]
    )
    
    # =========================================================================
    #                                視覺化結果 (已更新)
    # =========================================================================
    
    # 找出中間索引 (基準面)
    mid_idx = len(images) // 2
    # 計算寬場影像 (Widefield)，即所有已對齊影像的平均
    widefield_img = np.mean(images, axis=0)

    plt.figure(figsize=(18, 5))
    
    # 1. 顯示基準影像 (中間那張)
    plt.subplot(1, 4, 1)
    plt.title(f"Reference Frame (idx:{mid_idx})")
    plt.imshow(images[mid_idx], cmap='gray')
    plt.axis('off')
    
    # 2. 顯示寬場影像 (平均值)
    plt.subplot(1, 4, 2)
    plt.title("Widefield (Mean of All)")
    plt.imshow(widefield_img, cmap='gray')
    plt.axis('off')
    
    # 3. 顯示 PIFP 重建結果
    plt.subplot(1, 4, 3)
    plt.title("PIFP Reconstructed")
    # 可選：若想增強對比度，可以加上 vmax=np.percentile(recon_obj, 99.5)
    plt.imshow(recon_obj, cmap='gray') 
    plt.axis('off')
    
    # 4. 顯示還原出的照明圖案 (Pattern)
    plt.subplot(1, 4, 4)
    plt.title("Recovered Pattern")
    plt.imshow(recon_pattern, cmap='gray')
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # 額外：誤差收斂曲線
    plt.figure(figsize=(6, 4))
    plt.plot(errors, marker='o', markersize=4)
    plt.title(f"Convergence Plot (Tol={config_algo['tolerance']})")
    plt.xlabel("Iteration")
    plt.ylabel("Total MSE Loss")
    plt.grid(True)
    plt.show()

    # =========================================================================
    #                                儲存檔案區塊
    # =========================================================================
    
    # 將浮點數矩陣正規化轉換為 0-255 的 uint8 格式，方便儲存成一般圖片
    wf_uint8 = cv2.normalize(widefield_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    recon_uint8 = cv2.normalize(recon_obj, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # 1. 獨立儲存寬場影像 (Widefield)
    cv2.imwrite("Result_Widefield.png", wf_uint8)
    print("寬場影像已獨立儲存為 Result_Widefield.png")
    
    # 2. 獨立儲存重建影像 (Reconstructed)
    cv2.imwrite("Result_Reconstructed.png", recon_uint8)
    print("重建影像已獨立儲存為 Result_Reconstructed.png")

if __name__ == "__main__":
    main()