import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, grey_erosion, grey_dilation, sobel

# 1. 基礎設定 (沿用您的設定)
size = 400 
x = np.linspace(-10, 10, size)
xx, yy = np.meshgrid(x, x)
r_sq = xx**2 + yy**2

def sharp_disk(xx, yy, cx, cy, r):
    dist = np.sqrt((xx - cx)**2 + (yy - cy)**2)
    return (dist < r).astype(float)

cells_base = sharp_disk(xx, yy, 2, 2, 1.2) * 0.9 + \
             sharp_disk(xx, yy, -2, -2, 1.5) * 0.8 + \
             sharp_disk(xx, yy, -3, 3, 0.8) * 0.95

# 2. 模擬場景
scenarios = [
    ('(I) In-Focus', 0.5, 15, 0.25),
    ('(II) Severe Defocus', 8.0, 150, 0.1)
]

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
plt.rc('font', family='sans-serif')

# 用於存儲結果以便統一色階
grad_results = []
top_scores = []

# 第一遍運算：計算所有梯度並找出全局最大值
for name, sigma, g_width, g_int in scenarios:
    glow = np.exp(-r_sq / g_width) * g_int
    original = gaussian_filter(cells_base, sigma=sigma) + glow + np.random.normal(0, 0.005, (size, size))
    original = np.clip(original, 0, 1)
    
    k_size = 21
    erosion = grey_erosion(original, size=(k_size, k_size))
    opening = grey_dilation(erosion, size=(k_size, k_size))
    
    sx = sobel(opening, axis=0)
    sy = sobel(opening, axis=1)
    grad = np.sqrt(sx**2 + sy**2)
    
    # 計算 Top 0.1% 能量分數 (量化重點)
    threshold = np.percentile(grad, 99.9)
    score = np.mean(grad[grad >= threshold])
    
    grad_results.append((original, opening, grad))
    top_scores.append(score)

# 設定統一的梯度最大值，確保對比度正確
global_grad_max = max([np.max(g[2]) for g in grad_results])

# 第二遍運算：繪圖
for row, (original, opening, grad) in enumerate(grad_results):
    name = scenarios[row][0]
    imgs = [original, opening, grad]
    titles = ['Original Image', 'After Opening', 'Focus Feature (Gradient)']
    
    for col, (img, title) in enumerate(zip(imgs, titles)):
        ax = axes[row, col]
        
        if col < 2:
            rgb = np.zeros((*img.shape, 3))
            rgb[:, :, 1] = np.clip(img, 0, 1)
            ax.imshow(rgb)
        else:
            # 關鍵修正：設定 vmin=0, vmax=global_grad_max，讓能量強度可被比較
            im_grad = ax.imshow(img, cmap='hot', vmin=0, vmax=global_grad_max)
            
            # 在梯度圖上標註 Top 0.1% 分數
            ax.text(size*0.05, size*0.9, f'Top 0.1% Score: {top_scores[row]:.4f}', 
                    color='white', fontsize=12, fontweight='bold', 
                    bbox=dict(facecolor='black', alpha=0.5))
            
            # 只有右側梯度圖需要 Colorbar 來顯示強度尺標
            if row == 0:
                cbar = fig.colorbar(im_grad, ax=ax, fraction=0.046, pad=0.04)
                cbar.set_label('Gradient Intensity', rotation=270, labelpad=15)

        if row == 0: ax.set_title(title, fontsize=16, fontweight='bold', pad=10)
        if col == 0: ax.set_ylabel(name, fontsize=16, fontweight='bold', labelpad=20)
        ax.set_xticks([]); ax.set_yticks([])

plt.tight_layout()
plt.savefig('chap2_fig3_morphology_quantitative_comparison.png', dpi=300, bbox_inches='tight')
plt.show()