with open('app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
in_css = False
for i, line in enumerate(lines):
    if '<style>' in line:
        in_css = True
    if in_css:
        print(str(i+1) + ': ' + repr(line.encode('ascii', 'ignore').decode().rstrip()))
    if '</style>' in line:
        break
