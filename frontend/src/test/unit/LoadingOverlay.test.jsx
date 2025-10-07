import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingOverlay from '../../components/LoadingOverlay';

jest.mock('antd', () => ({
  Spin: () => <div data-testid="spin" />,
}));

describe('LoadingOverlay', () => {
  it('renders the overlay and spinner when loading is true', () => {
    const { container } = render(<LoadingOverlay loading={true} />);

    const overlay = container.querySelector('.loading-overlay');
    expect(overlay).toBeInTheDocument();

    const spinner = screen.getByTestId('spin');
    expect(spinner).toBeInTheDocument();
    expect(overlay).toContainElement(spinner);
  });

  it('renders nothing when loading is false', () => {
    const { container } = render(<LoadingOverlay loading={false} />);
    expect(container.firstChild).toBeNull();
  });
});