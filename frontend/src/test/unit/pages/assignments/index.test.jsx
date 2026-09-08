import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

jest.mock('../../../../App', () => {
  const React = require('react');
  return {
    GlobalContext: React.createContext({}),
  };
});

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

jest.mock(
  '../../../../pages/assignments/assignment_modal',
  () => {
    const React = require('react');
    const mockModal = jest.fn(({ open }) =>
      React.createElement(
        'div',
        { 'data-testid': 'assignment-modal' },
        open ? 'OPEN' : 'CLOSED'
      )
    );
    return { __esModule: true, default: mockModal };
  }
);

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams  : () => ({ courseId: 'CS101' }),
}));

const fakeAssignment = {
  id: '1',
  name: 'Homework 1',
  published_date: '2025-05-28T12:00:00-05:00',
  due_date:       '2099-12-31T23:59:00-06:00',   // far future
  late_due_date:  '2100-01-10T23:59:00-06:00',
};

const Assignments = require('../../../../pages/assignments').default;
const { GlobalContext } = require('../../../../App');

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

beforeAll(() => {
  process.env.REACT_APP_API_URL = 'http://fake.api';
});
afterEach(() => {
  jest.clearAllMocks();
  mockNavigate.mockReset();
});

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

  const rowBtn = await screen.findByRole('button', { name: /homework 1/i });
  await userEvent.click(rowBtn);

  const modalMock = require('../../../../pages/assignments/assignment_modal').default;

  expect(modalMock).toHaveBeenCalled();
  const { open, assignmentID, assignmentTitle } = modalMock.mock.calls.pop()[0];
  expect(open).toBe(true);
  expect(assignmentID).toBe('1');
  expect(assignmentTitle).toBe('Homework 1');

  expect(mockNavigate).not.toHaveBeenCalled();
});

it('does not redirect a student away from their assignments page', async () => {
  queueFetches();

  render(
    <GlobalContext.Provider
      value={{
        userInfo:  { id: 42 },
        courseInfo:{ name: 'Intro CS', semester: 'Fall', year: '2025' },
        courseRole: 'student',
      }}
    >
      <Assignments />
    </GlobalContext.Provider>
  );

  await screen.findByRole('button', { name: /homework 1/i });

  expect(mockNavigate).not.toHaveBeenCalledWith('/instructorDashboard/CS101');
});

it('redirects a TA away from the student assignments page', async () => {
  queueFetches();

  render(
    <GlobalContext.Provider
      value={{
        userInfo:  { id: 42 },
        courseInfo:{ name: 'Intro CS', semester: 'Fall', year: '2025' },
        courseRole: 'ta',
      }}
    >
      <Assignments />
    </GlobalContext.Provider>
  );

  await waitFor(() =>
    expect(mockNavigate).toHaveBeenCalledWith('/instructorDashboard/CS101')
  );
});

it('shows "Pending" in the GRADES column when grades are held and not yet published', async () => {
  global.fetch = jest
    .fn()
    /* /get_course_assignments */
    .mockResolvedValueOnce({ json: () => Promise.resolve([fakeAssignment]) })
    /* /get_extension */
    .mockResolvedValueOnce({ json: () => Promise.resolve({}) })
    /* /get_active_submission */
    .mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          completed: true,
          score: null,
          grades_published: false,
          id: 'sub1',
          late: false,
        }),
    });

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

  expect(await screen.findByTestId('cell-0-2')).toHaveTextContent('Pending');
});

it('shows the score in the GRADES column once grades are published', async () => {
  global.fetch = jest
    .fn()
    .mockResolvedValueOnce({ json: () => Promise.resolve([fakeAssignment]) })
    .mockResolvedValueOnce({ json: () => Promise.resolve({}) })
    .mockResolvedValueOnce({
      json: () =>
        Promise.resolve({
          completed: true,
          score: 92,
          grades_published: true,
          id: 'sub1',
          late: false,
        }),
    });

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

  expect(await screen.findByTestId('cell-0-2')).toHaveTextContent('92');
});

it('redirects an instructor away from the student assignments page', async () => {
  queueFetches();

  render(
    <GlobalContext.Provider
      value={{
        userInfo:  { id: 42 },
        courseInfo:{ name: 'Intro CS', semester: 'Fall', year: '2025' },
        courseRole: 'instructor',
      }}
    >
      <Assignments />
    </GlobalContext.Provider>
  );

  await waitFor(() =>
    expect(mockNavigate).toHaveBeenCalledWith('/instructorDashboard/CS101')
  );
});
