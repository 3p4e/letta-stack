import { useEffect, useState } from 'react';
import { ApiError } from './api/types';
import { ChangePassword, Shell, SignIn } from './components/Shell';
import { Builder } from './screens/Builder';
import { Chat } from './screens/Chat';
import { Fleet } from './screens/Fleet';
import { Users } from './screens/Users';
import { Formatter } from './screens/Formatter';
import { Jobs } from './screens/Jobs';
import { Library } from './screens/Library';
import { Workflow } from './screens/Workflow';
import { Preview } from './screens/Preview';
import { Questionnaire } from './screens/Questionnaire';
import { Reports } from './screens/Reports';
import { Verify } from './screens/Verify';
import { useApp, type Screen } from './store/store';

const SCREENS: Record<Screen, () => JSX.Element> = { flow: Workflow, builder: Builder, chat: Chat, quest: Questionnaire, format: Formatter, report: Reports, library: Library, jobs: Jobs, verify: Verify, preview: Preview, fleet: Fleet, users: Users };

export function App() {
  const { authed, api, set, screen, dataRev, flash } = useApp();
  const [unconfigured, setUnconfigured] = useState(false);
  // The initial password from the server is changed at the first sign-in (Head of QC, 19.10.2026).
  const [mustChange, setMustChange] = useState(false);
  // A failed /api/me is said, not swallowed, and tried again on the next data change (review 19.10.2026).
  useEffect(() => { if (authed) api.me().then(m => { set({ me: m }); setMustChange(m.must_change); }).catch((e: ApiError) => flash(`/api/me → ${[e.status || '', e.message].filter(Boolean).join(' · ')}`)); }, [authed, api, set, dataRev, flash]);
  useEffect(() => {
    if (authed !== null) return;
    // Probe a gated route: 200 → the cookie is valid; 401 → sign in; 503 → server has no key.
    // 403 "password change required" (review 19.10.2026): the cookie is valid, the person must change the temporary
    // password first — /api/me is allowed through and the forced-change card follows from must_change.
    api.doctypes().then(() => set({ authed: true })).catch((e: ApiError) => { setUnconfigured(e.status === 503); set({ authed: e.status === 403 }); });
  }, [authed, api, set]);
  if (authed === null) return <div style={{ height: '100vh', background: '#0f1a26' }} />;
  if (!authed) return <SignIn unconfigured={unconfigured} />;
  if (mustChange) return <ChangePassword forced onDone={() => setMustChange(false)} />;
  const S = SCREENS[screen];
  return <Shell><S /></Shell>;
}
