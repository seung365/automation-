# 네이버 지도 링크의 가게 정보(메뉴·가격·영업시간·리뷰 키워드)를 m.place.naver.com에서 읽어 place.json으로 남긴다
# usage: python3 -I scripts/naver_place.py <request.md>   (링크가 없거나 못 읽으면 place.json 없이 끝난다)
import json, re, sys, urllib.request

UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.geturl(), res.read().decode('utf-8', 'replace')


def place_id(text):
    for link in re.findall(r'https?://(?:naver\.me|map\.naver\.com|m\.place\.naver\.com|place\.naver\.com)/[^\s)<>"]+', text):
        final, _ = get(link)  # naver.me 단축 링크는 pinId가 붙은 지도 주소로 넘어간다
        m = re.search(r'(?:pinId=|place/|restaurant/|cafe/)(\d{5,})', final + ' ' + link)
        if m:
            return m.group(1)


def apollo(url):
    _, html = get(url)
    m = re.search(r'window\.__APOLLO_STATE__\s*=\s*(\{.*?\});\s*window\.', html, re.S)
    return json.loads(m.group(1)) if m else {}


def find_hours(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == 'businessHours' and isinstance(v, list) and v and isinstance(v[0], dict) and 'day' in v[0]:
                return [f"{h['day']} {(h.get('businessHours') or {}).get('start', '?')}~{(h.get('businessHours') or {}).get('end', '?')}"
                        + ''.join(f" (브레이크 {b['start']}~{b['end']})" for b in h.get('breakHours') or []) for h in v]
            found = find_hours(v)
            if found:
                return found
    elif isinstance(node, list):
        for v in node:
            found = find_hours(v)
            if found:
                return found


def main():
    pid = place_id(open(sys.argv[1], encoding='utf-8').read())
    if not pid:
        print('네이버 지도 링크 없음'); return
    # ponytail: 음식점·카페는 /restaurant 경로로 열린다. 다른 업종이 필요해지면 /place도 시도
    home = apollo(f'https://m.place.naver.com/restaurant/{pid}/home')
    menu = apollo(f'https://m.place.naver.com/restaurant/{pid}/menu/list')
    base = home.get(f'PlaceDetailBase:{pid}') or menu.get(f'PlaceDetailBase:{pid}') or {}
    info = {
        'source': f'https://m.place.naver.com/restaurant/{pid}/home',
        'name': base.get('name'),
        'category': base.get('category'),
        'address': base.get('roadAddress'),
        'businessHours': find_hours(home) or find_hours(menu),
        'menus': [{'name': v.get('name'), 'price': (v.get('price') or {}).get('displayText')}
                  for k, v in menu.items() if k.startswith('PlaceMenuItem:')],
        'reviewKeywords': base.get('microReviews'),
        'visitorReviews': {'score': base.get('visitorReviewsScore'), 'total': base.get('visitorReviewsTotal')},
    }
    json.dump(info, open('place.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(info, ensure_ascii=False)[:500])


try:
    main()
except Exception as e:  # 가게 정보는 보충용이라 실패해도 글은 쓴다
    print('네이버 플레이스 정보를 못 읽음:', e)
