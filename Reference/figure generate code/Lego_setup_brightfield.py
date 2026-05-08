import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 1. 建立畫布與基本設定
fig, ax = plt.subplots(figsize=(10, 8))
plt.rc('font', family='sans-serif')
ax.set_xlim(-1, 9)
ax.set_ylim(0.5, 8.5)
ax.axis('off') # 隱藏座標軸

# 定義顏色
color_light = '#fff59d' # 白光 (淡黃色)
color_lens = '#a6cee3'  # 透鏡顏色
color_component = '#eeeeee' # 一般元件底色

# 2. 繪製核心光學元件 (垂直置中於 x=4.0, 等距間隔 1.3)

# (A) White LED (光源)
# Center (4.0, 7.35), Width 1.0, Height 0.8
ax.add_patch(patches.Rectangle((3.5, 6.95), 1.0, 0.8, facecolor=color_component, edgecolor='black', lw=2, zorder=2))

# (B) Condenser (聚光鏡)
# Center (4.0, 5.5), Width 1.6, Height 0.3
ax.add_patch(patches.Ellipse((4.0, 5.5), 1.6, 0.3, facecolor=color_lens, edgecolor='black', lw=2, zorder=2))

# (C) Sample (樣本)
# y=4.05
ax.plot([2.5, 5.5], [4.05, 4.05], color='black', lw=2, zorder=2)

# (D) Objective lens (物鏡) - 改為橢圓形
# Center (4.0, 2.6), Width 1.6, Height 0.3
ax.add_patch(patches.Ellipse((4.0, 2.6), 1.6, 0.3, facecolor=color_lens, edgecolor='black', lw=2, zorder=2))

# (E) Camera (相機)
# Center (4.0, 1.0), Width 2.0, Height 0.3
ax.add_patch(patches.Rectangle((3.0, 0.85), 2.0, 0.3, facecolor='#555555', edgecolor='black', lw=2, zorder=2))


# 3. 繪製光路徑 (Arrows)
arrow_style = "Simple, tail_width=3, head_width=10, head_length=12"

# 從 LED 經 Condenser 到 Sample
# 從 LED 底部 (4.0, 6.95) 到 Sample 上方 (4.0, 4.15)
ax.add_patch(patches.FancyArrowPatch((4.0, 6.95), (4.0, 4.15), color=color_light, alpha=0.8, arrowstyle=arrow_style, zorder=3))

# 從 Sample 經 Objective 到 Camera
# 從 Sample 下方 (4.0, 3.95) 到 Camera 上方 (4.0, 1.25)
ax.add_patch(patches.FancyArrowPatch((4.0, 3.95), (4.0, 1.25), color=color_light, alpha=0.8, arrowstyle=arrow_style, zorder=3))


# 4. 繪製標籤 (對齊右側 x=5.8)

# (A) White LED
ax.text(5.8, 7.35, 'White LED', va='center', ha='left', fontsize=12, fontweight='bold')

# (B) Condenser
ax.text(5.8, 5.5, 'Condenser', va='center', ha='left', fontsize=12, fontweight='bold')

# (C) Sample
ax.text(5.8, 4.05, 'Sample', va='center', ha='left', fontsize=12, fontweight='bold')

# (D) Objective lens
ax.text(5.8, 2.6, 'Objective lens', va='center', ha='left', fontsize=12, fontweight='bold')

# (E) Camera
ax.text(5.8, 1.0, 'Camera', va='center', ha='left', fontsize=12, fontweight='bold')


# 5. 輸出與儲存
plt.tight_layout()
plt.savefig('optical_components_brightfield.svg', format='svg', bbox_inches='tight', transparent=True)
plt.savefig('optical_components_brightfield.png', dpi=300, bbox_inches='tight', transparent=True)

print("明視野版光路圖已成功儲存為 optical_components_brightfield.svg 與 optical_components_brightfield.png")
plt.show()
