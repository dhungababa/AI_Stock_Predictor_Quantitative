with open('app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(220, 265):
    line = lines[i]
    if 'bg_color = "#dcfce7"' in line: lines[i] = line.replace('#dcfce7', 'rgba(0, 208, 132, 0.1)')
    if 'pred_color = "#16a34a"' in line: lines[i] = line.replace('#16a34a', '#00d084')
    if 'bg_color = "#fef08a"' in line: lines[i] = line.replace('#fef08a', 'rgba(202, 138, 4, 0.1)')
    if 'bg_color = "#fee2e2"' in line: lines[i] = line.replace('#fee2e2', 'rgba(220, 38, 38, 0.1)')
    if 'background-color: rgba(255,255,255,0.6)' in line: lines[i] = line.replace('rgba(255,255,255,0.6)', 'rgba(0,0,0,0.4)')
    if 'color: #f8fafc;' in line and 'The XGBoost Neural Engine predicts' in line: lines[i] = line.replace('color: #f8fafc;', 'color: #94a3b8;')

with open('app/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
