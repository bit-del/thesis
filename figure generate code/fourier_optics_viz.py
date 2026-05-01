import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift, ifft2

# 1. 建立高頻樣本 (Siemens Star 變體)
size = 1000
x = np.linspace(-10, 10, size)
xx, yy = np.meshgrid(x, x)
theta = np.arctan2(yy, xx)
r = np.sqrt(xx**2 + yy**2)

# 建立具有極細節的放射狀圖案 (高頻訊號)
spokes = 36
original = (np.sin(spokes * theta) > 0).astype(float)
# 加上一些極細的橫線
original += (np.sin(50 * xx) > 0.8).astype(float)
original = np.clip(original, 0, 1)

# 2. 計算傅立葉轉換 (頻譜)
spectrum = fftshift(fft2(original))
magnitude_spectrum = np.log(1 + np.abs(spectrum))

# 3. 模擬物鏡的低通濾波效果 (有限 NA)
# 建立一個圓形孔徑 (Pupil Function)
radius = 40 # 代表 NA/lambda 的限制
mask = (r < radius/10).astype(float) # 縮小尺度以適應頻譜空間
# 這裡手動建立一個在頻譜中心的圓
center = size // 2
Y, X = np.ogrid[:size, :size]
dist_from_center = np.sqrt((X - center)**2 + (Y - center)**2)
pupil = (dist_from_center <= radius).astype(float)

filtered_spectrum = spectrum * pupil
magnitude_filtered = np.log(1 + np.abs(filtered_spectrum))

# 4. 反傅立葉轉換 (成像結果)
reconstructed = np.abs(ifft2(fftshift(filtered_spectrum)))

# 5. 繪製 2x2 對比圖
fig, axes = plt.subplots(2, 2, figsize=(12, 12))
plt.rc('font', family='sans-serif')

# (A) 原始樣本
axes[0, 0].imshow(original, cmap='gray')
axes[0, 0].set_title('(a) Original Object\n(High Frequency Details)', fontsize=14, fontweight='bold')

# (B) 原始頻譜
axes[0, 1].imshow(magnitude_spectrum, cmap='magma')
axes[0, 1].set_title('(b) Fourier Spectrum\n(Full Bandwidth)', fontsize=14, fontweight='bold')

# (C) 經過物鏡孔徑限制的頻譜
axes[1, 1].imshow(magnitude_filtered, cmap='magma')
axes[1, 1].set_title('(c) Filtered Spectrum\n(Objective NA Limitation)', fontsize=14, fontweight='bold')

# (D) 最終成像結果
axes[1, 0].imshow(reconstructed, cmap='gray')
axes[1, 0].set_title('(d) Captured Image\n(Low-pass Filtered / Blurred)', fontsize=14, fontweight='bold')

for ax in axes.flatten():
    ax.axis('off')

plt.tight_layout()
plt.savefig('chap2_fig5_fourier_filtering.png', dpi=300, bbox_inches='tight')
print("傅立葉濾波原理圖已成功輸出！(chap2_fig5_fourier_filtering.png)")
plt.show()
