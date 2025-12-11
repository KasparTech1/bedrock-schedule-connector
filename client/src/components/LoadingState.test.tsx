import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { LoadingState, LoadingSkeleton, LoadingCard, LoadingTable } from './LoadingState';

describe('LoadingState', () => {
  it('renders with default state', () => {
    render(<LoadingState />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<LoadingState message="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });

  it('has correct aria-label', () => {
    render(<LoadingState message="Fetching schedule" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Fetching schedule');
  });

  it('applies fullHeight class when specified', () => {
    render(<LoadingState fullHeight />);
    const container = screen.getByRole('status');
    expect(container.className).toContain('min-h-[400px]');
  });

  it('renders different sizes', () => {
    const { rerender } = render(<LoadingState size="sm" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    
    rerender(<LoadingState size="lg" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});

describe('LoadingSkeleton', () => {
  it('renders with custom className', () => {
    render(<LoadingSkeleton className="h-10 w-full" />);
    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('h-10', 'w-full');
  });

  it('has aria-hidden attribute', () => {
    render(<LoadingSkeleton />);
    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toHaveAttribute('aria-hidden', 'true');
  });
});

describe('LoadingCard', () => {
  it('renders skeleton elements', () => {
    render(<LoadingCard />);
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});

describe('LoadingTable', () => {
  it('renders correct number of rows', () => {
    render(<LoadingTable rows={3} />);
    const rows = document.querySelectorAll('.border-b');
    // Header + 3 rows = 4 border-b elements
    expect(rows.length).toBe(4);
  });

  it('uses default of 5 rows', () => {
    render(<LoadingTable />);
    const rows = document.querySelectorAll('.border-b');
    // Header + 5 rows = 6 border-b elements
    expect(rows.length).toBe(6);
  });
});
