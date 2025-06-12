import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

jest.mock('antd', () => {
  const React = require('react');

  const Select = ({ options, ...rest }) => (
    <select {...rest}>
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>
          {opt.value}
        </option>
      ))}
    </select>
  );

  const Input  = props => <input {...props} />;
  const Button = ({ htmlType, onClick, children, ...p }) => (
    <button type={htmlType === 'submit' ? 'submit' : 'button'} onClick={onClick} {...p}>
      {children}
    </button>
  );

  const Form = ({ onFinish, children, ...p }) => {
    const handle = e => {
      e.preventDefault();
      onFinish(Object.fromEntries(new FormData(e.currentTarget).entries()));
    };
    return <form onSubmit={handle} {...p}>{children}</form>;
  };

  Form.Item = ({ label, name, children }) => (
    <div style={{ marginBottom: 4 }}>
      {label && <label htmlFor={name}>{label}</label>}
      {React.isValidElement(children)
        ? React.cloneElement(children, { name, id: name })
        : children}
    </div>
  );

  return { __esModule: true, Form, Select, Input, Button };
});

import AddForm from '../../../../pages/dashboard/addForm';

const mockFinish = jest.fn();
const mockCancel = jest.fn();

describe('<AddForm />', () => {
  beforeEach(() => jest.clearAllMocks());

  it('submits correct data', async () => {
    render(<AddForm onFinish={mockFinish} onCancel={mockCancel} />);

    await userEvent.type(screen.getByLabelText(/course name/i), 'CS101');
    await userEvent.type(screen.getByLabelText(/year/i), '2025');
    await userEvent.selectOptions(screen.getByLabelText(/semester/i), 'Fall');
    await userEvent.type(screen.getByLabelText(/course entry code/i), 'ABC123');

    fireEvent.click(screen.getByRole('button', { name: /add course/i }));

    await waitFor(() =>
      expect(mockFinish).toHaveBeenCalledWith({
        courseName: 'CS101',
        year: '2025',
        semester: 'Fall',
        entryCode: 'ABC123',
      })
    );
  });

  it('calls onCancel when Cancel clicked', () => {
    render(<AddForm onFinish={mockFinish} onCancel={mockCancel} />);
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(mockCancel).toHaveBeenCalledTimes(1);
  });
});
