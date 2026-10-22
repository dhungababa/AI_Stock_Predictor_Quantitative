with open('app/app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f.readlines()):
        if 'st.markdown' in line or 'Deep Quantum Analysis Engine' in line or 'Speedometer' in line:
            print(f'{i+1}: ' + repr(line.encode('ascii', 'ignore').decode().strip()))
