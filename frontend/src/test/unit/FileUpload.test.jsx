// frontend/tests/unit/FileUpload.test.jsx
import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUpload from '../../components/FileUpload';
import axios from 'axios';

// mock deps

jest.mock('../../components/TestResults', () => ({ data }) => (
  <div data-testid="test-results">{JSON.stringify(data)}</div>
));
jest.mock('../../components/TestResult', () => (props) => (
  <div data-testid="test-log">{props.testOutput}</div>
));

jest.mock('axios');

beforeAll(() => {
  process.env.REACT_APP_API_URL = 'http://fake.api';
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('FileUpload component', () => {
  test('uploads file, posts to API, and renders results/logs', async () => {
    const fakeResults = {passed: 3, failed: 0};
    const fakeLogs = 'Everything compiled ✔︎';

    axios.post.mockResolvedValueOnce({
      data: {
        results: JSON.stringify(fakeResults),
        logs: fakeLogs,
      },
    });

    render(<FileUpload />);

    const select = screen.getByRole('combobox');
    expect(select.value).toBe('A1');

    await userEvent.selectOptions(select, 'test');
    expect(select.value).toBe('test');

    const fileInput = screen.getByLabelText(/choose file/i); // from <p> text
    const file = new File(['print("hi")\n'], 'main.py', {type: 'text/x-python'});
    await userEvent.upload(fileInput, file);
    expect(fileInput.files[0]).toStrictEqual(file);

    fireEvent.submit(screen.getByRole('form', { name: /upload form/i }));
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledTimes(1);
    });
    const [url, formData] = axios.post.mock.calls[0];
    expect(url).toBe('http://fake.api/upload');
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get('assignment')).toBe('test');
    expect(formData.get('file')).toBe(file);

    expect(await screen.findByTestId('test-results')).toHaveTextContent(
      '"passed":3'
    );
    expect(screen.getByTestId('test-log')).toHaveTextContent(fakeLogs);
  });
});
