import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EmptyState, SearchEmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('renders with default type', () => {
    render(<EmptyState />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
    expect(screen.getByText("There's no data to display at the moment.")).toBeInTheDocument();
  });

  it('renders no-results type', () => {
    render(<EmptyState type="no-results" />);
    expect(screen.getByText('No results found')).toBeInTheDocument();
  });

  it('renders not-found type', () => {
    render(<EmptyState type="not-found" />);
    expect(screen.getByText('Not found')).toBeInTheDocument();
  });

  it('renders empty-table type', () => {
    render(<EmptyState type="empty-table" />);
    expect(screen.getByText('No records')).toBeInTheDocument();
  });

  it('renders custom title and description', () => {
    render(
      <EmptyState
        title="Custom Title"
        description="Custom description text"
      />
    );
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
    expect(screen.getByText('Custom description text')).toBeInTheDocument();
  });

  it('shows action button when actionText and onAction provided', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        actionText="Add Item"
        onAction={onAction}
      />
    );
    
    const button = screen.getByRole('button', { name: /add item/i });
    expect(button).toBeInTheDocument();
  });

  it('calls onAction when button is clicked', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        actionText="Add Item"
        onAction={onAction}
      />
    );
    
    fireEvent.click(screen.getByRole('button', { name: /add item/i }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('does not show button when actionText is missing', () => {
    render(<EmptyState onAction={() => {}} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('does not show button when onAction is missing', () => {
    render(<EmptyState actionText="Add Item" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('applies different sizes', () => {
    const { container, rerender } = render(<EmptyState size="sm" />);
    expect(container.firstChild).toHaveClass('p-4');
    
    rerender(<EmptyState size="lg" />);
    expect(container.firstChild).toHaveClass('p-12', 'min-h-[400px]');
  });
});

describe('SearchEmptyState', () => {
  it('renders with search term', () => {
    render(<SearchEmptyState searchTerm="test query" />);
    expect(screen.getByText('No results for "test query"')).toBeInTheDocument();
  });

  it('shows clear button when onClear provided', () => {
    const onClear = vi.fn();
    render(<SearchEmptyState searchTerm="test" onClear={onClear} />);
    
    const button = screen.getByRole('button', { name: /clear search/i });
    expect(button).toBeInTheDocument();
  });

  it('calls onClear when clear button is clicked', () => {
    const onClear = vi.fn();
    render(<SearchEmptyState searchTerm="test" onClear={onClear} />);
    
    fireEvent.click(screen.getByRole('button', { name: /clear search/i }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
