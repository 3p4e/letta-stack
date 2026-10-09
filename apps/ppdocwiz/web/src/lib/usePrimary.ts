import { useEffect, useRef } from 'react';
import { useApp } from '../store/store';

/** Register the top-bar primary button for the current screen. */
export function usePrimary(label: string, run: () => void, disabled = false) {
  const set = useApp(s => s.set);
  const fn = useRef(run); fn.current = run;
  useEffect(() => { set({ primary: { label, run: () => fn.current(), disabled } }); }, [label, disabled, set]);
  useEffect(() => () => set({ primary: null }), [set]);
}
