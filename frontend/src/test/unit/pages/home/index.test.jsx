import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
  const real = jest.requireActual('react-router-dom');
  return { ...real, useNavigate: () => mockNavigate };
});

jest.mock('antd', () => {
  const real = jest.requireActual('antd');
  return {
    __esModule: true,
    ...real,
    Button: props => <button {...props}>{props.children}</button>,
  };
});

const mockSignUpModal = jest.fn();
jest.mock(
  '../../../../pages/home/signUpModal',
  () => ({ __esModule: true, default: props => {
    mockSignUpModal(props);
    return null;
  }})
);

const mockLogInModal = jest.fn();
jest.mock(
  '../../../../pages/home/logInModal',
  () => ({ __esModule: true, default: props => {
    mockLogInModal(props);
    return null;
  }})
);

import Home from '../../../../pages/home';
import { GlobalContext } from '../../../../App';

describe('<Home />', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('toggles SignUpModal open prop when Sign Up clicked', async () => {
    render(
      <GlobalContext.Provider value={{ userInfo: {} }}>
        <Home />
      </GlobalContext.Provider>
    );

    expect(mockSignUpModal).toHaveBeenCalledTimes(1);
    expect(mockSignUpModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ open: false })
    );

    await userEvent.click(screen.getByRole('button', { name: /sign up/i }));

    await waitFor(() => {
      expect(mockSignUpModal).toHaveBeenCalledTimes(2);
      expect(mockSignUpModal).toHaveBeenLastCalledWith(
        expect.objectContaining({ open: true })
      );
    });
  });

  test('toggles LogInModal open prop when Log In clicked', async () => {
    render(
      <GlobalContext.Provider value={{ userInfo: {} }}>
        <Home />
      </GlobalContext.Provider>
    );

    expect(mockLogInModal).toHaveBeenCalledTimes(1);
    expect(mockLogInModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ open: false })
    );

    await userEvent.click(screen.getByRole('button', { name: /log in/i }));

    await waitFor(() => {
      expect(mockLogInModal).toHaveBeenCalledTimes(2);
      expect(mockLogInModal).toHaveBeenLastCalledWith(
        expect.objectContaining({ open: true })
      );
    });
  });

  test('navigates to /dashboard when userInfo.name is set', () => {
    render(
      <GlobalContext.Provider value={{ userInfo: { name: 'Alice' } }}>
        <Home />
      </GlobalContext.Provider>
    );
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });
});
