# card.json → 슬라이드별 HTML → 헤드리스 Chrome 스크린샷(1080x1350 PNG)
# 사용: python3 render.py <card.json> <out_dir> [chrome 경로]
#  - 문구 안의 *강조*는 형광펜으로 그린다
#  - calc 슬라이드 금액은 LLM이 쓰지 않고 phases×wages로 여기서 계산한다
#  - 넘침·표지 숫자 불일치는 <out_dir>/warnings.txt에 남긴다 (이슈 본문에 ⚠️로 붙는다)
import html, json, pathlib, re, subprocess, sys

card = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2]); out.mkdir(exist_ok=True)
chrome = sys.argv[3] if len(sys.argv) > 3 else "google-chrome"
BRAND = "@oooo.zzii 꿀정보"

CSS = """
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
*{margin:0;padding:0;box-sizing:border-box}
:root{--ink:#1C1A17;--sub:#5E564D;--yellow:#FFE24A;--pink:#FF6FA3;--pinkbg:#FFE1EC;--paper:#FFFDF6}
body{width:1080px;height:1350px;font-family:Pretendard,sans-serif;background:var(--paper);color:var(--ink);
  display:flex;flex-direction:column;padding:72px 80px 56px;word-break:keep-all;white-space:pre-line}
body.cover,body.outro{background:var(--yellow)}
header{display:flex;justify-content:space-between;align-items:center}
.brand{font-size:28px;font-weight:800;background:var(--ink);color:#fff;border-radius:999px;padding:12px 26px;white-space:nowrap}
.save{font-size:28px;font-weight:800;background:#fff;border:3px solid var(--ink);border-radius:999px;padding:9px 22px;white-space:nowrap}
main{flex:1;display:flex;flex-direction:column;justify-content:center;gap:34px;min-height:0}
em{font-style:normal;background:linear-gradient(transparent 55%,var(--pink) 55%,var(--pink) 92%,transparent 92%)}
body.cover em,body.outro em{background:linear-gradient(transparent 55%,#fff 55%,#fff 92%,transparent 92%)}
.kicker{font-size:84px;font-weight:900;letter-spacing:-2px;line-height:1.15}
h1{font-size:200px;font-weight:900;line-height:1;letter-spacing:-8px;white-space:nowrap}
.cond{align-self:flex-start;font-size:36px;font-weight:800;background:var(--ink);color:var(--yellow);border-radius:14px;padding:12px 22px}
h2{font-size:80px;font-weight:900;letter-spacing:-2.5px;line-height:1.18}
.say{align-self:flex-start;position:relative;font-size:38px;font-weight:700;background:#fff;border:4px solid var(--ink);border-radius:36px;padding:20px 30px}
.say::after{content:"";position:absolute;left:48px;bottom:-22px;width:30px;height:30px;background:#fff;border-right:4px solid var(--ink);border-bottom:4px solid var(--ink);transform:rotate(45deg)}
.box{background:#fff;border:4px solid var(--ink);border-radius:32px;box-shadow:8px 8px 0 var(--ink);overflow:hidden}
table{width:100%;border-collapse:collapse}
th{font-size:30px;font-weight:700;color:var(--sub);padding:22px 26px;text-align:right;border-bottom:3px solid var(--ink)}
th:first-child,td:first-child{text-align:left}
td{font-size:42px;font-weight:800;padding:24px 26px;text-align:right;border-bottom:3px dashed #D9D2C7}
tr.sum td{background:var(--ink);color:#fff;border:0}
tr.sum td.hi{color:var(--yellow);font-size:56px;font-weight:900}
.row{display:flex;flex-direction:column;gap:6px;padding:32px 40px}
.row b{font-size:38px;font-weight:700;color:var(--sub)}.row strong{font-size:72px;font-weight:900;line-height:1.15}
.note{font-size:36px;color:var(--sub);font-weight:700}
.tip{display:flex;gap:26px;align-items:flex-start;padding:30px 34px}
.tip i{font-style:normal;font-size:60px;line-height:1.1}
.tip b{display:block;font-size:46px;font-weight:900;line-height:1.25;margin-bottom:8px}
.tip span{font-size:36px;font-weight:600;line-height:1.4;color:var(--sub)}
.list{display:flex;flex-direction:column;gap:24px}
ol{list-style:none;display:flex;flex-direction:column;gap:24px;counter-reset:s}
ol li{counter-increment:s;display:flex;gap:26px;align-items:center;font-size:46px;font-weight:800;line-height:1.35;padding:32px 36px}
ol li::before{content:counter(s);flex:none;width:68px;height:68px;border-radius:50%;background:var(--yellow);border:4px solid var(--ink);display:grid;place-items:center;font-size:38px;font-weight:900}
.checks li::before{content:"✓";background:var(--pink);color:#fff}
.next{align-self:flex-end;font-size:34px;font-weight:800;background:var(--pinkbg);border-radius:999px;padding:14px 28px}
footer{display:flex;justify-content:space-between;font-size:22px;color:var(--sub);white-space:nowrap;margin-top:24px}
"""

# 표지 숫자가 가로로 넘치면 줄이고, main이 세로로 넘치면 전체를 5%씩 줄인다. 70%까지 줄여도 넘치면 title에 남긴다
FIT_JS = """<script>
const h=document.querySelector('h1');
if(h){let f=200;while(h.scrollWidth>h.clientWidth+1&&f>110){f-=10;h.style.fontSize=f+'px'}}
const m=document.querySelector('main');let k=1;
while(m.scrollHeight>m.clientHeight+1&&k>0.7){k-=0.05;document.body.style.zoom=k}
if(m.scrollHeight>m.clientHeight+1||(h&&h.scrollWidth>h.clientWidth+1))document.title='OVERFLOW';
</script>"""

e = lambda t: re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(t))
say = lambda s: f'<div class="say">{e(s["say"])}</div>' if s.get("say") else ""
won = lambda v: f"{v:,.0f}"


def calc_totals(s):
    """월급별 (월급, 기간별 월 지급액, 합계). phases = [기간, 지급률, 월 상한, 개월 수]"""
    res = []
    for w in s["wages"]:
        monthly = [min(w * rate, cap) for _, rate, cap, _ in s["phases"]]
        res.append((w, monthly, sum(m * p[3] for m, p in zip(monthly, s["phases"]))))
    return res


def calc_table(s):
    months = sum(p[3] for p in s["phases"])
    label = "1년" if months == 12 else f"{months}개월"
    head = f'<tr><th>월급({e(s["unit"])})</th>' + "".join(f"<th>{e(p[0])}</th>" for p in s["phases"]) + f"<th>{label}</th></tr>"
    top = max(s["wages"])
    rows = "".join(
        f'<tr{" class=sum" if w == top else ""}><td>{won(w)}</td>' + "".join(f"<td>{won(m)}</td>" for m in monthly)
        + f'<td class="hi">{won(t)}</td></tr>'
        for w, monthly, t in calc_totals(s))
    return f'<div class="box"><table>{head}{rows}</table></div>'


def body(s):
    t = s["type"]
    if t == "cover":
        return (f'<div class="kicker">{e(s["kicker"])}</div><h1>{e(s["title"])}</h1>'
                f'<div class="cond">{e(s["cond"])}</div>{say(s)}')
    if t == "calc":  # 매달 받는 혜택: 금액은 코드가 계산
        return f'<h2>{e(s["title"])}</h2>{say(s)}{calc_table(s)}<div class="note">{e(s["note"])}</div>'
    if t == "amount":  # 일시금·바우처·감면: 조건별 금액
        rows = "".join(f'<div class="box row"><b>{e(k)}</b><strong>{e(v)}</strong></div>' for k, v in s["rows"])
        return f'<h2>{e(s["title"])}</h2>{say(s)}<div class="list">{rows}</div><div class="note">{e(s.get("note", ""))}</div>'
    if t == "tips":
        tips = "".join(f'<div class="box tip"><i>{ic}</i><div><b>{e(h)}</b><span>{e(d)}</span></div></div>' for ic, h, d in s["items"])
        return f'<h2>{e(s["title"])}</h2><div class="list">{tips}</div>{say(s)}'
    if t == "steps":
        return f'<h2>{e(s["title"])}</h2><ol>' + "".join(f'<li class="box">{e(i)}</li>' for i in s["items"]) + f'</ol><div class="note">{e(s.get("note", ""))}</div>'
    if t == "outro":
        checks = "".join(f'<li class="box">{e(c)}</li>' for c in s["checks"])
        return f'<h2 style="font-size:104px">{e(s["title"])}</h2><ol class="checks">{checks}</ol><div class="kicker" style="font-size:44px">{e(s["sub"])}</div>'
    raise ValueError(t)


warnings = []
slides = card["slides"]

# 표지 숫자 검증: calc가 있으면 최고 월급의 합계가 표지 title에 그대로 있어야 한다
for s in slides:
    if s["type"] == "calc":
        top = won(max(t for *_, t in calc_totals(s)))
        if top not in slides[0]["title"]:
            warnings.append(f"표지 숫자({slides[0]['title']})가 계산 합계({top}만)와 달라요")

n = len(slides)
args = [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--window-size=1080,1350", "--virtual-time-budget=5000"]
for i, s in enumerate(slides, 1):
    nxt = ""
    if i < n:
        teaser = re.sub(r"[*\n]", " ", slides[i]["title"]).strip()
        nxt = f'<div class="next">다음 › {html.escape(teaser)}</div>'
    page = out / f"{i}.html"
    page.write_text(f'<!doctype html><meta charset="utf-8"><title>ok</title><style>{CSS}</style><body class="{s["type"]}">'
                    f'<header><div class="brand">{BRAND}</div><div class="save">📌 저장각</div></header>'
                    f'<main>{body(s)}</main>{nxt}'
                    f'<footer><span>{html.escape(card["source"])}</span><span>{i}/{n}</span></footer>{FIT_JS}')
    uri = page.resolve().as_uri()
    # --no-sandbox: 우리가 만든 로컬 HTML만 열고, ubuntu 러너의 AppArmor가 샌드박스를 막는 경우가 있다
    subprocess.run([*args, f"--screenshot={out / f'{i}.png'}", uri], check=True, capture_output=True)
    # HTML 원본에도 'OVERFLOW' 문자열이 있으니 스크립트 실행 뒤의 DOM에서 title을 본다
    dom = subprocess.run([*args, "--dump-dom", uri], check=True, capture_output=True, text=True).stdout
    if "<title>OVERFLOW</title>" in dom:
        warnings.append(f"{i}장 글이 넘쳐요 (글자를 줄여도 안 들어감)")
    print(out / f"{i}.png")

(out / "warnings.txt").write_text("".join(f"{w}\n" for w in warnings))
