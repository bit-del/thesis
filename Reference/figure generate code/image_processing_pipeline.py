import graphviz
import os

font_name = "Times New Roman"
g = graphviz.Digraph('Image_Processing_Pipeline', format='png')

# 設定由左至右排版，適合流程圖
g.attr(rankdir='LR', splines='spline', nodesep='0.6', ranksep='0.8', fontname=font_name)
g.attr(compound='true', dpi='300')

# 全域節點樣式設定
g.attr('node', shape='rect', style='rounded,filled', fillcolor='#F8F9FA', color='#495057', 
       fontname=font_name, fontsize='13', margin='0.3,0.15')
g.attr('edge', fontname=font_name, fontsize='11', color='#495057')

# ==========================================
# 1. Input Layer
# ==========================================
g.node('RawIn', 'IMX708 Sensor\n(10-bit Bayer RAW)', shape='cylinder', fillcolor='#E3F2FD')

# ==========================================
# 2. Pre-processing & Basic Correction
# ==========================================
with g.subgraph(name='cluster_basic') as c_basic:
    c_basic.attr(label='Basic Correction', style='dashed', fontname=font_name)
    c_basic.node('Bayer', 'Bayer Demosaicing\n(Extract RGB Channels)')
    c_basic.node('BlackLevel', 'Sensor Black Level\nSubtraction')
    c_basic.node('BgSub', 'Fixed Background\nSubtraction\n(Optional)')

# ==========================================
# 3. Advanced Optical Correction
# ==========================================
with g.subgraph(name='cluster_advanced') as c_adv:
    c_adv.attr(label='Advanced Optical & Color Correction', style='dashed', fontname=font_name)
    c_adv.node('FlatField', 'Flat-Field Correction\n(Apply Gain Maps)', fillcolor='#FFF3E0', color='#FF9800')
    c_adv.node('Unmix', 'Fluorescence Color Unmixing\n(Spatial Tensor Math)', fillcolor='#FFF3E0', color='#FF9800', shape='component')
    c_adv.node('Denoise', 'Digital Gain & \nMedian Filtering')

# ==========================================
# 4. Output Layer
# ==========================================
with g.subgraph(name='cluster_output') as c_out:
    c_out.attr(label='Output Branching', style='dashed', fontname=font_name)
    c_out.node('ForceScale', 'Resolution Scaling\n(Stream Requirement)')
    c_out.node('Out16Bit', '16-bit Scientific Data\n(To Save Queue)', shape='folder', fillcolor='#F3E5F5')
    c_out.node('Out8Bit', '8-bit QImage / MJPEG\n(To Web UI)', shape='folder', fillcolor='#E8F5E9')

# ==========================================
# Routing
# ==========================================
g.edge('RawIn', 'Bayer')
g.edge('Bayer', 'BlackLevel')
g.edge('BlackLevel', 'BgSub')
g.edge('BgSub', 'FlatField')
g.edge('FlatField', 'Unmix')
g.edge('Unmix', 'Denoise')
g.edge('Denoise', 'ForceScale')

g.edge('ForceScale', 'Out16Bit', label=' Queue for I/O', color='#8E24AA')
g.edge('ForceScale', 'Out8Bit', label=' Real-time View', color='#4CAF50')

# Render
g.render('image_processing_pipeline', cleanup=True)
print("管線圖已生成：image_processing_pipeline.png")

if os.name == 'posix': os.system('open image_processing_pipeline.png')
elif os.name == 'nt': os.startfile('image_processing_pipeline.png')