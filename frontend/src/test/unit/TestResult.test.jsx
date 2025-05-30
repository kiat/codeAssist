import React from 'react';
import { render, screen } from '@testing-library/react';
import TestResult from '../../components/TestResult';

describe('<TestResult />', () => {
  it('renders the test name with the correct CSS class', () => {
    render(<TestResult colorClass="pass" testName="MyTest" />);
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toHaveClass('pass');
    expect(heading).toHaveTextContent('MyTest');
  });

  it('renders the output paragraph when testOutput is provided', () => {
    render(
      <TestResult
        colorClass="fail"
        testName="OtherTest"
        testOutput="Expected 2, got 3"
      />
    );
    const output = screen.getByText('Expected 2, got 3');
    expect(output).toBeInTheDocument();
    expect(output.tagName).toBe('P');
  });

  it('does not render a <p> when testOutput is empty or undefined', () => {
    const { container } = render(
      <TestResult colorClass="skip" testName="EmptyTest" />
    );
    expect(container.querySelector('p')).toBeNull();
  });
});
