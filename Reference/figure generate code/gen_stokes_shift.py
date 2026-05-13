import numpy as np
import matplotlib
matplotlib.use('Agg') # 使用非 GUI 後端
import matplotlib.pyplot as plt
from scipy.stats import norm

# 設定解析度與字體
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

def generate_stokes_shift_plot(save_path):
    x = np.linspace(350, 650, 1000)
    
    # 定義激發光與發射光的中心波長與寬度
    peak_ex = 470  # 藍光激發
    peak_em = 520  # 綠光發射
    std_dev = 15
    
    # 生成高斯曲線
    excitation = norm.pdf(x, peak_ex, std_dev)
    emission = norm.pdf(x, peak_em, std_dev)
    
    # 歸一化
    excitation /= np.max(excitation)
    emission /= np.max(emission)
    
    plt.figure(figsize=(10, 6), dpi=300)
    
    # 繪製曲線
    plt.plot(x, excitation, color='blue', lw=3, label='Excitation Spectrum')
    plt.fill_between(x, excitation, color='blue', alpha=0.2)
    
    plt.plot(x, emission, color='green', lw=3, label='Emission Spectrum')
    plt.fill_between(x, emission, color='green', alpha=0.2)
    
    # 標註峰值點
    plt.axvline(peak_ex, color='blue', linestyle='--', alpha=0.5)
    plt.axvline(peak_em, color='green', linestyle='--', alpha=0.5)
    
    # 標註 Stokes Shift 箭頭
    arrow_y = 0.5
    plt.annotate('', xy=(peak_em, arrow_y), xytext=(peak_ex, arrow_y),
                 arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    plt.text((peak_ex + peak_em) / 2, arrow_y + 0.05, 'Stokes Shift', 
             color='red', ha='center', fontsize=12, fontweight='bold')
    
    # 標註波長
    plt.text(peak_ex, -0.07, f'λex = {peak_ex} nm', color='blue', ha='center', fontsize=11)
    plt.text(peak_em, -0.07, f'λem = {peak_em} nm', color='green', ha='center', fontsize=11)
    
    # 圖表美化
    plt.title('Stokes Shift Concept Diagram', fontsize=16, pad=20)
    plt.xlabel('Wavelength (nm)', fontsize=14)
    plt.ylabel('Normalized Intensity (a.u.)', fontsize=14)
    plt.xlim(380, 620)
    plt.ylim(0, 1.0)
    plt.legend(loc='upper right', fontsize=12)
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"Image saved to: {save_path}")

if __name__ == "__main__":
    import os
    # 確保目錄存在
    if not os.path.exists('figures'):
        os.makedirs('figures')
    
    generate_stokes_shift_plot('figures/stokes_shift_plot.png')
