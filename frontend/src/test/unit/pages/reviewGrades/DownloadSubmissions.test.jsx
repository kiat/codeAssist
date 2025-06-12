import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import DownloadSubmissionsModal from '../../../../pages/reviewGrades/DownloadSubmissions';

beforeAll(() => {
  if (!window.matchMedia) {
    window.matchMedia = () => ({
      matches: false,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    });
  }
});

describe('<DownloadSubmissionsModal />', () => {
  const onCancel = jest.fn();

  const renderModal = (open) =>
    render(<DownloadSubmissionsModal open={open} onCancel={onCancel} />);

  afterEach(() => {
    onCancel.mockReset();
  });

  it('does not render when open=false', () => {
    renderModal(false);
    expect(screen.queryByText('Export Submissions')).toBeNull();
  });

  it('renders header, body text, and buttons when open=true', () => {
    renderModal(true);

    expect(screen.getByText('Export Submissions')).toBeInTheDocument();

    expect(
      screen.getByText(
        /We're exporting your submissions now; this may take a few minutes\./i
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(/You can check back here in a bit to download the file\./i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/We'll also email you a link when it's ready\./i)
    ).toBeInTheDocument();

    expect(
      screen.getByRole('button', { name: /download submissions/i })
    ).toBeInTheDocument();

    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('calls onCancel when Close is clicked', () => {
    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
