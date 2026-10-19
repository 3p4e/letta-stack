import { describe, expect, it } from 'vitest';
import type { Job } from '../api/types';
import { pickJob, reviewLocks, stillRunning } from './jobview';

const job = (id: string, status: Job['status'] = 'done') => ({ id, status } as Job);

describe('Jobs screen selection (review 19.10.2026)', () => {
  it('shows the selected job when listed, asks for it by id when not, and never falls back to jobs[0] silently', () => {
    const list = [job('a'), job('b')];
    expect(pickJob(list, 'b', null).job?.id).toBe('b');
    expect(pickJob(list, 'zz', null)).toEqual({ job: null, fetch: 'zz', empty: false });
    expect(pickJob(list, 'zz', job('zz')).job?.id).toBe('zz');
    expect(pickJob(list, null, null).job?.id).toBe('a');
    expect(pickJob([], null, null)).toEqual({ job: null, fetch: null, empty: true });
  });
  it('locks both review decisions while one is in flight; Return also needs a note', () => {
    expect(reviewLocks(false, '')).toEqual({ approve: true, ret: false });
    expect(reviewLocks(false, 'fix 3.0')).toEqual({ approve: true, ret: true });
    expect(reviewLocks(true, 'fix 3.0')).toEqual({ approve: false, ret: false });
  });
  it('polls only while a job is queued or running', () => {
    expect(stillRunning([job('a', 'done'), job('b', 'awaiting_review'), job('c', 'failed')])).toBe(false);
    expect(stillRunning([job('a', 'done'), job('b', 'queued')])).toBe(true);
  });
});
