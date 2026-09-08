import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExportEvaluations from '../../../../pages/reviewGrades/ExportEvaluations';
import { exportEvaluations } from '../../../../services/submission';
import { message } from 'antd';

jest.mock('../../../../services/submission', () => ({
  exportEvaluations: jest.fn(),
}));

jest.spyOn(message, 'error').mockImplementation(() => {});

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
  window.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
  window.URL.revokeObjectURL = jest.fn();
});

describe('<ExportEvaluations />', () => {
  const onCancel = jest.fn();

  const renderModal = (open) =>
    render(
      <ExportEvaluations open={open} onCancel={onCancel} assignmentId='assgn1' />
    );

  afterEach(() => {
    onCancel.mockReset();
    exportEvaluations.mockReset();
    message.error.mockClear();
  });

  it('does not render when open=false', () => {
    renderModal(false);
    expect(screen.queryByText('Export Evaluations')).toBeNull();
  });

  it('renders header, body text, and buttons when open=true', () => {
    renderModal(true);

    expect(screen.getByText('Export Evaluations')).toBeInTheDocument();
    expect(
      screen.getByText(/Export one spreadsheet per test case/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /download evaluations/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('calls onCancel when Close is clicked', () => {
    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('downloads the zip using the filename from Content-Disposition', async () => {
    exportEvaluations.mockResolvedValue({
      data: new Blob(['zip-bytes']),
      headers: { 'content-disposition': 'attachment; filename="HW1_evaluations.zip"' },
    });
    let capturedDownloadName;
    const clickSpy = jest
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function () {
        capturedDownloadName = this.download;
      });

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download evaluations/i }));

    await waitFor(() =>
      expect(exportEvaluations).toHaveBeenCalledWith({ assignment_id: 'assgn1' })
    );
    expect(clickSpy).toHaveBeenCalled();
    expect(capturedDownloadName).toBe('HW1_evaluations.zip');
    expect(window.URL.createObjectURL).toHaveBeenCalled();
    expect(window.URL.revokeObjectURL).toHaveBeenCalled();

    clickSpy.mockRestore();
  });

  it('falls back to a default filename when Content-Disposition is missing', async () => {
    exportEvaluations.mockResolvedValue({ data: new Blob(['zip-bytes']), headers: {} });
    let capturedDownloadName;
    const clickSpy = jest
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function () {
        capturedDownloadName = this.download;
      });

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download evaluations/i }));

    await waitFor(() => expect(clickSpy).toHaveBeenCalled());
    expect(capturedDownloadName).toBe('evaluations.zip');

    clickSpy.mockRestore();
  });

  it('shows the backend error message when the export fails', async () => {
    const errorBlob = new Blob([JSON.stringify({ message: 'No test cases found for this assignment' })]);
    exportEvaluations.mockRejectedValue({ response: { data: errorBlob } });

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download evaluations/i }));

    await waitFor(() =>
      expect(message.error).toHaveBeenCalledWith(
        'No test cases found for this assignment'
      )
    );
  });

  it('shows a generic error toast on a network failure with no response', async () => {
    exportEvaluations.mockRejectedValue(new Error('Network Error'));

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download evaluations/i }));

    await waitFor(() =>
      expect(message.error).toHaveBeenCalledWith('Failed to export evaluations.')
    );
  });
});
