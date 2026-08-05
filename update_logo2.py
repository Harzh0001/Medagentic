import re

with open("ui/chat.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove base64 block
content = re.sub(r'import base64.*?LOGO_IMG_TAG = .*?\n', '', content, flags=re.DOTALL)

# 2. Replace nav-left
nav_left_old = """<div class="nav-left">
{LOGO_IMG_TAG}
<div class="nav-titles" style="margin-left: 10px; justify-content: center;">
<div class="nav-subtitle" style="margin-top: 4px;">Medical question assistant</div>
</div>
</div>"""

nav_left_new = """<div class="nav-left">
<div class="nav-icon" style="background-color: transparent; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 32px;">
⚕️
</div>
<div class="nav-titles">
<div class="nav-brand">Mediate</div>
<div class="nav-subtitle">Medical question assistant</div>
</div>
</div>"""

content = content.replace(nav_left_old, nav_left_new)

# 3. Replace hero_icon
hero_icon_old = """<div class="hero-icon">
<img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 60px; object-fit: contain;">
</div>"""

hero_icon_new = """<div class="hero-icon" style="font-size: 56px;">
⚕️
</div>"""

content = content.replace(hero_icon_old, hero_icon_new)

# 4. Replace logged-in top banner
logged_in_old = """<div style="margin-bottom: 16px; display: flex; justify-content:center; align-items:center;">
        <img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 60px; object-fit: contain;">
    </div>
    <div style="font-size: 20px; font-weight: 500; color: var(--text-main);">Wellness & Health Education</div>"""

logged_in_new = """<div style="margin-bottom: 16px; display: flex; justify-content:center; align-items:center; font-size: 56px;">
        ⚕️
    </div>
    <div style="font-size: 20px; font-weight: 500; color: var(--text-main);">Mediate Wellness & Health Education</div>"""

content = content.replace(logged_in_old, logged_in_new)

with open("ui/chat.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated chat.py successfully!")
