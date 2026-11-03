# automation-

네이버 블로그(oooozzii)·인스타(@oooo.zzii) 글을 GitHub Actions와 Claude로 자동으로 준비하는 개인 레포.
모든 결과물은 **이슈**로 올라오고(봇이 올려서 메일 알림이 온다), 확인한 뒤 **이슈 댓글 명령**으로 다듬고 게시한다.

## 하루 흐름

| 시각 (KST) | 무엇이 | 결과 |
|---|---|---|
| 06:30 | 내 맥 launchd → `sharelink/daily.mjs` | 토스 쉐어링크 특가·꿀템 후보 링크 발급 → 후보 이슈 |
| 07:00 | `benefit-daily` | 육아 혜택 카드뉴스 5장 + 인스타 캡션 이슈 (라벨 `benefit`). **경고가 없으면 바로 @oooo.zzii에 게시** |
| 09:00 | `daily-blog-draft` | 요일별 블로그 초안 + 썸네일 + 인스타 캡션 이슈 |

## 이슈 댓글 명령 (내 댓글만 동작)

| 명령 | 하는 일 |
|---|---|
| `/claude <요청>` | 이슈의 글을 요청대로 고쳐 댓글로 단다. 혜택 카드는 카드를 다시 그려 단다. 예: `/claude 표지 문구 더 짧게` |
| `/image [요청·이미지·URL]` | 블로그 썸네일을 새로 뽑는다 (`무드컷`, 첨부 이미지, 상품 URL 기준 등) |
| `/insta [이미지·URL]` | 가장 최근 `## 인스타 캡션`과 이미지로 @oooo.zzii에 게시. 혜택 카드는 가장 최근 카드 묶음을 캐러셀로. 올린 이슈엔 `insta` 라벨 |

캡션에 `[ ]` 빈칸이나 `확인 필요`가 남아 있으면 `/insta`가 막힌다.

## 워크플로

| 파일 | 트리거 | 내용 |
|---|---|---|
| `daily-blog-draft.yml` | 매일 09:00 | 요일별 카테고리(뷰티·맛집·카페·꿀정보) 초안. 후기 사진을 찾아 Higgsfield로 썸네일 재구성 |
| `blog-request.yml` | '내 사진으로 블로그 글 요청' 이슈 | 첨부 사진·네이버 플레이스 정보로 초안을 댓글로 |
| `sharelink-draft.yml` | '오늘의 특가 & 꿀템' 이슈 | 쉐어링크 정보 글·모음 글 초안을 댓글로 |
| `benefit-daily.yml` | 매일 07:00 | 육아 혜택 카드뉴스 (아래) |
| `claude-on-comment.yml` | `/claude` 댓글 | 글·카드 수정 |
| `image-on-comment.yml` | `/image` 댓글 | 썸네일 재생성 |
| `insta-on-comment.yml` | `/insta` 댓글 | 인스타 게시 (Graph API) |
| `notify.yml` | 수동(로컬 스크립트) | 로컬 스크립트 오류를 봇 이슈로 알림 |

## 육아 혜택 카드뉴스 (`benefit/`)

1. `pick.py` — 행정안전부 공공서비스(혜택) API에서 임신·출산·보육·교육 분야, 전국 대상 혜택 중 조회수 1위(이미 올린 건 제외)를 고른다. 이미 올린 건 `benefit` 이슈 제목 끝의 서비스ID로 거른다.
2. Claude가 원문(`detail.json`)의 사실만으로 `card.json`(카드 문구)과 `insta.txt`(캡션)를 쓴다. 형식은 `card.example.json`.
3. `render.py` — HTML 템플릿 → 헤드리스 Chrome으로 1080×1350 PNG. 매달 받는 혜택의 금액표(`calc`)는 코드가 계산하고, 표지 숫자 불일치·글 넘침은 경고로 남긴다.
4. `build-body.sh` — JPEG로 바꿔 `seung365/simple-init`(공개)에 올리고 이슈 본문을 만든다. 본문에는 카드, ⚠️ 경고, 원문 링크, 접힌 `card.json`(다음 `/claude` 수정용), `## 인스타 캡션`이 들어간다.

5. 경고(글 넘침·표지 숫자 불일치·`확인 필요`·해시태그 5개 초과)가 없으면 `insta-on-comment`를 수동 실행으로 불러 바로 캐러셀로 게시한다. 경고가 있으면 이슈에 안내 댓글만 남기고 멈추니, 확인하거나 `/claude`로 고친 뒤 `/insta`.

같은 혜택을 다시 만들려면 이전 이슈를 닫고 `benefit` 라벨을 뗀 뒤 `Benefit Daily Card`를 수동 실행한다.

## 왜 simple-init 레포가 따로 있나

인스타 Graph API는 이미지를 직접 받지 않고 **공개 URL**만 받는다. 이 레포는 비공개라 Meta가 못 가져가므로, 공개 레포 `simple-init`을 이미지 호스팅으로 쓴다 (`raw.githubusercontent.com`). `INSTA_MEDIA_TOKEN`은 그 레포 쓰기 권한만 있다.

## 시크릿

| 이름 | 용도 |
|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | claude-code-action (개인 구독) |
| `INSTAGRAM_TOKEN` | 인스타 게시용 시스템 사용자 토큰 (만료 없음) |
| `INSTA_MEDIA_TOKEN` | simple-init Contents 쓰기 전용 |
| `DATA_GO_KR_KEY` | 공공데이터포털 공공서비스(혜택) API 키 |
| `HIGGSFIELD_CREDENTIALS` | Higgsfield OAuth 인증 파일. 갱신 토큰이 1회용이라 매 실행 끝에 되쓴다 |
| `GH_SECRETS_PAT` | 위 Higgsfield 인증을 Secret에 되쓰는 PAT |
| `ATTACHMENTS_TOKEN` | 비공개 이슈 첨부 이미지를 받는 토큰 |

## 주의

- Higgsfield 갱신 토큰은 1회용이라 Higgsfield를 쓰는 워크플로는 같은 concurrency 그룹으로 겹치지 않게 돈다. 이미 쓴 토큰을 다시 쓰면 세션 전체가 끊긴다.
- 쉐어링크는 토스 정책상 상품 이미지 가공 금지, 광고 문구 필수. 로그인 쿠키는 5일 만료라 `cd sharelink && npm run login`으로 갱신한다.
- 인스타 해시태그는 게시물당 5개까지(2025-12~).
