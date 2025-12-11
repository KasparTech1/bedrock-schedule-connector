import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorState, InlineError } from './ErrorState';

describe('ErrorState', () => {
  it('renders with default content', () => {
    render(<ErrorState />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders with custom title and message', () => {
    render(
      <ErrorState
        title="Custom Error"
        message="This is a custom error message"
      />
    );
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
    expect(screen.getByText('This is a custom error message')).toBeInTheDocument();
  });

  it('displays error message from Error object', () => {
    const error = new Error('Database connection failed');
    render(<ErrorState error={error} />);
    expect(screen.getByText('Database connection failed')).toBeInTheDocument();
  });

  it('shows retry button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);
    
    const retryButton = screen.getByRole('button', { name: /try again/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);
    
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('does not show retry button when onRetry is not provided', () => {
    render(<ErrorState />);
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });

  it('detects network errors', () => {
    const error = new Error('Network request failed');
    render(<ErrorState error={error} />);
    expect(screen.getByText('Connection Error')).toBeInTheDocument();
  });

  it('detects authentication errors', () => {
    const error = new Error('401 Unauthorized');
    render(<ErrorState error={error} />);
    expect(screen.getByText('Authentication Required')).toBeInTheDocument();
  });

  it('detects server errors', () => {
    const error = new Error('500 Internal Server Error');
    render(<ErrorState error={error} />);
    expect(screen.getByText('Server Error')).toBeInTheDocument();
  });

  it('applies different sizes', () => {
    const { rerender } = render(<ErrorState size="sm" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    
    rerender(<ErrorState size="lg" />);
    const container = screen.getByRole('alert');
    expect(container.className).toContain('min-h-[400px]');
  });
});

describe('InlineError', () => {
  it('renders error message', () => {
    render(<InlineError message="Field is required" />);
    expect(screen.getByText('Field is required')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<InlineError message="Error" className="mt-2" />);
    const container = screen.getByText('Error').parentElement;
    expect(container).toHaveClass('mt-2');
  });
});

