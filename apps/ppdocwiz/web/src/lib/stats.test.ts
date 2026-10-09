import { describe, expect, it } from 'vitest';
import { consistent, mean, num, parseDataset, rsd, sd } from './stats';

describe('pp_data mirror', () => {
  it('num accepts comma decimals and ±', () => { expect(num('11,28')).toBe(11.28); expect(num('±0.5')).toBe(0.5); expect(num('')).toBeNaN(); });
  it('sample SD (n-1)', () => { expect(sd([2, 4, 4, 4, 5, 5, 7, 9])).toBeCloseTo(2.138, 3); expect(rsd([10, 10])).toBe(0); expect(mean([1, 2, 3])).toBe(2); });
  it('assert_consistent tolerance', () => { expect(consistent(11.28, 11.285)).toBe(true); expect(consistent(11.28, 11.30)).toBe(false); });
  it('parses csv, tsv and json', () => {
    expect(parseDataset('a.csv', 'x,y\n1,2').rows).toEqual([{ x: '1', y: '2' }]);
    expect(parseDataset('a.tsv', 'x\ty\n1\t2').columns).toEqual(['x', 'y']);
    expect(parseDataset('a.json', '[{"x":1}]').rows).toEqual([{ x: '1' }]);
  });
});
