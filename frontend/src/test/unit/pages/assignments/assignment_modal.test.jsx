// src/test/unit/pages/assignments/assignment_modal.test.jsx
//
// Unit-test for <AssignmentModal>.  Ensures the user can:
// 1. pick a file,
// 2. click “Submit”,
// 3. component POSTs the correct FormData to /upload_submission,
// 4. then navigates to /assignmentResult/<submissionID>.

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AssignmentModal from '../../../../pages/assignments/assignment_modal';
import { GlobalContext } from '../../../../App';

/* ───────────────────────── antd stub ────────────────────────── */

jest.mock('antd', () => {
  const real = jest.requireActual('antd');

  const FormItem = ({ children, ...rest }) => <div {...rest}>{children}</div>;
  const FormStub = ({ children, ...rest }) => <form {...rest}>{children}</form>;
  FormStub.Item = FormItem;

  const UploadStub = ({ beforeUpload }) => (
    <input
      data-testid="file-input"
      type="file"
      onChange={e => beforeUpload(e.target.files[0])}
    />
  );
  UploadStub.Dragger = UploadStub;

  return {
    ...real,
    Modal:  ({ children }) => <div data-testid="modal">{children}</div>,
    Form:   FormStub,
    Upload: UploadStub,
    Button: ({ onClick, children }) => (
      <button type="button" onClick={onClick}>
        {children}
      </button>
    ),
    message: { success: jest.fn(), error: jest.fn() },
  };
});

/* ────────────────────── react-router stub ───────────────────── */

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

/* ───────────────────── global setup/teardown ────────────────── */

beforeAll(() => {
  process.env.REACT_APP_API_URL = 'http://fake.api';
});

afterEach(() => {
  jest.clearAllMocks();
  mockNavigate.mockReset();
  global.fetch?.mockClear();
});

/* ───────────────────────────── test ─────────────────────────── */

describe('AssignmentModal', () => {
  test('uploads file, posts to API, and navigates to results', async () => {
    /* fake server response */
    global.fetch = jest.fn().mockResolvedValueOnce({
      json: () => Promise.resolve({ submissionID: 123 }),
    });

    /* render component with user context */
    render(
      <GlobalContext.Provider value={{ userInfo: { id: 42 } }}>
        <AssignmentModal
          open={true}
          onCancel={jest.fn()}
          assignmentID="A1"
          assignmentTitle="Assignment 1"
        />
      </GlobalContext.Provider>
    );

    /* user selects a file */
    const file = new File(['print("hi")'], 'main.py', { type: 'text/x-python' });
    await userEvent.upload(screen.getByTestId('file-input'), file);

    /* user clicks “Submit” */
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));

    /* fetch called once with correct FormData */
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const [url, opts] = global.fetch.mock.calls[0];

    expect(url).toBe('http://fake.api/upload_submission');
    expect(opts.method).toBe('POST');
    expect(opts.body).toBeInstanceOf(FormData);

    const fd = opts.body;
    expect(fd.get('file')).toBe(file);
    expect(fd.get('assignment')).toBe('Assignment 1');
    expect(fd.get('student_id')).toBe('42');
    expect(fd.get('assignment_id')).toBe('A1');

    /* navigation triggered */
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/assignmentResult/123')
    );
  });
});
