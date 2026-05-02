import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 建立畫布
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
plt.rc('font', family='sans-serif')

def draw_diffraction(ax, d, wavelength, title):
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    y_start = 2
    y_end = 8
    grating_height = y_end - y_start
    
    num_slits = int(grating_height / d)
    slit_width = d * 0.4
    
    # 畫出單一開口 (開口大小為 d)
    slit_center = 5
    slit_top = slit_center + d/2
    slit_bottom = slit_center - d/2
    
    # 畫出上下兩塊實體擋板 (稍微減細線條讓開口更明顯)
    ax.plot([4, 4], [y_start, slit_bottom], color='#555555', lw=4)
    ax.plot([4, 4], [slit_top, y_end], color='#555555', lw=4)
            
    # 入射平面波
    for i in range(5):
        x_pos = 1 + i * 0.6
        ax.plot([x_pos, x_pos], [y_start, y_end], color='#1f77b4', lw=2, alpha=0.6)
    
    # 入射波箭頭 (縮小寬度並精確定位，確保不遮擋小洞口)
    ax.arrow(0.5, 5, 3.2, 0, head_width=0.15, head_length=0.3, fc='#1f77b4', ec='#1f77b4', zorder=5)
    ax.text(1.8, 5.5, 'Incident Light', color='#1f77b4', fontsize=12, ha='center', va='bottom', 
            fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
    
    # 計算繞射角 theta = arcsin(lambda / d)
    theta = np.arcsin(wavelength / d)
    
    # 第 0 級繞射 (直射)
    ax.arrow(4.2, 5, 4, 0, head_width=0.2, head_length=0.3, fc='#d62728', ec='#d62728', alpha=0.3)
    
    # 第 +1 級繞射
    dx = 4 * np.cos(theta)
    dy = 4 * np.sin(theta)
    ax.arrow(4.2, 5, dx, dy, head_width=0.3, head_length=0.4, fc='#d62728', ec='#d62728', lw=2, zorder=6)
    ax.text(4.2 + dx + 0.5, 5 + dy, '$m=+1$', color='#d62728', fontsize=12, va='center', ha='left',
            fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=0.5))
    
    # 第 -1 級繞射
    ax.arrow(4.2, 5, dx, -dy, head_width=0.3, head_length=0.4, fc='#d62728', ec='#d62728', lw=2, zorder=6)
    ax.text(4.2 + dx + 0.5, 5 - dy, '$m=-1$', color='#d62728', fontsize=12, va='center', ha='left',
            fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=0.5))
    
    # 標示繞射角 theta
    arc = patches.Arc((4.2, 5), 3, 3, angle=0, theta1=0, theta2=np.degrees(theta), color='black', lw=1.5, linestyle='--')
    ax.add_patch(arc)
    ax.text(4.2 + 1.8 * np.cos(theta/2), 5 + 1.8 * np.sin(theta/2), r'$\theta$', fontsize=16, 
            fontweight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))
    
    # 設定標題與資訊
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    
    # 畫一個代表物鏡接收範圍的虛線弧 (NA)
    na_angle = np.radians(25)
    na_arc = patches.Arc((4.2, 5), 8, 8, angle=0, theta1=-np.degrees(na_angle), theta2=np.degrees(na_angle), color='green', lw=2, linestyle=':')
    ax.add_patch(na_arc)
    ax.plot([4.2, 4.2 + 4 * np.cos(na_angle)], [5, 5 + 4 * np.sin(na_angle)], color='green', linestyle=':', lw=2)
    ax.plot([4.2, 4.2 + 4 * np.cos(na_angle)], [5, 5 - 4 * np.sin(na_angle)], color='green', linestyle=':', lw=2)
    ax.text(9.2, 5, 'Objective\nAcceptance', color='green', fontsize=12, ha='left', va='center', 
            fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))

# 為了呈現明顯的多開口光柵效果，我們使用較小的 d 值
lambda_val = 0.15

# (A) 粗糙結構 (較大的間距 d) -> 產生的繞射角較小
draw_diffraction(ax1, d=0.5, wavelength=lambda_val, title="(A) Coarse Grating (Larger $d$)\nSmall Diffraction Angle $\\theta$")

# (B) 微細結構 (極小的間距 d) -> 產生的繞射角很大，超出 NA
draw_diffraction(ax2, d=0.2, wavelength=lambda_val, title="(B) Fine Grating (Smaller $d$)\nLarge Diffraction Angle $\\theta$ (Lost)")

plt.tight_layout()
plt.savefig('chap2_fig1_diffraction.png', dpi=300, bbox_inches='tight')
print("光柵繞射示意圖已成功輸出！(chap2_fig1_diffraction.png)")
