import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PublishGradesModal from '../../../../pages/reviewGrades/PublishGradesModal';
import { publishGrades } from '../../../../services/submission';
import { message } from 'antd';

jest.mock('../../../../services/submission', () => ({
  publishGrades: jest.fn(),
}));

jest.spyOn(message, 'error').mockImplementation(() => {});
jest.spyOn(message, 'success').mockImplementation(() => {});

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

describe('<PublishGradesModal />', () => {
  const onCancel = jest.fn();
  const onSuccess = jest.fn();

  const renderModal = (props = {}) =>
    render(
      <PublishGradesModal
        open={true}
        onCancel={onCancel}
        assignmentId="assgn1"
        published={false}
        studentCount={5}
        onSuccess={onSuccess}
        {...props}
      />
    );

  afterEach(() => {
    onCancel.mockReset();
    onSuccess.mockReset();
    publishGrades.mockReset();
    message.error.mockClear();
    message.success.mockClear();
  });

  it('shows Publish copy and button when currently unpublished', () => {
    renderModal({ published: false });
    expect(screen.getByRole('dialog', { name: 'Publish Grades' })).toBeInTheDocument();
    expect(screen.getByText(/Make grades and results visible to all 5 students/)).toBeInTheDocument();
  });

  it('shows Unpublish copy and button when currently published', () => {
    renderModal({ published: true });
    expect(screen.getByRole('dialog', { name: 'Unpublish Grades' })).toBeInTheDocument();
    expect(screen.getByText(/Hide grades and results from students again/)).toBeInTheDocument();
  });

  it('calls onCancel when Close is clicked', () => {
    renderModal();
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('publishes grades and reports success', async () => {
    publishGrades.mockResolvedValue({
      data: { assignment_id: 'assgn1', grades_published: true, grades_published_at: '2026-08-25T00:00:00Z' },
    });

    renderModal({ published: false });
    fireEvent.click(screen.getByRole('button', { name: /Publish Grades/i }));

    await waitFor(() =>
      expect(publishGrades).toHaveBeenCalledWith({ assignment_id: 'assgn1', published: true })
    );
    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith({
      assignment_id: 'assgn1', grades_published: true, grades_published_at: '2026-08-25T00:00:00Z',
    }));
    expect(onCancel).toHaveBeenCalled();
    expect(message.success).toHaveBeenCalledWith('Grades published to students.');
  });

  it('unpublishes grades when currently published', async () => {
    publishGrades.mockResolvedValue({
      data: { assignment_id: 'assgn1', grades_published: false, grades_published_at: null },
    });

    renderModal({ published: true });
    fireEvent.click(screen.getByRole('button', { name: /Unpublish Grades/i }));

    await waitFor(() =>
      expect(publishGrades).toHaveBeenCalledWith({ assignment_id: 'assgn1', published: false })
    );
    expect(message.success).toHaveBeenCalledWith('Grades hidden from students.');
  });

  it('shows an error toast when the request fails', async () => {
    publishGrades.mockRejectedValue(new Error('network error'));

    renderModal({ published: false });
    fireEvent.click(screen.getByRole('button', { name: /Publish Grades/i }));

    await waitFor(() =>
      expect(message.error).toHaveBeenCalledWith('Failed to publish grades.')
    );
    expect(onSuccess).not.toHaveBeenCalled();
  });
});
