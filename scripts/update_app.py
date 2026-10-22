import re
with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("st.error('I AM HERE DEBUG')", "")

target_news = '<div style="padding: 15px; border-left: 5px solid {color}; background-color: #ffffff; border: 1px solid #e2e8f0; margin-bottom: 10px; border-radius: 5px;">'
replacement_news = '<div style="padding: 20px; border-left: 5px solid {color}; background-color: #252836; border: 1px solid #3b3f51; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.2);">'
content = content.replace(target_news, replacement_news)

with open('app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('SUCCESS')
