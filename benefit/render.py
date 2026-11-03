# card.json → 슬라이드별 HTML → 헤드리스 Chrome 스크린샷(1080x1350 PNG)
# 사용: python3 render.py <card.json> <out_dir> [chrome 경로]
import html, json, pathlib, subprocess, sys

card = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2]); out.mkdir(exist_ok=True)
chrome = sys.argv[3] if len(sys.argv) > 3 else "google-chrome"
BRAND = "@oooo.zzii 꿀정보"

CSS = """
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1350px;font-family:Pretendard,sans-serif;background:#FFF8EF;color:#2B2118;
  display:flex;flex-direction:column;padding:96px 88px 72px;word-break:keep-all}
.brand{font-size:30px;font-weight:700;color:#E8833A;letter-spacing:-.5px}
main{flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px}
.kicker{font-size:44px;font-weight:600;color:#8A6F5A}
h1{font-size:120px;font-weight:800;line-height:1.15;letter-spacing:-3px;white-space:pre-line}
h2{font-size:76px;font-weight:800;letter-spacing:-2px;white-space:pre-line;line-height:1.25}
.sub{font-size:42px;font-weight:600;color:#E8833A}
ul{list-style:none;padding:0;display:flex;flex-direction:column;gap:28px}
li{font-size:46px;font-weight:600;line-height:1.4;background:#fff;border-radius:28px;padding:36px 44px;white-space:pre-line;
  box-shadow:0 4px 0 #F1E3D3}
.row{display:flex;justify-content:space-between;align-items:baseline;background:#fff;border-radius:28px;padding:44px 52px;box-shadow:0 4px 0 #F1E3D3}
.row b{font-size:48px;font-weight:600;color:#8A6F5A}.row strong{font-size:84px;font-weight:800;color:#E8833A}
.note{font-size:38px;color:#8A6F5A}
footer{display:flex;justify-content:space-between;font-size:26px;color:#A8917D}
"""

def body(s):
    e = lambda t: html.escape(t)
    t = s["type"]
    if t == "cover":
        return f'<div class="kicker">{e(s["kicker"])}</div><h1>{e(s["title"])}</h1><div class="sub">{e(s["sub"])}</div>'
    if t == "list":
        return f'<h2>{e(s["title"])}</h2><ul>' + "".join(f"<li>{e(i)}</li>" for i in s["items"]) + "</ul>"
    if t == "amount":
        rows = "".join(f'<div class="row"><b>{e(k)}</b><strong>{e(v)}</strong></div>' for k, v in s["rows"])
        return f'<h2>{e(s["title"])}</h2>{rows}<div class="note">{e(s["note"])}</div>'
    if t == "outro":
        return f'<h2>{e(s["title"])}</h2><div class="sub">{e(s["sub"])}</div>'
    raise ValueError(t)

n = len(card["slides"])
for i, s in enumerate(card["slides"], 1):
    page = out / f"{i}.html"
    page.write_text(f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
                    f'<div class="brand">{BRAND}</div><main>{body(s)}</main>'
                    f'<footer><span>{html.escape(card["source"])}</span><span>{i}/{n}</span></footer>')
    # ponytail: 웹폰트 로딩은 virtual-time-budget으로 기다린다. 폰트가 빠지면 폰트 파일을 레포에 넣는다
    subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=1080,1350",
                    "--virtual-time-budget=5000", f"--screenshot={out / f'{i}.png'}", page.resolve().as_uri()],
                   check=True, capture_output=True)
    print(out / f"{i}.png")
