import re
with open('data.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('period="2y"', 'period="5y"')
content = content.replace('Downloading 2 years of price data', 'Downloading 5 years of price data')

with open('data.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("SUCCESS")
