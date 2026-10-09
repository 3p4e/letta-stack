import { useEffect, useState } from 'react';
import { ApiError } from './api/types';
import { Shell, SignIn } from './components/Shell';
import { Builder } from './screens/Builder';
import { Chat } from './screens/Chat';
import { Fleet } from './screens/Fleet';
import { Formatter } from './screens/Formatter';
import { Jobs } from './screens/Jobs';
import { Library } from './screens/Library';
import { Preview } from './screens/Preview';
import { Questionnaire } from './screens/Questionnaire';
import { Reports } from './screens/Reports';
import { Verify } from './screens/Verify';
import { useApp, type Screen } from './store/store';

const SCREENS: Record<Screen, () => JSX.Element> = { builder: Builder, chat: Chat, quest: Questionnaire, format: Formatter, report: Reports, library: Library, jobs: Jobs, verify: Verify, preview: Preview, fleet: Fleet };

export function App() {
  const { authed, api, set, screen } = useApp();
  const [unconfigured, setUnconfigured] = useState(false);
  useEffect(() => {
    if (authed !== null) return;
    // Probe a gated route: 200 → the cookie is valid; 401 → sign in; 503 → server has no key.
    api.doctypes().then(() => set({ authed: true })).catch((e: ApiError) => { setUnconfigured(e.status === 503); set({ authed: false }); });
  }, [authed, api, set]);
  if (authed === null) return <div style={{ height: '100vh', background: '#0f1a26' }} />;
  if (!authed) return <SignIn unconfigured={unconfigured} />;
  const S = SCREENS[screen];
  return <Shell><S /></Shell>;
}
