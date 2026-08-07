import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { message } from 'antd';
import GradeStatistics from '../../../../pages/reviewGrades/GradeStatistics';
import { getGradeStatistics } from '../../../../services/submission';

jest.mock('../../../../services/submission', () => ({
  getGradeStatistics: jest.fn(),
}));

jest.spyOn(message, 'error').mockImplementation(() => {});

beforeAll(() => {
  if (!window.matchMedia) {
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
});

const FULL_STATS = {
  count: 2,
  mean: 20,
  median: 20,
  min: 20,
  max: 20,
  stdev: 0,
  max_points: 20,
  mode: 'percentage',
  histogram: [
    { label: '0-10%', bucket_start: 0, bucket_end: 2, count: 0 },
    { label: '90-100%', bucket_start: 18, bucket_end: 20, count: 2 },
  ],
};

const RAW_MODE_STATS = {
  count: 2,
  mean: 15,
  median: 15,
  min: 10,
  max: 20,
  stdev: 5,
  max_points: null,
  mode: 'raw',
  histogram: [
    { label: '10.0-20.0', bucket_start: 10, bucket_end: 20, count: 2 },
  ],
};

const EMPTY_STATS = {
  count: 0,
  mean: null,
  median: null,
  min: null,
  max: null,
  stdev: null,
  max_points: 100,
  mode: 'percentage',
  histogram: [],
};

describe('<GradeStatistics />', () => {
  const onCancel = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('does not render content when open=false', () => {
    render(<GradeStatistics open={false} onCancel={onCancel} assignmentId='assgn1' />);
    expect(screen.queryByText('Statistics')).toBeNull();
    expect(getGradeStatistics).not.toHaveBeenCalled();
  });

  it('fetches statistics with the assignment id when opened', async () => {
    getGradeStatistics.mockResolvedValue({ data: FULL_STATS });
    render(<GradeStatistics open={true} onCancel={onCancel} assignmentId='assgn1' />);

    await waitFor(() => {
      expect(getGradeStatistics).toHaveBeenCalledWith({ assignment_id: 'assgn1' });
    });
  });

  it('renders summary stats as percentage + raw fraction once loaded', async () => {
    getGradeStatistics.mockResolvedValue({ data: FULL_STATS });
    const { baseElement } = render(
      <GradeStatistics open={true} onCancel={onCancel} assignmentId='assgn1' />
    );

    await screen.findByText('Mean');
    // The Modal renders into a document.body portal, so assert against
    // baseElement's full text rather than an exact node match.
    expect(baseElement.textContent).toContain('100% (20/20)');
  });

  it('falls back to plain values in raw mode (no reliable max points)', async () => {
    getGradeStatistics.mockResolvedValue({ data: RAW_MODE_STATS });
    const { baseElement } = render(
      <GradeStatistics open={true} onCancel={onCancel} assignmentId='assgn1' />
    );

    await screen.findByText('Mean');
    expect(baseElement.textContent).toContain('15');
    expect(baseElement.textContent).toContain('10');
    expect(baseElement.textContent).toContain('20');
    expect(baseElement.textContent).not.toContain('%');
  });

  it('shows an empty state when there are no graded submissions', async () => {
    getGradeStatistics.mockResolvedValue({ data: EMPTY_STATS });
    render(<GradeStatistics open={true} onCancel={onCancel} assignmentId='assgn1' />);

    expect(await screen.findByText('No graded submissions yet.')).toBeInTheDocument();
    expect(screen.queryByText('Mean')).toBeNull();
  });

  it('shows an error message when the request fails', async () => {
    getGradeStatistics.mockRejectedValue(new Error('network error'));
    render(<GradeStatistics open={true} onCancel={onCancel} assignmentId='assgn1' />);

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('Failed to load statistics.');
    });
  });

  it('calls onCancel when Close is clicked', async () => {
    getGradeStatistics.mockResolvedValue({ data: FULL_STATS });
    render(<GradeStatistics open={true} onCancel={onCancel} assignmentId='assgn1' />);

    await screen.findByText('Mean');
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
