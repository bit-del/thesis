import re

def group_stage_figures(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    stage_marker = r'\\subsubsection\{載台部分\}'
    next_section_marker = r'為了進一步提升實驗操作的便利性'
    
    stage_match = re.search(stage_marker, content)
    next_match = re.search(next_section_marker, content)
    
    if not (stage_match and next_match):
        print("Could not find sections!")
        return

    pre_stage = content[:stage_match.end()]
    stage_content = content[stage_match.end():next_match.start()]
    post_stage = content[next_match.start():]

    lines = stage_content.split('\n')
    text_blocks = []
    in_figure = False
    
    for line in lines:
        if line.strip().startswith('\\begin{figure}'):
            in_figure = True
        elif line.strip().startswith('\\end{figure}'):
            in_figure = False
            continue
        
        if not in_figure and not line.strip().startswith('\\centering') and not line.strip().startswith('\\includegraphics') and not line.strip().startswith('\\caption') and not line.strip().startswith('\\label'):
            if line.strip():
                text_blocks.append(line.strip())
                
    # Group descriptions based on keywords
    z_desc = []
    y_desc = []
    x_desc = []
    
    for d in text_blocks:
        if "Z 軸" in d or "樣本" in d:
            z_desc.append(d)
        elif "Y 軸" in d:
            y_desc.append(d)
        elif "X 軸" in d:
            x_desc.append(d)
        else:
            print(f"Unknown block: {d[:20]}...")
            z_desc.append(d)

    z_fig = """
\\begin{figure}[H]
    \\centering
    \\begin{minipage}{0.45\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_21_a.png}
        \\par (a) Z 軸基座
    \\end{minipage}
    \\begin{minipage}{0.45\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_21_b.png}
        \\par (b) Z 軸螺帽支架
    \\end{minipage}
    \\vspace{0.5cm}
    \\begin{minipage}{0.45\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_21_c.png}
        \\par (c) 樣本夾
    \\end{minipage}
    \\begin{minipage}{0.45\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_21_d.png}
        \\par (d) 樣本固定夾
    \\end{minipage}
    \\caption{Z 軸與樣本夾部件}
    \\label{fig:stage_z}
\\end{figure}
"""

    y_fig = """
\\begin{figure}[H]
    \\centering
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_22_a.png}
        \\par (a) Y 軸馬達座
    \\end{minipage}
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_22_b.png}
        \\par (b) Y 軸軸承座
    \\end{minipage}
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_22_c.png}
        \\par (c) Y 軸 T8 螺帽支架
    \\end{minipage}
    \\vspace{0.5cm}
    \\begin{minipage}{0.45\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_22_d.png}
        \\par (d) Y 軸導軌至軸承轉接件
    \\end{minipage}
    \\begin{minipage}{0.45\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_22_e.png}
        \\par (e) Y 軸至 X 軸轉接件
    \\end{minipage}
    \\caption{Y 軸部件}
    \\label{fig:stage_y}
\\end{figure}
"""

    x_fig = """
\\begin{figure}[H]
    \\centering
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_23_a.png}
        \\par (a) X 軸馬達座
    \\end{minipage}
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_23_b.png}
        \\par (b) X 軸軸承座
    \\end{minipage}
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_23_c.png}
        \\par (c) X 軸被動端支架
    \\end{minipage}
    \\vspace{0.5cm}
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_23_d.png}
        \\par (d) X 軸 T8 螺帽支架
    \\end{minipage}
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_23_e.png}
        \\par (e) X 軸導軌樂高轉接件
    \\end{minipage}
    \\begin{minipage}{0.3\\textwidth}
        \\centering
        \\includegraphics[width=\\textwidth]{figures/ch3/fig3_23_f.png}
        \\par (f) X 軸導軌至軸承轉接件
    \\end{minipage}
    \\caption{X 軸部件}
    \\label{fig:stage_x}
\\end{figure}
"""

    new_stage_content = "\n\n" + "\n\n".join(z_desc) + "\n" + z_fig + "\n\n" + "\n\n".join(y_desc) + "\n" + y_fig + "\n\n" + "\n\n".join(x_desc) + "\n" + x_fig + "\n\n"

    new_content = pre_stage + new_stage_content + post_stage

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Grouping completed!")

group_stage_figures('c:/Users/chen0/OneDrive/Documents/Thesis/Thesis_Proposal/contents/chapter03.tex')
