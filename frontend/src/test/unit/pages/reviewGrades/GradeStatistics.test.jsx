import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import GradeStatistics, { formatAxisTick, formatStatValue } from '../../../../pages/reviewGrades/GradeStatistics';

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

describe('formatAxisTick', () => {
  it('shows the percentage-converted right boundary for a normal bucket', () => {
    expect(formatAxisTick({ label: '80-90%', bucket_start: 16, bucket_end: 18 }, 'percentage', 20)).toBe('90%');
  });

  it('shows the raw right boundary in raw mode without a % suffix', () => {
    expect(formatAxisTick({ label: '10.0-20.0', bucket_start: 10, bucket_end: 20 }, 'raw', null)).toBe('20');
  });

  it('preserves the sign on a negative raw-mode boundary', () => {
    expect(formatAxisTick({ label: '-10.0--8.0', bucket_start: -10, bucket_end: -8 }, 'raw', null)).toBe('-8');
  });

  it('falls back to the label for edge buckets with no numeric boundary', () => {
    expect(formatAxisTick({ label: '<0%', bucket_start: null, bucket_end: 0 }, 'percentage', 20)).toBe('<0%');
    expect(formatAxisTick({ label: '>100%', bucket_start: 20, bucket_end: null }, 'percentage', 20)).toBe('>100%');
  });
});

describe('formatStatValue', () => {
  it('shows percentage + raw fraction in percentage mode', () => {
    expect(formatStatValue(20, 'percentage', 20)).toBe('100% (20/20)');
  });

  it('shows the raw value in raw mode', () => {
    expect(formatStatValue(15, 'raw', null)).toBe(15);
  });

  it('shows a dash for a null value', () => {
    expect(formatStatValue(null, 'percentage', 20)).toBe('-');
  });
});

describe('<GradeStatistics />', () => {
  const onCancel = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('does not render content when open=false', () => {
    render(<GradeStatistics open={false} onCancel={onCancel} stats={null} loading={false} error={false} />);
    expect(screen.queryByText('Statistics')).toBeNull();
  });

  it('shows a loading spinner while loading', () => {
    // The Modal renders into a document.body portal, not inside `container`.
    const { baseElement } = render(
      <GradeStatistics open={true} onCancel={onCancel} stats={null} loading={true} error={false} />
    );
    expect(baseElement.querySelector('.ant-spin')).toBeInTheDocument();
  });

  it('shows an error state on failure', () => {
    render(<GradeStatistics open={true} onCancel={onCancel} stats={null} loading={false} error={true} />);
    expect(screen.getByText('Failed to load statistics.')).toBeInTheDocument();
  });

  it('renders summary stats as percentage + raw fraction once loaded', () => {
    const { baseElement } = render(
      <GradeStatistics open={true} onCancel={onCancel} stats={FULL_STATS} loading={false} error={false} />
    );
    // The Modal renders into a document.body portal, so assert against
    // baseElement's full text rather than an exact node match.
    expect(baseElement.textContent).toContain('100% (20/20)');
  });

  it('falls back to plain values in raw mode (no reliable max points)', () => {
    const { baseElement } = render(
      <GradeStatistics open={true} onCancel={onCancel} stats={RAW_MODE_STATS} loading={false} error={false} />
    );
    expect(baseElement.textContent).toContain('15');
    expect(baseElement.textContent).toContain('10');
    expect(baseElement.textContent).toContain('20');
    expect(baseElement.textContent).not.toContain('%');
  });

  it('shows an empty state when there are no graded submissions', () => {
    render(<GradeStatistics open={true} onCancel={onCancel} stats={EMPTY_STATS} loading={false} error={false} />);
    expect(screen.getByText('No graded submissions yet.')).toBeInTheDocument();
    expect(screen.queryByText('Mean')).toBeNull();
  });

  it('calls onCancel when Close is clicked', () => {
    render(<GradeStatistics open={true} onCancel={onCancel} stats={FULL_STATS} loading={false} error={false} />);
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
