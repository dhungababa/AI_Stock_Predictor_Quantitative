with open('app/app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f.readlines()):
        if 'make_subplots' in line or 'Candlestick' in line or 'fig.update' in line:
            print(str(i+1) + ': ' + repr(line.encode('ascii', 'ignore').decode()))
