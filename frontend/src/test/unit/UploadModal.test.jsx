import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import UploadModal from '../../components/UploadModal';
import { GlobalContext } from '../../App';
import { uploadSubmission } from '../../services/submission';
import { message } from 'antd';
import { useNavigate } from 'react-router-dom';

jest.mock('react-router-dom', () => ({
  useNavigate: jest.fn(),
}));

jest.mock('../../services/submission', () => ({
  uploadSubmission: jest.fn(),
}));

jest.spyOn(message, 'error').mockImplementation(() => {});
jest.spyOn(message, 'success').mockImplementation(() => {});

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

describe('<UploadModal />', () => {
  const fakeNavigate = jest.fn();
  useNavigate.mockReturnValue(fakeNavigate);

  const defaultProps = {
    open: true,
    title: 'Test Upload',
    onCancel: jest.fn(),
    afterUpdate: jest.fn(),
    url: '/upload',
    data: {},
    assignmentID: 123,
    assignmentTitle: 'Assignment X',
    extra: jest.fn(),
  };

  const renderWithContext = (ui) => {
    const contextValue = { userInfo: { id: 1 } };
    return render(
      <GlobalContext.Provider value={contextValue}>
        {ui}
      </GlobalContext.Provider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows error message when submitting without a file', async () => {
    renderWithContext(<UploadModal {...defaultProps} />);
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitBtn);
    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('No file uploaded');
    });
  });

  // Additional tests (file upload, successful submission) can be added here.
});
