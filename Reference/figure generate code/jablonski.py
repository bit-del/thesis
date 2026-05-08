import matplotlib.pyplot as plt

# 設定畫布大小與字體風格（稍微加寬以容納水平文字）
plt.rc('font', family='sans-serif')
fig, ax = plt.subplots(figsize=(10, 6))

# 定義繪製能階的函式
def draw_energy_levels(x_start, y_base, num_levels, width, label, level_spacing=0.2):
    for i in range(num_levels):
        y = y_base + i * level_spacing
        # 最底層的能階使用較粗的線條代表主量子態
        lw = 3.0 if i == 0 else 1.0
        ax.plot([x_start, x_start + width], [y, y], color='black', linewidth=lw)
    # 添加能階標籤，統一設定為靠左對齊 (ha='left')
    ax.text(x_start - 0.7, y_base, label, fontsize=16, fontweight='bold', ha='left', va='center')

# 1. 繪製各個能階狀態 (稍微調整 X 軸位置拉開間距)
draw_energy_levels(x_start=1, y_base=0, num_levels=5, width=2.8, label='$S_0$')
draw_energy_levels(x_start=1, y_base=3, num_levels=5, width=2.8, label='$S_1$')
draw_energy_levels(x_start=5.5, y_base=2, num_levels=4, width=2.5, label='$T_1$')

# 2. 加入躍遷箭頭與標籤 (所有 text 皆設定 ha='left')
# 吸收 (Absorption) 
ax.annotate('', xy=(1.3, 3.8), xytext=(1.3, 0),
            arrowprops=dict(arrowstyle="->", color='#1f77b4', lw=2.5))
ax.text(1.4, 1.9, 'Absorption\n(Excitation)', color='#1f77b4', 
        ha='left', va='center', fontsize=12, fontweight='bold')

# 振動弛豫 (VR) 
ax.annotate('', xy=(2.3, 3.0), xytext=(2.3, 3.8),
            arrowprops=dict(arrowstyle="->", color='gray', ls='dashed', lw=1.5))
ax.text(2.4, 3.4, 'VR', color='gray', ha='left', va='center', fontsize=11)

# 螢光 (Fluorescence) 
ax.annotate('', xy=(3.3, 0), xytext=(3.3, 3.0),
            arrowprops=dict(arrowstyle="->", color='#2ca02c', lw=2.5))
ax.text(3.4, 1.5, 'Fluorescence\n(Emission)', color='#2ca02c', 
        ha='left', va='center', fontsize=12, fontweight='bold')

# 系統間穿越 (ISC) 
ax.annotate('', xy=(5.6, 2.0), xytext=(3.8, 3.0),
            arrowprops=dict(arrowstyle="->", color='gray', ls='dashed', lw=1.5, connectionstyle="arc3,rad=-0.2"))
ax.text(4.4, 2.7, 'ISC', color='gray', ha='left', va='center', fontsize=11)

# 磷光 (Phosphorescence) 
ax.annotate('', xy=(6.5, 0), xytext=(6.5, 2.0),
            arrowprops=dict(arrowstyle="->", color='#d62728', lw=2.5))
ax.text(6.6, 1.0, 'Phosphorescence', color='#d62728', 
        ha='left', va='center', fontsize=12, fontweight='bold')

# 3. 美化與輸出
# 隱藏外框與座標軸
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.get_xaxis().set_ticks([])
ax.get_yaxis().set_ticks([])

# 儲存為高解析度圖片
plt.tight_layout()
plt.savefig('jablonski_diagram.svg', format='svg', bbox_inches='tight', transparent=True)
plt.savefig('jablonski_diagram.png', dpi=300, bbox_inches='tight', transparent=True)

print("圖片已成功儲存為 jablonski_diagram.svg 與 jablonski_diagram.png")
plt.show()