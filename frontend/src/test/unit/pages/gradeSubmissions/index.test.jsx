import { render, screen } from '@testing-library/react';
import React from 'react';

jest.mock('antd', () => {
  const React = require('react');
  const real  = jest.requireActual('antd');

  const Typography = {
    Link: ({ children }) => <span>{children}</span>,
  };
  const Progress = ({ percent }) => <span>{percent}%</span>;
  const Table = ({ columns, dataSource }) => (
    <table>
      <tbody>
        {dataSource.map(r => (
          <tr key={r.id} role="row">
            {columns.map(c => (
              <td key={c.dataIndex}>
                {c.render ? c.render(r[c.dataIndex], r) : r[c.dataIndex]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
  const PageHeader = ({ title }) => <h1>{title}</h1>;
  const Card       = ({ children }) => <div>{children}</div>;
  const Button     = ({ children }) => <button>{children}</button>;

  const Collapse = ({ children }) => <div>{children}</div>;
  Collapse.Panel = ({ children }) => <div>{children}</div>;

  return {
    __esModule: true,
    ...real,
    Typography,
    Progress,
    Table,
    PageHeader,
    Card,
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

jest.mock(
  '../../../../pages/gradeSubmissions/Question',
  () => ({ __esModule: true, default: () => <span>Question</span> })
);

import GradingDashboard from '../../../../pages/gradeSubmissions';
import { gradingData }  from '../../../../pages/gradeSubmissions/mock';

describe('<GradingDashboard />', () => {
  it('renders header, correct number of rows, and the Review Grades button', () => {
    render(<GradingDashboard changePage={() => {}} />);

    expect(
      screen.getByRole('heading', { name: /grading dashboard/i })
    ).toBeInTheDocument();

    expect(screen.getAllByRole('row')).toHaveLength(gradingData.length);

    expect(
      screen.getByRole('button', { name: /review grades/i })
    ).toBeInTheDocument();
  });
});
