import React from 'react';
import { render, screen } from '@testing-library/react';
import TestResults from '../../components/TestResults';

const sampleData = {
  score: 3,
  tests: [
    { name: 'TestA', score: 2, max_score: 2, output: 'All good' },
    { name: 'TestB', score: 0, max_score: 1, output: 'Failed' },
    { name: 'TestC', score: 1, max_score: 2, output: '' },
  ],
};

describe('<TestResults />', () => {
  beforeEach(() => {
    render(<TestResults data={sampleData} />);
  });

  it('displays the total score heading correctly', () => {
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toHaveTextContent('Score: 3/5');
  });

  it('renders a TestResult for each test', () => {
    expect(screen.getByText('TestA (2/2)')).toBeInTheDocument();
    expect(screen.getByText('TestB (0/1)')).toBeInTheDocument();
    expect(screen.getByText('TestC (1/2)')).toBeInTheDocument();
  });

  it('applies the correct CSS class based on score', () => {
    const passed = screen.getByText('TestA (2/2)');
    expect(passed).toHaveClass('testPassed');
    const failed = screen.getByText('TestB (0/1)');
    expect(failed).toHaveClass('testFailed');
    const partial = screen.getByText('TestC (1/2)');
    expect(partial).toHaveClass('testPartial');
  });

  it('renders output paragraphs only when output is non-empty', () => {
    const goodOutput = screen.getByText('All good');
    expect(goodOutput.tagName).toBe('P');
    const failedOutput = screen.getByText('Failed');
    expect(failedOutput.tagName).toBe('P');
    const paragraphs = screen.getAllByRole('paragraph', { hidden: true });
    expect(paragraphs).toHaveLength(2);
  });
});
