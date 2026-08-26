import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExportSubmissions from '../../../../pages/reviewGrades/ExportSubmissions';
import { exportSubmissions } from '../../../../services/submission';
import { message } from 'antd';

jest.mock('../../../../services/submission', () => ({
  exportSubmissions: jest.fn(),
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

describe('<ExportSubmissions />', () => {
  const onCancel = jest.fn();

  const renderModal = (open) =>
    render(
      <ExportSubmissions open={open} onCancel={onCancel} assignmentId='assgn1' />
    );

  afterEach(() => {
    onCancel.mockReset();
    exportSubmissions.mockReset();
    message.error.mockClear();
    window.URL.createObjectURL.mockClear();
    window.URL.revokeObjectURL.mockClear();
  });

  it('does not render when open=false', () => {
    renderModal(false);
    expect(screen.queryByText('Export Submissions')).toBeNull();
  });

  it('renders header, body text, and buttons when open=true', () => {
    renderModal(true);

    expect(screen.getByText('Export Submissions')).toBeInTheDocument();
    expect(
      screen.getByText(/Export every student's active submission/i)
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

  it('does not request an export before assignmentId is available', () => {
    render(
      <ExportSubmissions open={true} onCancel={onCancel} assignmentId={undefined} />
    );

    fireEvent.click(screen.getByRole('button', { name: /download submissions/i }));

    expect(exportSubmissions).not.toHaveBeenCalled();
    expect(message.error).toHaveBeenCalledWith('Assignment is still loading.');
  });

  it('downloads the zip using the filename from Content-Disposition', async () => {
    exportSubmissions.mockResolvedValue({
      data: new Blob(['zip-bytes']),
      headers: { 'content-disposition': 'attachment; filename="HW1_submissions.zip"' },
    });
    let capturedDownloadName;
    const clickSpy = jest
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function () {
        capturedDownloadName = this.download;
      });

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download submissions/i }));

    await waitFor(() =>
      expect(exportSubmissions).toHaveBeenCalledWith({ assignment_id: 'assgn1' })
    );
    expect(clickSpy).toHaveBeenCalled();
    expect(capturedDownloadName).toBe('HW1_submissions.zip');
    expect(window.URL.createObjectURL).toHaveBeenCalled();
    expect(window.URL.revokeObjectURL).toHaveBeenCalled();

    clickSpy.mockRestore();
  });

  it('falls back to a default filename when Content-Disposition is missing', async () => {
    exportSubmissions.mockResolvedValue({ data: new Blob(['zip-bytes']), headers: {} });
    let capturedDownloadName;
    const clickSpy = jest
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function () {
        capturedDownloadName = this.download;
      });

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download submissions/i }));

    await waitFor(() => expect(clickSpy).toHaveBeenCalled());
    expect(capturedDownloadName).toBe('submissions.zip');

    clickSpy.mockRestore();
  });

  it('reads the download filename from a canonical Content-Disposition header', async () => {
    exportSubmissions.mockResolvedValue({
      data: new Blob(['zip-bytes']),
      headers: { 'Content-Disposition': "attachment; filename*=UTF-8''HW%201_submissions.zip" },
    });
    let capturedDownloadName;
    const clickSpy = jest
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function () {
        capturedDownloadName = this.download;
      });

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download submissions/i }));

    await waitFor(() => expect(clickSpy).toHaveBeenCalled());
    expect(capturedDownloadName).toBe('HW 1_submissions.zip');

    clickSpy.mockRestore();
  });

  it('shows the backend error message when the export fails', async () => {
    const errorBlob = new Blob([JSON.stringify({ message: 'No active submissions found for this assignment' })]);
    exportSubmissions.mockRejectedValue({ response: { data: errorBlob } });

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download submissions/i }));

    await waitFor(() =>
      expect(message.error).toHaveBeenCalledWith(
        'No active submissions found for this assignment'
      )
    );
  });

  it('shows a generic error toast on a network failure with no response', async () => {
    exportSubmissions.mockRejectedValue(new Error('Network Error'));

    renderModal(true);
    fireEvent.click(screen.getByRole('button', { name: /download submissions/i }));

    await waitFor(() =>
      expect(message.error).toHaveBeenCalledWith('Failed to export submissions.')
    );
  });
});
