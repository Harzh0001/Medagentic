import re

with open("ui/chat.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add base64 import and get_logo_base64 logic
b64_logic = """import base64
def get_logo_base64():
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_base64()
LOGO_IMG_TAG = f'<img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 40px; object-fit: contain;">'
"""

# Replace CROSS_SVG definition with LOGO_IMG_TAG
content = re.sub(r'# MEDICAL CROSS SVG\nCROSS_SVG = .*?</svg>"""', b64_logic, content, flags=re.DOTALL)

# In render_top_nav, replace the nav-left content
nav_left_old = """<div class="nav-left">
<div class="nav-icon">
{CROSS_SVG}
</div>
<div class="nav-titles">
<div class="nav-brand">Mediate</div>
<div class="nav-subtitle">Medical question assistant</div>
</div>
</div>"""

nav_left_new = """<div class="nav-left">
{LOGO_IMG_TAG}
<div class="nav-titles" style="margin-left: 10px; justify-content: center;">
<div class="nav-subtitle" style="margin-top: 4px;">Medical question assistant</div>
</div>
</div>"""

content = content.replace(nav_left_old, nav_left_new)

# In html_hero, replace the CROSS_SVG block
hero_icon_old = """<div class="hero-icon">
{CROSS_SVG}
</div>
<div class="hero-title">Ask a wellness or health education question</div>"""

hero_icon_new = """<div class="hero-icon">
<img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 60px; object-fit: contain;">
</div>
<div class="hero-title">Ask a wellness or health education question</div>"""

content = content.replace(hero_icon_old, hero_icon_new)

# In logged-in view, replace the CROSS_SVG block
logged_in_old = """<div style="color: var(--teal-dark); margin-bottom: 16px; width:48px; height:48px; display: flex; justify-content:center; align-items:center;">
        {CROSS_SVG}
    </div>
    <div style="font-size: 20px; font-weight: 500; color: var(--text-main);">Mediate Wellness & Health Education</div>"""

logged_in_new = """<div style="margin-bottom: 16px; display: flex; justify-content:center; align-items:center;">
        <img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 60px; object-fit: contain;">
    </div>
    <div style="font-size: 20px; font-weight: 500; color: var(--text-main);">Wellness & Health Education</div>"""

content = content.replace(logged_in_old, logged_in_new)

with open("ui/chat.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated chat.py successfully!")
