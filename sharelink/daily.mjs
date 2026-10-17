// 매일 새벽: 쉐어링크 홈의 하루특가·BEST에서 품절 아닌 후보를 골라 링크를 발급하고, 후보 목록 이슈를 연다
// → sharelink-draft 워크플로가 특가 1 + 꿀템 3을 골라 모음 글 초안을 댓글로 단다
// usage: npm run daily  (DRY_RUN=1 이면 링크 발급·이슈 생성 없이 후보만 출력)
import fs from 'node:fs';
import { chromium } from 'playwright';
import { HOME_URL, REPO, STATE, authDaysLeft, gh, notify, saveState } from './lib.mjs';

const DRY_RUN = process.env.DRY_RUN === '1';
const MAX_DEALS = 6;
const MAX_BEST = 6;

const fail = message => {
  console.error(message);
  notify(message);
  process.exit(1);
};

const daysLeft = authDaysLeft();
if (daysLeft <= 0) fail('쉐어링크 로그인이 만료됐어요. 맥에서 `cd ~/automation-/sharelink && npm run login` 해 주세요.');

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({
  storageState: STATE,
  locale: 'ko-KR',
  viewport: { width: 1400, height: 900 },
  permissions: ['clipboard-read', 'clipboard-write'],
});
const page = await ctx.newPage();

try {
  await page.goto(HOME_URL);
  await page.waitForLoadState('networkidle').catch(() => {});
  const buttons = page.getByRole('button', { name: '링크 발급' });
  if (!page.url().startsWith(HOME_URL) || (await buttons.count()) === 0) {
    fail('쉐어링크 로그인이 풀렸어요. 맥에서 `cd ~/automation-/sharelink && npm run login` 해 주세요.');
  }

  // '링크 발급' 버튼마다 카드(이미지와 가격이 함께 있는 가장 가까운 조상)의 텍스트와 이미지를 읽는다
  const cards = await page.evaluate(() =>
    [...document.querySelectorAll('button')]
      .filter(b => b.innerText.trim() === '링크 발급')
      .map((b, index) => {
        let el = b;
        while (el && !(el.querySelector('img') && /원/.test(el.innerText))) el = el.parentElement;
        return { index, text: el.innerText.replace(/\s+/g, ' ').trim(), img: el.querySelector('img')?.src ?? '' };
      }),
  );

  // 이미지 최적화 주소 안에 원본 주소가 인코딩돼 있다 → 원본 그대로 쓴다
  for (const c of cards) {
    const inner = c.img.match(/image-optimize\/[^/]+\/(https%3A.+)$/);
    c.image = inner ? decodeURIComponent(inner[1]) : c.img;
    // "… 개당 N원 수익 [지금 30일 내 최저가예요] 상품명 가격원 …"
    c.name = c.text.match(/수익 (?:지금 30일 내 최저가예요 )?(.+?) [\d,]+원/)?.[1] ?? c.text;
  }

  // 하루특가 카드는 '선착순특가'로, BEST 카드는 순위 숫자로 시작한다. 두 섹션에 같은 상품이 겹쳐 나온다
  const fresh = cards.filter(c => !c.text.includes('품절'));
  const deals = fresh.filter(c => c.text.startsWith('선착순특가')).slice(0, MAX_DEALS);
  const best = fresh.filter(c => /^\d+ /.test(c.text) && !deals.some(d => d.name === c.name)).slice(0, MAX_BEST);
  const candidates = [...deals.map(c => ({ ...c, kind: '하루특가' })), ...best.map(c => ({ ...c, kind: 'BEST' }))];
  if (candidates.length === 0) fail('쉐어링크 홈에서 후보 상품을 찾지 못했어요. 화면 구조가 바뀌었을 수 있어요.');

  for (const c of candidates) {
    if (DRY_RUN) continue;
    await buttons.nth(c.index).click();
    await page.waitForTimeout(1500);
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    c.link = copied.match(/https:\/\/toss\.(shopping|im)\/\S+/)?.[0] ?? '';
  }

  const issued = candidates.filter(c => DRY_RUN || c.link);
  console.log(issued.map(c => `[${c.kind}] ${c.name} ${c.link ?? ''}\n    ${c.image}`).join('\n'));
  if (DRY_RUN) process.exit(0);
  if (issued.length === 0) fail('쉐어링크 링크 발급에 실패했어요. 화면 구조가 바뀌었을 수 있어요.');

  const today = new Date().toLocaleDateString('ko-KR', { timeZone: 'Asia/Seoul', month: 'numeric', day: 'numeric' });
  const body = [
    '<!-- auto -->',
    `자동 수집한 후보 ${issued.length}개예요 (${new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })} 기준).`,
    '',
    ...issued.map((c, i) =>
      [`### 후보 ${i + 1} (${c.kind})`, `- 카드: ${c.text.replace(/\s*링크 발급$/, '')}`, `- 링크: ${c.link}`, `- 이미지: ${c.image}${c.image.includes('/taca/ai/') ? ' (토스 AI 썸네일)' : ''}`, ''].join('\n'),
    ),
  ].join('\n');
  fs.writeFileSync('/tmp/sharelink-issue.md', body);
  const url = gh(['issue', 'create', '--repo', REPO, '--label', 'sharelink', '--title', `[오늘의 특가] ${today} 자동`, '--body-file', '/tmp/sharelink-issue.md']);
  console.log('이슈 생성:', url.trim());

  await saveState(ctx);
  if (daysLeft < 1.2) notify(`쉐어링크 로그인이 ${daysLeft.toFixed(1)}일 뒤 만료돼요. 맥에서 \`npm run login\`으로 갱신해 주세요.`);
} catch (e) {
  fail(`쉐어링크 자동 실행 중 오류: ${e.message.split('\n')[0]}`);
} finally {
  await browser.close();
}
