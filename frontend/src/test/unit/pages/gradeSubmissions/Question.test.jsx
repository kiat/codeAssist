import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

jest.mock('react-router-dom', () => {
  const real = jest.requireActual('react-router-dom');
  return { ...real, useNavigate: () => jest.fn() };
});

jest.mock('../../../../App', () => {
  const React = require('react');
  const mockUpdate = jest.fn();
  const mockInfo = { id: 123, studentName: '' };
  return {
    GlobalContext: React.createContext({
      assignmentInfo: mockInfo,
      updateAssignmentInfo: mockUpdate,
    }),
  };
});

jest.mock('antd', () => {
  const real  = jest.requireActual('antd');
  const React = require('react');

  const Typography = {
    Link: ({ onClick, children }) => (
      <a href="#" onClick={e => { e.preventDefault(); onClick(); }}>
        {children}
      </a>
    ),
  };

  const Table = ({ columns, dataSource }) => (
      <table>
        <tbody>
          {dataSource.map((r, rowIdx) => (
            <tr key={r.id} role="row">
              {columns.map((c, colIdx) => (
                <td key={c.dataIndex ?? colIdx}>
                  {c.render ? c.render(r[c.dataIndex], r, rowIdx) : r[c.dataIndex]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
  );

  const PageHeader = ({ title, extra }) => (
    <header>
      <div>{title}</div>
      {extra}
    </header>
  );
  const Card   = ({ children }) => <div>{children}</div>;
  const Button = ({ children }) => <button>{children}</button>;
  const Input  = { Search: ({ enterButton, ...props}) => <input {...props} /> };

  return {
    __esModule: true,
    ...real,
    Typography,
    Table,
    PageHeader,
    Card,
    Button,
    Input,
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

jest.mock('@ant-design/icons', () => ({
  CheckOutlined: () => <span>✔</span>,
  LeftOutlined:  () => <span>←</span>,
  RightOutlined: () => <span>→</span>,
}));

import Question from '../../../../pages/gradeSubmissions/Question';
import { formattingData } from '../../../../pages/gradeSubmissions/mock';

describe('<Question />', () => {
  test('renders header, back-link, table rows, and updateAssignmentInfo', () => {
    render(<Question changePage={jest.fn()} />);

    expect(screen.getByText('Question 2: formatting')).toBeInTheDocument();

    expect(screen.getByText('←')).toBeInTheDocument();

    expect(screen.getAllByRole('row')).toHaveLength(formattingData.length);

    const user = formattingData[0].user;
    const link = screen.getByText(user);
    fireEvent.click(link);

    const { updateAssignmentInfo } = require('../../../../App').GlobalContext._currentValue;
    expect(updateAssignmentInfo).toHaveBeenCalledWith({
      ...require('../../../../App').GlobalContext._currentValue.assignmentInfo,
      studentName: user,
    });
  });
});
