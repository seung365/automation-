// 쉐어링크 로컬 스크립트 공용: 로그인 상태 파일, GitHub 호출(seung365 계정 고정)
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';

export const STATE = `${os.homedir()}/.sharelink-browser/state.json`;
export const REPO = 'seung365/automation-';
export const HOME_URL = 'https://sharelink.toss.im/home';

export const saveState = async ctx =>
  fs.writeFileSync(STATE, JSON.stringify(await ctx.storageState()), { mode: 0o600 });

// 인증 쿠키 남은 일수 (없으면 0)
export const authDaysLeft = () => {
  if (!fs.existsSync(STATE)) return 0;
  const auth = JSON.parse(fs.readFileSync(STATE, 'utf8')).cookies.find(c => c.name === 'TBIZAUTH');
  return auth ? (auth.expires - Date.now() / 1000) / 86400 : 0;
};

// gh 활성 계정이 회사 계정이어도 항상 개인 계정으로 호출한다
const ghToken = () => execFileSync('gh', ['auth', 'token', '--user', 'seung365'], { encoding: 'utf8' }).trim();
export const gh = args => execFileSync('gh', args, { encoding: 'utf8', env: { ...process.env, GH_TOKEN: ghToken() } });

// 내가 연 이슈는 나에게 메일이 안 오므로, 봇이 이슈를 열게 하는 notify 워크플로로 알린다
export const notify = message => {
  try {
    execFileSync('osascript', ['-e', `display notification ${JSON.stringify(message)} with title "쉐어링크 자동화"`]);
  } catch {}
  try {
    gh(['workflow', 'run', 'notify.yml', '--repo', REPO, '-f', `message=${message}`]);
  } catch (e) {
    console.error('알림 워크플로 실행 실패', e.message);
  }
};
