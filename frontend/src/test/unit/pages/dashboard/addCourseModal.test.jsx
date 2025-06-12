import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AddCourseModal from '../../../../pages/dashboard/addCourseModal';
import { formItemList } from '../../../../pages/dashboard/constant';

const mockOnCancel = jest.fn();
const mockOnFinish = jest.fn();

beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }),
  });
});

describe('AddCourseModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders modal when open', () => {
    render(<AddCourseModal open={true} onCancel={mockOnCancel} onFinish={mockOnFinish} />);

    expect(screen.getByText('ADD COURSE')).toBeInTheDocument();

    formItemList.forEach(item => {
      expect(screen.getByLabelText(item.label)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Add course/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
  });

  test('does not render modal when closed', () => {
    render(<AddCourseModal open={false} onCancel={mockOnCancel} onFinish={mockOnFinish} />);

    expect(screen.queryByText('ADD COURSE')).not.toBeInTheDocument();
  });

  test('calls onCancel when cancel button clicked', () => {
    render(<AddCourseModal open={true} onCancel={mockOnCancel} onFinish={mockOnFinish} />);

    fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  test('calls onFinish with form data when submitted', async () => {
    render(<AddCourseModal open={true} onCancel={mockOnCancel} onFinish={mockOnFinish} />);

    for (const item of formItemList) {
      await userEvent.type(screen.getByLabelText(item.label), 'Test Input');
    }

    fireEvent.click(screen.getByRole('button', { name: /Add course/i }));

    await waitFor(() => {
      expect(mockOnFinish).toHaveBeenCalledTimes(1);
    });

    const expectedFormData = formItemList.reduce((data, item) => {
      data[item.name] = 'Test Input';
      return data;
    }, {});

    expect(mockOnFinish).toHaveBeenCalledWith(expectedFormData);
  });
});
