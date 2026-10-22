import re
with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Speedometer Chart to look highly professional
target_speedometer = '''            fig_gauge.update_layout(height=250, margin=dict(t=50, b=20, l=20, r=20), paper_bgcolor="#1a1c23", font=dict(family="Inter"))'''
replacement_speedometer = '''            fig_gauge.update_traces(gauge=dict(bar=dict(color="#00d084"), bgcolor="#252836", borderwidth=0, threshold=dict(line=dict(color="#ef4444", width=4), thickness=0.75, value=50)))
            fig_gauge.update_layout(height=250, margin=dict(t=50, b=20, l=20, r=20), paper_bgcolor="#1a1c23", font=dict(family="Inter", color="#f8fafc"))'''
content = content.replace(target_speedometer, replacement_speedometer)

# 2. Update Candlestick Chart to look like the neon UI
content = content.replace("increasing_line_color='#16a34a'", "increasing_line_color='#00d084', increasing_fillcolor='#00d084'")
content = content.replace("decreasing_line_color='#dc2626'", "decreasing_line_color='#ef4444', decreasing_fillcolor='#ef4444'")
content = content.replace("line=dict(color=\"#2563eb\", width=3, shape=\"spline\"), fill='tozeroy', opacity=0.1", "line=dict(color=\"#3b82f6\", width=4, shape=\"spline\"), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)', opacity=0.8")

# 3. Donut Chart Colors
content = content.replace("color_discrete_sequence=px.colors.sequential.Blues_r", "color_discrete_sequence=['#00d084', '#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981']")
content = content.replace("color='#ffffff'", "color='#1a1c23'") # Donut borders

with open('app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('SUCCESS')
