import html
import re
import sys
import urllib.request

USER = sys.argv[1]
README = "README.md"
START = "<!-- ACHIEVEMENTS:START -->"
END = "<!-- ACHIEVEMENTS:END -->"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile-readme-updater)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse(page):
    found = {}
    parts = re.split(r'(?=<img[^>]*alt="Achievement: )', page)
    for part in parts[1:]:
        m = re.match(r'<img[^>]*alt="Achievement: ([^"]+)"[^>]*>', part)
        if not m:
            continue
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            continue
        name = html.unescape(m.group(1)).strip()
        tier = re.search(r'achievement-tier-label[^>]*>\s*x(\d+)\s*<', part[:2500])
        count = int(tier.group(1)) if tier else 1
        if name not in found or count > found[name][1]:
            found[name] = (html.unescape(src.group(1)), count)
    return found


achievements = {}
for url in (f"https://github.com/{USER}?tab=achievements", f"https://github.com/{USER}"):
    try:
        for k, v in parse(fetch(url)).items():
            if k not in achievements or v[1] > achievements[k][1]:
                achievements[k] = v
    except Exception as e:
        print("Could not read", url, e)

if not achievements:
    print("No achievements found; README left unchanged.")
    sys.exit(0)

cells = []
for name, (src, count) in sorted(achievements.items()):
    label = f"{name} x{count}" if count > 1 else name
    cells.append(
        f'  <a href="https://github.com/{USER}?tab=achievements" title="{label}">'
        f'<img src="{src}" height="96" alt="{label}" /></a>'
    )
caption = " &nbsp;·&nbsp; ".join(
    f"{n} x{c}" if c > 1 else n for n, (s, c) in sorted(achievements.items())
)
block = (
    f'{START}\n<p align="center">\n' + "\n".join(cells) + "\n</p>\n"
    f'<p align="center"><sub>{caption}</sub></p>\n{END}'
)

text = open(README, encoding="utf-8").read()
new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
if new != text:
    open(README, "w", encoding="utf-8").write(new)
    print("Updated achievements:", caption)
else:
    print("Achievements unchanged.")
