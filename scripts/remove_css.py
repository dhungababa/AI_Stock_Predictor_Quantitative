import re

with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the broken selectbox CSS lines
broken_css_pattern = r'/\* Inputs \*/.*?div\[role="radiogroup"\] p \{ color: #f8fafc !important; font-size: 16px; \}'
content = re.sub(broken_css_pattern, '/* Inputs styled natively via config.toml */', content, flags=re.DOTALL)

with open('app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("SUCCESS")
