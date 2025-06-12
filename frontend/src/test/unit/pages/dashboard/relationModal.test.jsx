import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

jest.mock('antd', () => {
  const React = require('react');

  const Modal = ({ title, open, children }) =>
    open ? (
      <div data-testid="modal">
        <h2>{title}</h2>
        {children}
      </div>
    ) : null;

  const Alert = ({ message }) => <div role="alert">{message}</div>;
  const Input = props => <input {...props} />;

  const Button = ({ htmlType, onClick, type, children, ...rest }) => (
    <button
      type={htmlType === 'submit' ? 'submit' : 'button'}
      data-variant={type}
      onClick={onClick}
      {...rest}
    >
      {children}
    </button>
  );

  const Form = ({ onFinish, children }) => {
    const handle = e => {
      e.preventDefault();
      onFinish(Object.fromEntries(new FormData(e.currentTarget).entries()));
    };
    return <form onSubmit={handle}>{children}</form>;
  };
  Form.Item = ({ label, name, children }) => (
    name ? (
      <label style={{ display: 'block', marginBottom: 4 }}>
        {label}
        {React.cloneElement(children, { name })}
      </label>
    ) : (
      <div style={{ marginTop: 8 }}>{children}</div>
    )
  );

  return { __esModule: true, Modal, Alert, Input, Button, Form };
});

import RelationModal from '../../../../pages/dashboard/relationModal';

const mockOk = jest.fn();
const mockCancel = jest.fn();

beforeEach(() => jest.clearAllMocks());

describe('<RelationModal />', () => {
  it('renders correctly when open', () => {
    render(<RelationModal open onCancel={mockCancel} onOk={mockOk} />);

    expect(screen.getByTestId('modal')).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /add course via entry code/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByLabelText(/course entry code/i)).toBeInTheDocument();
    expect(screen.getByText(/^add course$/i)).toBeInTheDocument();
    expect(screen.getByText(/^cancel$/i)).toBeInTheDocument();
  });

  it('renders nothing when closed', () => {
    const { queryByTestId } = render(
      <RelationModal open={false} onCancel={mockCancel} onOk={mockOk} />
    );
    expect(queryByTestId('modal')).toBeNull();
  });

  it('calls onCancel once when Cancel clicked', () => {
    render(<RelationModal open onCancel={mockCancel} onOk={mockOk} />);
    fireEvent.click(screen.getAllByRole('button')[1]);
    expect(mockCancel).toHaveBeenCalledTimes(1);
  });

  it('submits entry code through onOk', async () => {
    render(<RelationModal open onCancel={mockCancel} onOk={mockOk} />);

    await userEvent.type(
      screen.getByLabelText(/course entry code/i),
      'ABC123'
    );
    fireEvent.click(screen.getAllByRole('button')[0]);

    await waitFor(() =>
      expect(mockOk).toHaveBeenCalledWith({ entryCode: 'ABC123' })
    );
  });
});
