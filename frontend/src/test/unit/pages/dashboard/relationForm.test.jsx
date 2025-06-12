import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

jest.mock('antd', () => {
  const React = require('react');

  const Alert = ({ message }) => <div role="alert">{message}</div>;

  const Input = props => <input {...props} />;

  const Button = ({ htmlType, onClick, type, children, ...rest }) => (
    <button
      type={htmlType === 'submit' ? 'submit' : 'button'}
      onClick={onClick}
      data-variant={type}        
      {...rest}
    >
      {children}
    </button>
  );

  const Form = ({ onFinish, children, ...rest }) => {
    const handleSubmit = e => {
      e.preventDefault();
      onFinish(Object.fromEntries(new FormData(e.currentTarget).entries()));
    };
    return (
      <form onSubmit={handleSubmit} {...rest}>
        {children}
      </form>
    );
  };

  Form.Item = ({ label, name, children }) => {
    if (name) {
      return (
        <label style={{ display: 'block', marginBottom: 4 }}>
          {label}
          {React.isValidElement(children)
            ? React.cloneElement(children, { name })
            : children}
        </label>
      );
    }
    return <div style={{ marginTop: 8 }}>{children}</div>;
  };

  return { __esModule: true, Alert, Input, Button, Form };
});

import RelationForm from '../../../../pages/dashboard/relationForm';

const mockFinish = jest.fn();
const mockCancel = jest.fn();

beforeEach(() => jest.clearAllMocks());

describe('<RelationForm />', () => {
  test('renders alert, input, and buttons', () => {
    render(<RelationForm onFinish={mockFinish} onCancel={mockCancel} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(
      screen.getByLabelText(/course entry code/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /^add course$/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /^cancel$/i })
    ).toBeInTheDocument();
  });

  test('calls onCancel when Cancel clicked', () => {
    render(<RelationForm onFinish={mockFinish} onCancel={mockCancel} />);
    fireEvent.click(screen.getByRole('button', { name: /^cancel$/i }));
    expect(mockCancel).toHaveBeenCalledTimes(1);
  });

  test('submits entry code via onFinish', async () => {
    render(<RelationForm onFinish={mockFinish} onCancel={mockCancel} />);

    await userEvent.type(
      screen.getByLabelText(/course entry code/i),
      'ABC123'
    );
    fireEvent.click(screen.getByRole('button', { name: /^add course$/i }));

    await waitFor(() =>
      expect(mockFinish).toHaveBeenCalledWith({ entryCode: 'ABC123' })
    );
  });
});
