import re
with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_css = '''<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp { 
        background-color: #1a1c23; 
        color: #e2e8f0; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Professional Headers */
    h1, h2, h3, h4, h5, p, span, li, div { 
        font-family: 'Inter', sans-serif !important; 
        text-shadow: none;
    }
    h1, h2, h3, h4, h5 {
        color: #f8fafc !important; 
        font-weight: 700 !important; 
    }
    
    /* Clean Metric Containers */
    .metric-container { 
        background: #252836; 
        backdrop-filter: none;
        border: none;
        border-top: 4px solid #00d084;
        border-radius: 8px; 
        padding: 20px; 
        text-align: center; 
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.2);
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3);
    }
    .metric-value { font-size: 28px; color: #00d084; font-weight: 700; font-family: 'Inter', sans-serif; text-shadow: none; }
    
    /* Corporate Buttons */
    .stButton>button { 
        background: #00d084; 
        color: #1a1c23; 
        border: none; 
        border-radius: 6px; 
        padding: 10px 24px; 
        font-weight: 600; 
        transition: all 0.2s ease; 
    }
    .stButton>button:hover { 
        background: #00e676; 
        color: #1a1c23;
        transform: translateY(-1px); 
    }
    
    /* Input Fields & Radios */
    div[data-baseweb='select'] > div, div[data-baseweb='base-input'] {
        background: #252836;
        border: 1px solid #3b3f51;
        color: #f8fafc;
        border-radius: 6px;
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        border: 1px solid #3b3f51;
        background: #252836;
    }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>'''

content = re.sub(r'<style>.*?</style>', new_css, content, flags=re.DOTALL)
content = content.replace('color: #1e293b;', 'color: #f8fafc;')
content = content.replace('color: #0f172a;', 'color: #f8fafc;')
content = content.replace('color: #64748b;', 'color: #94a3b8;')
content = content.replace('color: #334155;', 'color: #cbd5e1;')
content = content.replace('color:#2563eb;', 'color:#00d084;')
content = content.replace('border-left: 4px solid #3b82f6; background-color: #f8fafc;', 'border-left: 4px solid #00d084; background-color: #252836;')
content = content.replace('plot_bgcolor=\"rgba(0,0,0,0)\"', 'plot_bgcolor=\"#1a1c23\"')
content = content.replace('paper_bgcolor=\"rgba(0,0,0,0)\"', 'paper_bgcolor=\"#1a1c23\"')
content = content.replace('font=dict(color=\"#1e293b\"', 'font=dict(color=\"#e2e8f0\"')
content = content.replace('gridcolor=\'#e2e8f0\'', 'gridcolor=\'#3b3f51\'')
content = content.replace('zerolinecolor=\'#e2e8f0\'', 'zerolinecolor=\'#3b3f51\'')
content = content.replace('rgba(255,255,255,1)', 'rgba(26,28,35,1)')
content = content.replace('color=\'#333333\'', 'color=\'#e2e8f0\'')

with open('app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
