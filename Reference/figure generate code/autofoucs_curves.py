import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, sobel, grey_opening

# ---------------------------------------------------------
# 1. 初始化與畫布設定 (2x2 網格排版)
# ---------------------------------------------------------
plt.rc('font', family='sans-serif')
fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.subplots_adjust(hspace=0.3, wspace=0.2) # 調整上下左右間距

ax_bf_img = axes[0, 0]   # 左上：明場樣本影像
ax_fl_img = axes[0, 1]   # 右上：螢光樣本影像
ax_bf_curve = axes[1, 0] # 左下：明場對焦曲線
ax_fl_curve = axes[1, 1] # 右下：螢光對焦曲線

# ---------------------------------------------------------
# 2. 建立測試影像模型 (Siemens Star vs. Green Cells + Glow)
# ---------------------------------------------------------
size = 300 # 稍微縮小尺寸以加快運算速度，不影響趨勢
x = np.linspace(-10, 10, size)
xx, yy = np.meshgrid(x, x)
r = np.sqrt(xx**2 + yy**2)

# --- (A) 明場影像 (Siemens Star) ---
theta = np.arctan2(yy, xx)
spokes = 24
bf_base = (np.sin(spokes * theta) > 0).astype(float)
bf_base += np.random.normal(0, 0.05, (size, size))
bf_base = np.clip(bf_base, 0, 1)

# --- (B) 螢光影像 (Green Emission & Sharp Edges) ---
def sharp_disk(xx, yy, cx, cy, r):
    dist = np.sqrt((xx - cx)**2 + (yy - cy)**2)
    return (dist < r).astype(float)

cell1 = sharp_disk(xx, yy, 2, 1, 0.9) * 0.9
cell2 = sharp_disk(xx, yy, -1, -2, 1.1) * 0.85
cell3 = sharp_disk(xx, yy, -1.5, 2, 0.7) * 0.95
cells = cell1 + cell2 + cell3

glow_background = np.exp(-(r**2)/60) * 0.15 
fluo_intensity = cells + glow_background + np.random.normal(0, 0.005, (size, size))
fluo_intensity = np.clip(fluo_intensity, 0, 1)

# 將單通道轉為 RGB (純綠色)
fluo_rgb = np.zeros((size, size, 3))
fluo_rgb[:, :, 1] = fluo_intensity 

# 繪製上半部影像
ax_bf_img.imshow(bf_base, cmap='gray', vmin=0, vmax=1)
ax_bf_img.set_title('(A) Simulated Brightfield Sample\n(Siemens Star & Noise)', fontsize=16, fontweight='bold')
ax_bf_img.axis('off')

ax_fl_img.imshow(fluo_rgb)
ax_fl_img.set_title('(B) Simulated Fluorescence Sample\n(Green Emission & Glow)', fontsize=16, fontweight='bold')
ax_fl_img.axis('off')

# ---------------------------------------------------------
# 3. 量化模擬運算 (模擬 Z 軸脫焦)
# ---------------------------------------------------------
z_positions = np.linspace(-6, 6, 80)
bf_var, bf_sf, bf_brenner = [], [], []
fl_var, fl_centric = [], []

print("開始進行脫焦光學運算，請稍候...")

for z in z_positions:
    # 模擬光學繞射與脫焦模糊
    sigma = abs(z) * 1.5 + 0.5 
    
    # --- 明場運算 ---
    blur_bf = gaussian_filter(bf_base, sigma)
    bf_var.append(np.var(blur_bf))
    bf_sf.append(np.mean(np.diff(blur_bf, axis=0)**2) + np.mean(np.diff(blur_bf, axis=1)**2))
    bf_brenner.append(np.mean((blur_bf[2:, :] - blur_bf[:-2, :])**2))
    
    # --- 螢光運算 ---
    blur_fl = gaussian_filter(cells, sigma) + gaussian_filter(glow_background, sigma*2) + np.random.normal(0, 0.01, (size, size))
    fl_var.append(np.var(blur_fl))
    
    # Fluo-Centric 演算法 (形態學開運算 -> Sobel -> Top 0.1%)
    opened = grey_opening(blur_fl, size=(3, 3))
    sx = sobel(opened, axis=0)
    sy = sobel(opened, axis=1)
    grad = sx**2 + sy**2
    threshold = np.percentile(grad, 99.9)
    top_pixels = grad[grad >= threshold]
    fl_centric.append(np.mean(top_pixels) if len(top_pixels) > 0 else 0)

def normalize(data):
    return np.array(data) / np.max(data)

# ---------------------------------------------------------
# 4. 繪製下半部曲線圖
# ---------------------------------------------------------
# --- (C) 明場對焦曲線 ---
ax_bf_curve.plot(z_positions, normalize(bf_var), label='Stage 1-2: Global Variance', color='#1f77b4', lw=3, linestyle='-.')
ax_bf_curve.plot(z_positions, normalize(bf_brenner), label='Stage 3+: Brenner', color='#d62728', lw=3, linestyle='-')
ax_bf_curve.axvline(x=0, color='gray', linestyle=':', lw=2)
ax_bf_curve.set_title('(C) Brightfield Autofocus Response', fontsize=16, fontweight='bold')
ax_bf_curve.set_xlabel('Defocus Distance (Z-axis)', fontsize=14)
ax_bf_curve.set_ylabel('Normalized Metric Score', fontsize=14)
ax_bf_curve.legend(fontsize=12, loc='upper right')
ax_bf_curve.grid(True, alpha=0.3)

# --- (D) 螢光對焦曲線 ---
ax_fl_curve.plot(z_positions, normalize(fl_var), label='Stage 1-2: Global Variance', color='#1f77b4', lw=3, linestyle='-.')
ax_fl_curve.plot(z_positions, normalize(fl_centric), label='Stage 3+: Fluo-Centric (Morph+Sobel+Top0.1%)', color='#2ca02c', lw=3, linestyle='-')
ax_fl_curve.axvline(x=0, color='gray', linestyle=':', lw=2)
ax_fl_curve.set_title('(D) Fluorescence Autofocus Response', fontsize=16, fontweight='bold')
ax_fl_curve.set_xlabel('Defocus Distance (Z-axis)', fontsize=14)
ax_fl_curve.legend(fontsize=12, loc='upper right')
ax_fl_curve.grid(True, alpha=0.3)

# ---------------------------------------------------------
# 5. 輸出儲存
# ---------------------------------------------------------
plt.savefig('chap2_fig2_combined_af_simulation.svg', format='svg', transparent=True, bbox_inches='tight')
plt.savefig('chap2_fig2_combined_af_simulation.png', dpi=300, transparent=True, bbox_inches='tight')
print("合併圖表已成功輸出！(chap2_fig2_combined_af_simulation)")
plt.show()