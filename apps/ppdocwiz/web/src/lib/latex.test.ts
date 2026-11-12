import { describe, expect, it } from 'vitest';
import { formulaMarkdown, formulasOf, insertFormula, insertMarkdown, localProblems, pieces } from './latex';

describe('formula grammar (mirror of pp_math)', () => {
  it('finds inline and display formulas and leaves money alone', () => {
    expect(formulasOf('Total $a_1+b$ and $$\\frac{a}{b}$$ and 5 $ vs 6 $ and \\$5')).toEqual(['a_1+b', '\\frac{a}{b}']);
    expect(pieces('x $y$ z').map(p => p.kind)).toEqual(['text', 'math', 'text']);
    expect(pieces('$$a=b$$')[0]).toEqual({ kind: 'display', value: 'a=b' });
  });
  it('does not read a currency pair as a formula', () => {
    expect(formulasOf('costs $5 and $6')).toEqual([]);
    expect(formulasOf('between $ 5 and 6 $')).toEqual([]);
  });
});

describe('local sanity checks', () => {
  it('catches an empty formula, unbalanced braces and a lone \\left', () => {
    expect(localProblems('')).toHaveLength(1);
    expect(localProblems('\\frac{a}{b')).toContain('braces { } do not match');
    expect(localProblems('\\left( x')).toContain('\\left and \\right do not pair');
    expect(localProblems('\\frac{a}{b}')).toEqual([]);
    expect(localProblems('\\{x\\}')).toEqual([]);
  });
});

describe('insertion', () => {
  it('writes inline in place and puts display forms on their own line', () => {
    expect(insertFormula('abc def', 4, 4, 'x^2', 'inline')).toEqual({ text: 'abc $x^2$def', caret: 9 });
    const d = insertFormula('line one\nline two', 8, 8, 'x', 'display');
    expect(d.text).toBe('line one\n$$x$$\nline two');
    expect(formulaMarkdown(' a ', 'eq')).toBe('[[EQ]]\n$a$\n[[/EQ]]');
  });
  it('replaces a selection', () => {
    expect(insertFormula('a XX b', 2, 4, 'y', 'inline').text).toBe('a $y$ b');
  });
});

describe('finished Markdown from the dialog', () => {
  it('is written as it is, block forms on their own line, never wrapped twice', () => {
    expect(insertMarkdown('a b', 2, 2, '$x$').text).toBe('a $x$b');
    expect(insertMarkdown('a\nb', 2, 2, '$$x$$').text).toBe('a\n$$x$$\nb');
    expect(insertMarkdown('a', 1, 1, '[[EQ]]\n$x$\n[[/EQ]]').text).toBe('a\n[[EQ]]\n$x$\n[[/EQ]]\n');
  });
});
