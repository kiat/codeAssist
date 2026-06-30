import React from 'react';
import { render, screen } from '@testing-library/react';
import SubmissionHistoryModal from '../../../../pages/result/submissionHistoryModal';
import { message } from 'antd';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

jest.mock('react-router-dom', () => ({
  useNavigate: jest.fn(),
}));

jest.mock('axios');

jest.spyOn(message, 'error').mockImplementation(() => {});

if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
}

describe('<SubmissionHistoryModal />', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useNavigate.mockReturnValue(jest.fn());
    axios.get.mockResolvedValue({ data: [] });
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ message: 'No active submission' }),
    });
  });

  it('renders without crashing when no current submission is provided', async () => {
    render(
      <SubmissionHistoryModal
        open={true}
        onCancel={jest.fn()}
        studentId={1}
        assignmentId={2}
        studentName="Student"
        extra={jest.fn()}
        currSubData={undefined}
      />
    );

    expect(await screen.findByText('Submission History')).toBeInTheDocument();
  });
});
