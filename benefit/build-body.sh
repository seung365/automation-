#!/usr/bin/env bash
# card.json · insta.txt → 카드 렌더 → simple-init 업로드 → body.md
#   body.md = 카드 이미지 + ⚠️ 경고 + [원문] + 카드 문구(card.json, 접힘) + "## 인스타 캡션"
#   card.json을 접어 넣어 두는 건 /claude가 다음 수정 때 꺼내 쓰기 위해서다 (캡션 섹션보다 앞에 둬야 한다)
# 사용: MEDIA_TOKEN=... bash benefit/build-body.sh <서비스ID> [원문 URL]   (benefit-daily · claude-on-comment)
set -euo pipefail
id="$1"; src="${2:-}"

# 이모지·ᐢ 같은 글자가 □로 깨지지 않게 (ubuntu 러너 기본 폰트에 없다)
sudo apt-get install -y -qq fonts-noto-color-emoji fonts-noto-core > /dev/null
python3 benefit/render.py card.json out # ubuntu 러너에 google-chrome 기본 설치
python3 -m venv /tmp/py && /tmp/py/bin/pip install -q pillow==12.0.0

: > body.md
for png in $(ls out/*.png | sort -V); do
  n="$(basename "$png" .png)"
  /tmp/py/bin/python -c "from PIL import Image; Image.open('$png').convert('RGB').save('c.jpg', quality=92)"
  # 내 계정과 연결 안 된 작성자로 커밋 → 잔디·프로필 활동에 안 잡힌다. 경로에 실행 번호를 넣어 덮어쓰기(sha 필요)를 피한다
  jq -n --arg m "benefit $id" --rawfile c <(base64 -w0 c.jpg) \
    '{message: $m, content: $c, committer: {name: "insta-bot", email: "insta-bot@oooozzii.invalid"}}' > put.json
  GH_TOKEN="$MEDIA_TOKEN" gh api -X PUT "repos/seung365/simple-init/contents/benefit/$id/$GITHUB_RUN_ID-$n.jpg" --input put.json > /dev/null
  echo "![$n](https://raw.githubusercontent.com/seung365/simple-init/main/benefit/$id/$GITHUB_RUN_ID-$n.jpg)" >> body.md
done

# 검수할 때 볼 경고: 렌더 경고(넘침·표지 숫자) + 확인 필요 + 해시태그 수
if grep -q '확인 필요' card.json; then echo '카드에 "확인 필요"가 있어요. 원문 확인 후 올려 주세요.' >> out/warnings.txt; fi
tags=$(grep -o '#[가-힣A-Za-z0-9_]\+' insta.txt | wc -l || true)
if [ "$tags" -gt 5 ]; then echo "해시태그가 ${tags}개예요. 인스타는 5개까지만 돼요." >> out/warnings.txt; fi
if [ -s out/warnings.txt ]; then { echo; sed 's/^/> ⚠️ /' out/warnings.txt; } >> body.md; fi

if [ -n "$src" ]; then printf '\n원문: %s\n' "$src" >> body.md; fi
printf '\n<details><summary>카드 문구 (card.json)</summary>\n\n```json card\n%s\n```\n</details>\n' "$(cat card.json)" >> body.md
# ~ 두 개는 GitHub에서 취소선이 된다 → 전각 물결로
printf '\n## 인스타 캡션\n%s\n' "$(sed 's/~/～/g' insta.txt)" >> body.md
