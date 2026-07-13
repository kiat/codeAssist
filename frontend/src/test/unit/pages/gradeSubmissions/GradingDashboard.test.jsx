
import { render, screen } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';

jest.mock('react-router-dom', () => {
  const real = jest.requireActual('react-router-dom');
  return { ...real, useNavigate: () => jest.fn() };
});

jest.mock('antd', () => {
  const real  = jest.requireActual('antd');
  const React = require('react');

  const Typography = {
    Link: ({ children }) => <span role="link">{children}</span>,
  };
  const Progress = ({ percent }) => <span>{percent}%</span>;
  const Table = ({ columns, dataSource }) => (
    <table>
      <tbody>
        {dataSource.map(row => (
          <tr key={row.id} role="row">
            {columns.map(col => (
              <td key={col.dataIndex}>
                {col.render ? col.render(row[col.dataIndex], row) : row[col.dataIndex]}
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

import GradingDashboard from '../../../../pages/gradeSubmissions';
import { gradingData }  from '../../../../pages/gradeSubmissions/mock';

describe('<GradingDashboard />', () => {
  it('renders header and correct number of rows', () => {
    render(
      <MemoryRouter>
        <GradingDashboard changePage={() => {}} />
      </MemoryRouter>
    );

    // Page title
    expect(
      screen.getByRole('heading', { name: /grading dashboard/i })
    ).toBeInTheDocument();

    // One <tr role="row"> per gradingData item
    expect(screen.getAllByRole('row')).toHaveLength(gradingData.length);
  });
});
