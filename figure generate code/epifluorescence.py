import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 1. 建立畫布與基本設定
fig, ax = plt.subplots(figsize=(10, 12))
plt.rc('font', family='sans-serif')
ax.set_xlim(0, 10)
ax.set_ylim(0, 11)
ax.axis('off') # 隱藏座標軸

# 定義顏色
color_exc = '#1f77b4' # 激發光 (藍色)
color_emi = '#2ca02c' # 發射螢光 (綠色)
color_component = '#eeeeee' # 光學元件底色

# 2. 繪製光學元件
# (A) 光源 (Light Source)
ax.add_patch(patches.Rectangle((0.5, 4.5), 1.5, 1, facecolor=color_component, edgecolor='black', lw=2))
ax.text(0.6, 5.0, 'Light Source\n(LED/Laser)', ha='left', va='center', fontsize=12, fontweight='bold')

# (B) 濾光方塊邊界 (Filter Cube Outline - 虛線框)
ax.add_patch(patches.Rectangle((3.5, 3.5), 3, 3, fill=False, edgecolor='gray', linestyle='dashed', lw=2))
ax.text(6.8, 6.2, 'Filter Cube', color='gray', fontsize=12, fontweight='bold', ha='left')

# (C) 激發濾波片 (Excitation Filter)
ax.add_patch(patches.Rectangle((3.6, 4.2), 0.4, 1.6, facecolor=color_exc, alpha=0.5, edgecolor='black', lw=2))
ax.text(2.2, 4.5, 'Excitation\nFilter', ha='left', va='center', fontsize=12, color=color_exc, fontweight='bold')

# (D) 雙色分光鏡 (Dichroic Mirror - 45度角)
ax.plot([4.2, 5.8], [4.2, 5.8], color='silver', lw=4, solid_capstyle='round')
ax.plot([4.2, 5.8], [4.2, 5.8], color='black', lw=1, linestyle='dashed') # 增加質感
ax.text(6.8, 5.0, 'Dichroic\nMirror', ha='left', va='center', fontsize=12, fontweight='bold')

# (E) 發射濾波片 (Emission Filter)
ax.add_patch(patches.Rectangle((4.2, 3.6), 1.6, 0.4, facecolor=color_emi, alpha=0.5, edgecolor='black', lw=2))
ax.text(6.8, 3.8, 'Emission\nFilter', ha='left', va='center', fontsize=12, color=color_emi, fontweight='bold')

# (F) 物鏡 (Objective Lens)
ax.add_patch(patches.Rectangle((4.6, 6.8), 0.8, 1.2, facecolor=color_component, edgecolor='black', lw=2))
ax.text(6.8, 7.4, 'Objective\nLens', ha='left', va='center', fontsize=12, fontweight='bold')

# (G) 樣本 (Sample)
ax.plot([3.5, 6.5], [8.5, 8.5], color='black', lw=2)
ax.text(6.8, 8.5, 'Sample', ha='left', va='center', fontsize=12, fontweight='bold')

# (H) 相機感測器 (Camera Sensor)
ax.add_patch(patches.Rectangle((4.0, 1.6), 2.0, 0.3, facecolor='#555555', edgecolor='black', lw=2))
ax.text(6.8, 1.75, 'Camera\nSensor', ha='left', va='center', fontsize=12, color='black', fontweight='bold')

# 3. 繪製光路徑 (Arrows)
arrow_style = "Simple, tail_width=2, head_width=8, head_length=10"

# --- 激發光路徑 (Excitation Path - Blue) ---
# 光源到雙色分光鏡
ax.add_patch(patches.FancyArrowPatch((2.0, 5.0), (4.8, 5.0), color=color_exc, alpha=0.8, arrowstyle=arrow_style))
# 雙色分光鏡反射向上到物鏡與樣本 (稍微偏左以區分螢光)
ax.add_patch(patches.FancyArrowPatch((4.8, 5.2), (4.8, 8.5), color=color_exc, alpha=0.8, arrowstyle=arrow_style))

# --- 發射光路徑 (Emission Path - Green) ---
# 樣本向下發出螢光穿透物鏡與分光鏡 (稍微偏右以區分激發光)
ax.add_patch(patches.FancyArrowPatch((5.2, 8.5), (5.2, 4.8), color=color_emi, alpha=0.8, arrowstyle=arrow_style))
# 穿透分光鏡與發射濾片進入相機
ax.add_patch(patches.FancyArrowPatch((5.2, 4.6), (5.2, 1.9), color=color_emi, alpha=0.8, arrowstyle=arrow_style))

# 4. 輸出與儲存
plt.tight_layout()
plt.savefig('epifluorescence_lightpath.svg', format='svg', bbox_inches='tight', transparent=True)
plt.savefig('epifluorescence_lightpath.png', dpi=300, bbox_inches='tight', transparent=True)

print("光路圖已成功儲存為 epifluorescence_lightpath.svg 與 epifluorescence_lightpath.png")
plt.show()