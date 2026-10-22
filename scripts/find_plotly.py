with open('app/app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f.readlines()):
        if 'st.plotly_chart' in line:
            print(str(i+1) + ': ' + repr(line.encode('ascii', 'ignore').decode()))
