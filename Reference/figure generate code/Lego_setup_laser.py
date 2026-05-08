import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 1. 建立畫布與基本設定
fig, ax = plt.subplots(figsize=(10, 8))
plt.rc('font', family='sans-serif')
ax.set_xlim(-1, 9)
ax.set_ylim(0.5, 8.5)
ax.axis('off') # 隱藏座標軸

# 定義顏色
color_exc = '#1f77b4'  # 激發光 (藍色)
color_emi = '#2ca02c'  # 發射螢光 (綠色)
color_lens = '#a6cee3' # 透鏡顏色
color_component = '#eeeeee' # 一般元件底色

# 2. 繪製核心光學元件

# (A) Laser (光源) - 置中於 y=4.5
ax.add_patch(patches.Rectangle((0.2, 4.1), 1.0, 0.8, facecolor=color_component, edgecolor='black', lw=2, zorder=2))

# (B) Diffuser (擴散片) - 置中於 y=4.5
ax.add_patch(patches.Rectangle((2.5, 3.7), 0.3, 1.6, facecolor='#e0e0e0', alpha=0.8, edgecolor='black', lw=2, zorder=2))

# (C) Dichroic mirror (雙色分光鏡) - 中心在 y=4.5
ax.plot([4.0, 6.0], [3.5, 5.5], color='silver', lw=4, solid_capstyle='round', zorder=2)
ax.plot([4.0, 6.0], [3.5, 5.5], color='black', lw=1, linestyle='dashed', zorder=3)

# (D) Objective lens (物鏡) - 置中於 y=6.0 (DM與Sample的正中間)
ax.add_patch(patches.Ellipse((5.0, 6.0), 1.6, 0.3, facecolor=color_lens, edgecolor='black', lw=2, zorder=2))

# (E) Sample (樣本) - 維持 y=7.5
ax.plot([3.5, 6.5], [7.5, 7.5], color='black', lw=2, zorder=2)

# (F) Camera (相機) - 置中於 y=1.5
ax.add_patch(patches.Rectangle((4.0, 1.35), 2.0, 0.3, facecolor='#555555', edgecolor='black', lw=2, zorder=2))

# (G) Emission Filter (發射濾波片) - 置中於 y=3.0 (DM與Camera的正中間)
ax.add_patch(patches.Rectangle((4.2, 2.8), 1.6, 0.4, facecolor=color_emi, alpha=0.5, edgecolor='black', lw=2, zorder=2))


# 3. 繪製光路徑 (Arrows)
arrow_style = "Simple, tail_width=2, head_width=8, head_length=10"

# --- 激發光路徑 (Excitation Path - Blue) ---
# 光源 -> Dichroic
ax.add_patch(patches.FancyArrowPatch((1.2, 4.5), (5.1, 4.5), color=color_exc, alpha=0.8, arrowstyle=arrow_style, zorder=3))
# Dichroic -> Sample (穿透物鏡)
ax.add_patch(patches.FancyArrowPatch((5.1, 4.5), (5.1, 7.3), color=color_exc, alpha=0.8, arrowstyle=arrow_style, zorder=3))

# --- 發射光路徑 (Emission Path - Green) ---
# Sample -> Dichroic (穿透物鏡)
ax.add_patch(patches.FancyArrowPatch((4.9, 7.3), (4.9, 4.4), color=color_emi, alpha=0.8, arrowstyle=arrow_style, zorder=3))
# Dichroic -> Camera
ax.add_patch(patches.FancyArrowPatch((4.9, 4.4), (4.9, 1.7), color=color_emi, alpha=0.8, arrowstyle=arrow_style, zorder=3))


# 4. 繪製標籤 (維持在上方或右側)

# (A) Laser
ax.text(0.7, 4.5, 'Laser', va='center', ha='center', fontsize=10, fontweight='bold')

# (B) Diffuser
ax.text(2.65, 5.7, 'Diffuser', va='bottom', ha='center', fontsize=12, fontweight='bold')

# (C) Dichroic mirror
ax.text(6.8, 4.5, 'Dichroic mirror', va='center', ha='left', fontsize=12, fontweight='bold')

# (D) Objective lens
ax.text(6.8, 6.0, 'Objective lens', va='center', ha='left', fontsize=12, fontweight='bold')

# (E) Sample
ax.text(6.8, 7.5, 'Sample', va='center', ha='left', fontsize=12, fontweight='bold')

# (F) Camera
ax.text(6.8, 1.5, 'Camera', va='center', ha='left', fontsize=12, fontweight='bold')

# (G) Emission Filter
ax.text(6.8, 3.0, 'Emission filter', va='center', ha='left', fontsize=12, fontweight='bold')


# 5. 輸出與儲存
plt.tight_layout()
plt.savefig('optical_components_laser.svg', format='svg', bbox_inches='tight', transparent=True)
plt.savefig('optical_components_laser.png', dpi=300, bbox_inches='tight', transparent=True)

print("Laser版光路圖已成功儲存為 optical_components_laser.svg 與 optical_components_laser.png")
plt.show()