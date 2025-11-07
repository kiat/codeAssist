import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
  const real = jest.requireActual('react-router-dom');
  return { ...real, useNavigate: () => mockNavigate };
});

jest.mock('antd', () => {
  const real  = jest.requireActual('antd');
  const React = require('react');

  const Modal = ({ title, open, onCancel, children }) =>
    open ? (
      <div data-testid="modal">
        <h2>{title}</h2>
        <button data-testid="close" onClick={onCancel}>×</button>
        {children}
      </div>
    ) : null;

  const Form = ({ onFinish, children }) => {
    const handle = e => {
      e.preventDefault();
      onFinish(Object.fromEntries(new FormData(e.currentTarget).entries()));
    };
    return <form onSubmit={handle}>{children}</form>;
  };
  Form.Item = ({ label, name, children }) =>
    name ? (
      <label>
        {label}
        {React.cloneElement(children, { name })}
      </label>
    ) : (
      <div>{children}</div>
    );

  const Input = props => <input {...props} />;
  Input.Password = props => <input type="password" {...props} />;

  const Button = ({ htmlType, children }) => (
    <button type={htmlType || 'button'}>{children}</button>
  );

  const Collapse = ({ children }) => <div>{children}</div>;
  Collapse.Panel = ({ children }) => <div>{children}</div>;

  return {
    __esModule: true,
    ...real,
    Modal,
    Form,
    Input,
    Button,
    Collapse,
  };
});

jest.mock(
  '../../../../components/layout/pageContent',
  () => ({ __esModule: true, default: ({ children }) => <div>{children}</div> })
);
jest.mock(
  '../../../../components/layout/pageBottom',
  () => ({ __esModule: true, default: ({ children }) => <div>{children}</div> })
);

jest.mock('../../../../services/user', () => ({ userLogin: jest.fn() }));
import { userLogin } from '../../../../services/user';

import { GlobalContext } from '../../../../App';
const mockUpdate = jest.fn();

import LogInModal from '../../../../pages/home/logInModal';

describe('<LogInModal />', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('is hidden when open=false and visible when open=true', () => {
    const { rerender } = render(
      <GlobalContext.Provider value={{ updateUserInfo: mockUpdate }}>
        <LogInModal open={false} onCancel={() => {}} />
      </GlobalContext.Provider>
    );

    expect(screen.queryByTestId('modal')).toBeNull();

    rerender(
      <GlobalContext.Provider value={{ updateUserInfo: mockUpdate }}>
        <LogInModal open={true} onCancel={() => {}} />
      </GlobalContext.Provider>
    );

    expect(screen.getByTestId('modal')).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^log in$/i })).toBeInTheDocument();
  });

  it('calls onCancel when the “×” is clicked', () => {
    const mockCancel = jest.fn();
    render(
      <GlobalContext.Provider value={{ updateUserInfo: mockUpdate }}>
        <LogInModal open={true} onCancel={mockCancel} />
      </GlobalContext.Provider>
    );

    fireEvent.click(screen.getByTestId('close'));
    expect(mockCancel).toHaveBeenCalledTimes(1);
  });

  it('submits credentials, updates context, and writes to localStorage', async () => {
    userLogin.mockResolvedValueOnce({ data: { name: 'Bob', id: 5, role: 'student' } });

    render(
      <GlobalContext.Provider value={{ updateUserInfo: mockUpdate }}>
        <LogInModal open={true} onCancel={() => {}} />
      </GlobalContext.Provider>
    );

    await userEvent.type(screen.getByLabelText(/email/i), 'bob@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'hunter2');
    fireEvent.click(screen.getByRole('button', { name: /^log in$/i }));

    await waitFor(() => {
      expect(userLogin).toHaveBeenCalledWith({
        email: 'bob@example.com',
        password: 'hunter2',
      });
      expect(mockUpdate).toHaveBeenCalledWith({
        name: 'Bob',
        id: 5,
        isStudent: true,
        role: 'student',
        isAdmin: false,
      });
      expect(JSON.parse(localStorage.getItem('userInfo'))).toEqual({
        name: 'Bob',
        id: 5,
        isStudent: true,
        role: 'student',
        isAdmin: false,
      });
    });
  });
});
