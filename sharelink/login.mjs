// 로그인 갱신: 브라우저 창을 띄우고, 토스 앱 푸시 승인으로 로그인해 홈이 보이면 쿠키를 저장하고 닫는다
// usage: npm run login
import { chromium } from 'playwright';
import { HOME_URL, authDaysLeft, saveState } from './lib.mjs';

const browser = await chromium.launch({ headless: false });
const ctx = await browser.newContext({ locale: 'ko-KR', viewport: { width: 1400, height: 900 } });
const page = await ctx.newPage();
await page.goto(HOME_URL);
console.log('브라우저에서 로그인해 주세요 (토스 앱 푸시 승인 → 계정 선택). 최대 10분 기다려요.');

await page.waitForURL(HOME_URL, { timeout: 10 * 60_000 });
await page.getByRole('button', { name: '링크 발급' }).first().waitFor({ timeout: 60_000 });
await saveState(ctx);
console.log(`로그인 저장 완료. 인증 남은 기간 ${authDaysLeft().toFixed(1)}일`);
await browser.close();
