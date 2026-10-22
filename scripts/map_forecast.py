with open('app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(250, 270):
    print(str(i+1) + ': ' + repr(lines[i].encode('ascii', 'ignore').decode().strip()))
