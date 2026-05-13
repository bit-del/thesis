import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Use standard sans-serif font for English
plt.rcParams['font.sans-serif'] = ['Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# Create figure
fig, ax = plt.subplots(figsize=(15, 9))
ax.set_xlim(0, 14)
ax.set_ylim(0, 9)
ax.axis('off')

# Helper function to draw a box
def draw_box(ax, text, xy, width, height, color='lightblue', fontsize=10):
    rect = patches.Rectangle(xy, width, height, linewidth=1.5, edgecolor='#2b2d42', facecolor=color, zorder=3)
    ax.add_patch(rect)
    # Add text
    cx = xy[0] + width / 2
    cy = xy[1] + height / 2
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fontsize, weight='bold', color='#2b2d42', zorder=4)

# Helper function to draw orthogonal arrows
def draw_orthogonal_arrow(ax, points, label='', color='black', label_pos='first'):
    # Draw lines for all segments except the last one
    for i in range(len(points) - 2):
        ax.plot([points[i][0], points[i+1][0]], [points[i][1], points[i+1][1]], color=color, linewidth=1.5, zorder=2)
    # Last segment with arrow
    p1 = points[-2]
    p2 = points[-1]
    arrow = patches.FancyArrowPatch(p1, p2, arrowstyle='->', mutation_scale=15, linewidth=1.5, color=color, zorder=2)
    ax.add_patch(arrow)
    
    if label:
        # Determine which segment to place the label on
        if label_pos == 'first' and len(points) >= 2:
            p_start = points[0]
            p_end = points[1]
        else:
            p_start = points[-2]
            p_end = points[-1]
            
        # Midpoint
        mx = (p_start[0] + p_end[0]) / 2
        my = (p_start[1] + p_end[1]) / 2
        # 將文字放在線條上方，不使用 bbox 以免遮擋線條
        ax.text(mx, my + 0.08, label, ha='center', va='bottom', fontsize=9, color=color, zorder=4)

# --- Draw Clusters ---
# Lower Control System (整體向右移，給予接線更多空間)
cluster1 = patches.Rectangle((4.2, 3.5), 9.2, 3.9, linewidth=1.5, edgecolor='#457b9d', facecolor='#f1faff', linestyle='--', zorder=1)
ax.add_patch(cluster1)
ax.text(4.4, 7.2, "Lower Control System", fontsize=12, color='#457b9d', weight='bold', va='top', zorder=4)

# Motion System 
cluster2 = patches.Rectangle((9.2, 3.8), 4.0, 3.3, linewidth=1.2, edgecolor='#2a9d8f', facecolor='#e6f4f1', linestyle='--', zorder=1)
ax.add_patch(cluster2)
ax.text(9.3, 7, "Motion System", fontsize=10, color='#2a9d8f', weight='bold', va='top', zorder=4)

# Light Source (已將名稱修改)
cluster3 = patches.Rectangle((4.2, 0.2), 9.2, 3.2, linewidth=1.5, edgecolor='#e63946', facecolor='#fff5f5', linestyle='--', zorder=1)
ax.add_patch(cluster3)
ax.text(4.4, 3.2, "Light Source", fontsize=12, color='#e63946', weight='bold', va='top', zorder=4)

# --- Draw Components ---
# Master Controller (稍微調高一點以騰出走線空間)
draw_box(ax, "Raspberry Pi 5\n(Master)", (0.5, 3.3), 1.8, 1.6, color='#a8dadc', fontsize=11)

# Image Input (往上移動，與 Lower Control 分離)
draw_box(ax, "Camera Module\n(Imaging)", (4.5, 7.8), 1.8, 0.8, color='#ffccd5', fontsize=10)

# Lower Controller Sequence (微調 Y 座標對齊中心點為 5.5)
draw_box(ax, "Arduino", (4.5, 5.1), 1.5, 0.8, color='#e0fbfc', fontsize=10)
draw_box(ax, "CNC Shield V3", (7.0, 5.1), 1.5, 0.8, color='#e0fbfc', fontsize=10)

# 3 Independent TMC2209 Drivers (Y 完全對齊 CNC Shield)
draw_box(ax, "TMC2209\n(X)", (9.5, 6.2), 1.3, 0.6, color='#ffe5ec', fontsize=10)
draw_box(ax, "TMC2209\n(Y)", (9.5, 5.2), 1.3, 0.6, color='#ffe5ec', fontsize=10)
draw_box(ax, "TMC2209\n(Z)", (9.5, 4.2), 1.3, 0.6, color='#ffe5ec', fontsize=10)

# Motion Components
draw_box(ax, "Motor X", (11.6, 6.2), 1.2, 0.6, color='#ffe5ec', fontsize=10)
draw_box(ax, "Motor Y", (11.6, 5.2), 1.2, 0.6, color='#ffe5ec', fontsize=10)
draw_box(ax, "Motor Z", (11.6, 4.2), 1.2, 0.6, color='#ffe5ec', fontsize=10)

# Light Path 1 (Fluo)
draw_box(ax, "Relay", (4.5, 2.1), 1.2, 0.8, color='#f4a261', fontsize=10)
draw_box(ax, "Buck\nConverter", (7.0, 2.1), 1.4, 0.8, color='#ffb703', fontsize=10)
draw_box(ax, "Fluo LED\nor Laser", (9.8, 2.1), 2.2, 0.8, color='#9b5de5', fontsize=10)

# Light Path 2 (Bright-field)
draw_box(ax, "Relay", (4.5, 0.7), 1.2, 0.8, color='#f4a261', fontsize=10)
draw_box(ax, "Buck\nConverter", (7.0, 0.7), 1.4, 0.8, color='#ffb703', fontsize=10)
draw_box(ax, "Bright-field\nLED", (9.8, 0.7), 2.2, 0.8, color='#fee440', fontsize=10)

# --- Draw Connections (Orthogonal) ---
# RPi to Camera (文字放置在最後一段水平線)
draw_orthogonal_arrow(ax, [(2.3, 4.6), (2.6, 4.6), (2.6, 8.2), (4.5, 8.2)], label='CSI Ribbon', color='#6c757d', label_pos='last')

# RPi to Arduino
draw_orthogonal_arrow(ax, [(2.3, 4.2), (3.0, 4.2), (3.0, 5.5), (4.5, 5.5)], label='USB (Serial)', color='#0077b6', label_pos='last')

# RPi to Relay 1 (Fluo) - 瀑布線：先往外延伸較長 (x=3.8) 再向下
draw_orthogonal_arrow(ax, [(2.3, 3.8), (3.8, 3.8), (3.8, 2.5), (4.5, 2.5)], label='GPIO Control', color='#e63946', label_pos='first')

# RPi to Relay 2 (BF) - 瀑布線：較早 (x=3.4) 就向下折
draw_orthogonal_arrow(ax, [(2.3, 3.4), (3.4, 3.4), (3.4, 1.1), (4.5, 1.1)], label='GPIO Control', color='#e63946', label_pos='first')

# Arduino to CNC Shield
draw_orthogonal_arrow(ax, [(6.0, 5.5), (7.0, 5.5)], color='#2b2d42')

# CNC Shield to 3x TMC2209 (中間那條線現在完全對齊平直)
draw_orthogonal_arrow(ax, [(8.5, 5.5), (8.9, 5.5), (8.9, 6.5), (9.5, 6.5)], color='#2b2d42')
draw_orthogonal_arrow(ax, [(8.5, 5.5), (9.5, 5.5)], color='#2b2d42') # 筆直對齊 Y 軸
draw_orthogonal_arrow(ax, [(8.5, 5.5), (8.9, 5.5), (8.9, 4.5), (9.5, 4.5)], color='#2b2d42')

# TMC2209 to Motors
draw_orthogonal_arrow(ax, [(10.8, 6.5), (11.6, 6.5)], color='#2b2d42')
draw_orthogonal_arrow(ax, [(10.8, 5.5), (11.6, 5.5)], color='#2b2d42')
draw_orthogonal_arrow(ax, [(10.8, 4.5), (11.6, 4.5)], color='#2b2d42')

# Light Path 1 Connections
draw_orthogonal_arrow(ax, [(5.7, 2.5), (7.0, 2.5)], color='#2b2d42')
draw_orthogonal_arrow(ax, [(8.4, 2.5), (9.8, 2.5)], color='#2b2d42')

# Light Path 2 Connections
draw_orthogonal_arrow(ax, [(5.7, 1.1), (7.0, 1.1)], color='#2b2d42')
draw_orthogonal_arrow(ax, [(8.4, 1.1), (9.8, 1.1)], color='#2b2d42')

plt.tight_layout()

# Save figure
output_path = "electronic_diagram.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Successfully generated chart and saved to {output_path}")