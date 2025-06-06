// src/test/unit/pages/assignments/constants.test.js
//
// Unit-tests for columns[] in src/pages/assignments/constants.js
// (same folder that holds AssignmentModal).

import moment from 'moment';
import { columns } from '../../../../pages/assignments/constant'; // 4-levels up from this test file

/* helper – find column object by dataIndex */
const col = key => columns.find(c => c.dataIndex === key);

describe('assignments/constants columns', () => {
  it('exposes the five expected dataIndex keys', () => {
    expect(columns.map(c => c.dataIndex)).toEqual([
      'name',
      'status',
      'grades',
      'released',
      'due',
    ]);
  });

  it('STATUS render returns “Submitted” for 1, “No Submission” otherwise', () => {
    const render = col('status').render;
    expect(render(1)).toBe('Submitted');
    expect(render(0)).toBe('No Submission');
    expect(render(42)).toBe('No Submission');
  });

  it('GRADES render returns raw value or “-” when empty', () => {
    const render = col('grades').render;
    expect(render(88)).toBe(88);
    expect(render('A')).toBe('A');
    expect(render(null)).toBe('-');
    expect(render(undefined)).toBe('-');
    expect(render('')).toBe('-');
  });

  it('RELEASED & DUE render format timestamps as “MMM DD AT h:mmA” (uppercase)', () => {
    const ts = '2025-05-28T14:05:00-05:00'; // 2:05 PM CDT
    const expected = moment(ts).format('MMM DD [AT] h:mmA').toUpperCase();
    expect(col('released').render(ts)).toBe(expected);
    expect(col('due').render(ts)).toBe(expected);
  });

  it('NAME “soeter” comparator behaves as a simple alphabetical greater-than', () => {
    const cmp = col('name').soeter;
    const a = { name: 'Alice' };
    const b = { name: 'Bob' };
    expect(cmp(a, b)).toBe(false); // 'Alice' > 'Bob' → false
    expect(cmp(b, a)).toBe(true);  // 'Bob'   > 'Alice' → true
  });
});
