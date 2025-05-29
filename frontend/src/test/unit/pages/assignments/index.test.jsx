/**
 * src/test/unit/pages/assignments/index.test.jsx
 *
 * Integration-y test for <Assignments/>.
 * ─ fetches a single assignment
 * ─ shows it as a link-button
 * ─ clicking (unsubmitted, not-past-due) opens AssignmentModal
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Assignments from '../../../../pages/assignments';
import { GlobalContext } from '../../../../App';

/* ───────────── lightweight antd stub ───────────── */
jest.mock('antd', () => {
  const real = jest.requireActual('antd');

  const Button = ({ onClick, children }) => (
    <button type="button" onClick={onClick}>
      {children}
    </button>
  );

  const Table = ({ columns, dataSource }) => (
    <div data-testid="table">
      {dataSource.map((row, r) =>
        columns.map((col, c) => {
          const raw = row[col.dataIndex];
          const out = col.render ? col.render(raw, row) : raw;
          return (
            <span key={`${r}-${c}`} data-testid={`cell-${r}-${c}`}>
              {out}
            </span>
          );
        })
      )}
    </div>
  );

  const PageHeader   = ({ children }) => <div>{children}</div>;
  const Descriptions = ({ children }) => <div>{children}</div>;
  Descriptions.Item  = ({ children }) => <span>{children}</span>;
  const Card    = ({ children }) => <div>{children}</div>;
  const message = { error: jest.fn(), success: jest.fn() };

  return { ...real, Button, Table, PageHeader, Descriptions, Card, message };
});

/* ───────────── AssignmentModal stub ─────────────
   * declare inside factory → no hoisting issues
   * later we pull it back via require() to assert calls           */
jest.mock(
  '../../../../pages/assignments/assignment_modal',
  () => {
    const mockModal = jest.fn(({ open }) => (
      <div data-testid="assignment-modal">{open ? 'OPEN' : 'CLOSED'}</div>
    ));
    return { __esModule: true, default: mockModal };
  }
);

/* ───────────── react-router stubs ───────────── */
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams  : () => ({ courseId: 'CS101' }),
}));

/* ───────────── helper to queue fetches ───────────── */
const fakeAssignment = {
  id: '1',
  name: 'Homework 1',
  published_date: '2025-05-28T12:00:00-05:00',
  due_date:       '2099-12-31T23:59:00-06:00',   // far future
  late_due_date:  '2100-01-10T23:59:00-06:00',
};

const queueFetches = () => {
  global.fetch = jest
    .fn()
    /* /get_course_assignments */
    .mockResolvedValueOnce({ json: () => Promise.resolve([fakeAssignment]) })
    /* /get_extension */
    .mockResolvedValueOnce({ json: () => Promise.resolve({}) })
    /* /get_active_submission */
    .mockResolvedValueOnce({
      json: () =>
        Promise.resolve({ completed: false, score: null, id: null, late: false }),
    });
};

/* ───────────── global hooks ───────────── */
beforeAll(() => {
  process.env.REACT_APP_API_URL = 'http://fake.api';
});
afterEach(() => {
  jest.clearAllMocks();
  mockNavigate.mockReset();
});

/* ───────────────────── TEST ───────────────────── */
it('opens AssignmentModal when unsubmitted assignment clicked', async () => {
  queueFetches();

  render(
    <GlobalContext.Provider
      value={{
        userInfo:  { id: 42 },
        courseInfo:{ name: 'Intro CS', semester: 'Fall', year: '2025' },
      }}
    >
      <Assignments />
    </GlobalContext.Provider>
  );

  /* wait for the assignment link to appear */
  const rowBtn = await screen.findByRole('button', { name: /homework 1/i });
  await userEvent.click(rowBtn);

  /* grab the stub via require so it’s definitely initialised */
  const modalMock = require('../../../../pages/assignments/assignment_modal').default;

  expect(modalMock).toHaveBeenCalled();
  const { open, assignmentID, assignmentTitle } = modalMock.mock.calls.pop()[0];
  expect(open).toBe(true);
  expect(assignmentID).toBe('1');
  expect(assignmentTitle).toBe('Homework 1');

  expect(screen.getByTestId('assignment-modal')).toHaveTextContent('OPEN');
  expect(mockNavigate).not.toHaveBeenCalled();
});
