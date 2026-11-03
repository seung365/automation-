# 오늘 올릴 혜택 1건: 육아 분야 · 전국 대상 · 조회수 순, 이미 올린 건 제외
# 사용: python3 benefit/pick.py <used_ids.txt>  → detail.json, stdout에 "서비스명 서비스ID"
import json, os, sys, urllib.parse, urllib.request

API = "https://api.odcloud.kr/api/gov24/v3"
FIELDS = {"임신·출산", "보육·교육"}
ORGS = {"중앙행정기관", "공공기관"}  # ponytail: 전국편 소진되면 지역(시군구) 편으로 넓힌다


def get(ep, **params):
    q = urllib.parse.urlencode({"serviceKey": os.environ["DATA_GO_KR_KEY"], **params})
    return json.load(urllib.request.urlopen(f"{API}/{ep}?{q}", timeout=30))


used = set(open(sys.argv[1]).read().split())
rows, page = [], 1
while True:
    d = get("serviceList", page=page, perPage=1000)
    rows += d["data"]
    if page * 1000 >= d["totalCount"]:
        break
    page += 1

pool = [r for r in rows if r["서비스분야"] in FIELDS and r["소관기관유형"] in ORGS and r["서비스ID"] not in used]
if not pool:
    sys.exit("올릴 혜택이 없어요")
top = max(pool, key=lambda r: r.get("조회수") or 0)
detail = get("serviceDetail", **{"cond[서비스ID::EQ]": top["서비스ID"]})["data"][0]
json.dump({**detail, "상세조회URL": top["상세조회URL"]}, open("detail.json", "w"), ensure_ascii=False, indent=1)
print(f'{top["서비스명"]} {top["서비스ID"]}')
