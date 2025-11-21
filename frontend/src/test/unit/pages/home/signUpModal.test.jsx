import React from 'react';
import {
  render,
  screen,
  fireEvent,
  waitFor
} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GlobalContext } from '../../../../App';
import SignUpModal from '../../../../pages/home/signUpModal';

jest.mock('react-router-dom', () => {
  const real = jest.requireActual('react-router-dom');
  return { ...real, useNavigate: () => jest.fn() };
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
  Form.Item = ({ label, name, initialValue, children }) =>
    name ? (
      <label>
        {label && <span>{label}</span>}
        {React.cloneElement(children, {
          name,
          defaultChecked: initialValue === children.props.value
        })}
      </label>
    ) : (
      <div>{children}</div>
    );

  const Input = props => <input {...props} />;
  Input.Password = props => <input type="password" {...props} />;

  const Button = ({ htmlType, children }) => (
    <button type={htmlType || 'button'}>{children}</button>
  );

  const Radio = {
    Group: ({ children }) => <div role="radiogroup">{children}</div>,
    Button: ({ value, children }) => (
      <label>
        <input type="radio" name="role" value={value} />
        {children}
      </label>
    )
  };

  const Collapse = ({ children }) => <div>{children}</div>;
  Collapse.Panel = ({ children }) => <div>{children}</div>;

  return {
    __esModule: true,
    ...real,
    Modal,
    Form,
    Input,
    Button,
    Radio,
    Collapse
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

jest.mock('../../../../services/user', () => ({ createUser: jest.fn() }));
import { createUser } from '../../../../services/user';

describe('<SignUpModal />', () => {
  const mockUpdate = jest.fn();
  const Wrapped = props => (
    <GlobalContext.Provider value={{ updateUserInfo: mockUpdate }}>
      <SignUpModal {...props} />
    </GlobalContext.Provider>
  );

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('does not render when open=false, and shows form when open=true', () => {
    const { rerender } = render(<Wrapped open={false} onCancel={() => {}} />);
    expect(screen.queryByTestId('modal')).toBeNull();

    rerender(<Wrapped open={true} onCancel={() => {}} />);
    expect(screen.getByTestId('modal')).toBeInTheDocument();

    expect(screen.getAllByRole('radio')).toHaveLength(2);

    expect(screen.getByLabelText(/EID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();

    expect(
      screen.getByRole('button', { name: /sign up/i })
    ).toBeInTheDocument();
  });

  it('calls onCancel when the close button is clicked', () => {
    const mockCancel = jest.fn();
    render(<Wrapped open={true} onCancel={mockCancel} />);
    fireEvent.click(screen.getByTestId('close'));
    expect(mockCancel).toHaveBeenCalledTimes(1);
  });

  it('submits form (selecting student), calls createUser, updates context, and writes localStorage', async () => {
    const fakeRes = { data: { name: 'Alice', id: 7, role: 'student' } };
    createUser.mockResolvedValueOnce(fakeRes);

    render(<Wrapped open={true} onCancel={() => {}} />);

    await userEvent.click(screen.getByRole('radio', { name: /student/i }));

    await userEvent.type(screen.getByLabelText(/EID/i), 'E123');
    await userEvent.type(screen.getByLabelText(/Name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/Email/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/Password/i), 'securepass');

    fireEvent.click(screen.getByRole('button', { name: /sign up/i }));

    await waitFor(() => {
      expect(createUser).toHaveBeenCalledWith({
        role: 'student',
        eid: 'E123',
        name: 'Alice',
        email_address: 'alice@example.com',
        password: 'securepass'
      });
      expect(mockUpdate).toHaveBeenCalledWith({
        name: 'Alice',
        id: 7,
        isStudent: true,
        role: 'student', 
        isAdmin: false,
      });
      expect(JSON.parse(localStorage.getItem('userInfo'))).toEqual({
        name: 'Alice',
        id: 7,
        isStudent: true,
        role: 'student',
        isAdmin: false,
      });
    });
  });
});
