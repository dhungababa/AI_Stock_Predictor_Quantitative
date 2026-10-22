import re

with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '/* Inputs styled natively via config.toml */'

replacement = '''    /* Inputs (Dropdowns and Selects) */
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        color: #f8fafc !important;
    }
    /* The actual popup menu */
    div[data-baseweb="popover"] > div {
        background-color: #0f172a !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
    }
    ul[role="listbox"] {
        background-color: #0f172a !important;
    }
    ul[role="listbox"] li {
        background-color: #0f172a !important; 
        color: #f8fafc !important; 
    }
    ul[role="listbox"] li:hover { 
        background-color: rgba(139, 92, 246, 0.3) !important; 
    }
    
    div[role="radiogroup"] label { color: #f8fafc !important; }
    div[role="radiogroup"] p { color: #f8fafc !important; font-size: 16px; }'''

if target in content:
    content = content.replace(target, replacement)
    with open('app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
