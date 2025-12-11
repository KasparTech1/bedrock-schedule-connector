import { Inbox, Search, FileQuestion, Database, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type EmptyStateType = "no-data" | "no-results" | "not-found" | "empty-table";

interface EmptyStateProps {
  /** Type of empty state */
  type?: EmptyStateType;
  /** Title text */
  title?: string;
  /** Description text */
  description?: string;
  /** Action button text */
  actionText?: string;
  /** Action callback */
  onAction?: () => void;
  /** Custom icon */
  icon?: React.ReactNode;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
}

const defaultContent: Record<EmptyStateType, { icon: typeof Inbox; title: string; description: string }> = {
  "no-data": {
    icon: Database,
    title: "No data available",
    description: "There's no data to display at the moment.",
  },
  "no-results": {
    icon: Search,
    title: "No results found",
    description: "Try adjusting your search or filter criteria.",
  },
  "not-found": {
    icon: FileQuestion,
    title: "Not found",
    description: "The item you're looking for doesn't exist.",
  },
  "empty-table": {
    icon: Inbox,
    title: "No records",
    description: "There are no records to display.",
  },
};

/**
 * Empty state component for when there's no data to display.
 *
 * @example
 * ```tsx
 * // Basic usage
 * {data.length === 0 && <EmptyState type="no-results" />}
 *
 * // With action
 * <EmptyState
 *   type="no-data"
 *   actionText="Add New Item"
 *   onAction={() => setShowModal(true)}
 * />
 *
 * // Custom content
 * <EmptyState
 *   title="No customers found"
 *   description="Try a different search term"
 *   icon={<Users className="h-12 w-12" />}
 * />
 * ```
 */
export function EmptyState({
  type = "no-data",
  title,
  description,
  actionText,
  onAction,
  icon,
  size = "md",
  className,
}: EmptyStateProps) {
  const defaults = defaultContent[type];
  const Icon = defaults.icon;

  const displayTitle = title || defaults.title;
  const displayDescription = description || defaults.description;

  const iconSize = size === "sm" ? "h-10 w-10" : size === "lg" ? "h-16 w-16" : "h-12 w-12";
  const containerPadding = size === "sm" ? "p-4" : size === "lg" ? "p-12" : "p-8";

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        containerPadding,
        size === "lg" && "min-h-[400px]",
        className
      )}
    >
      <div className="rounded-full bg-muted p-4 mb-4">
        {icon || <Icon className={cn("text-muted-foreground", iconSize)} />}
      </div>

      <h3 className="font-medium text-foreground mb-1">{displayTitle}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-4">{displayDescription}</p>

      {actionText && onAction && (
        <Button onClick={onAction} size="sm">
          <Plus className="h-4 w-4 mr-2" />
          {actionText}
        </Button>
      )}
    </div>
  );
}

/**
 * Search empty state for filtered/searched lists.
 */
export function SearchEmptyState({
  searchTerm,
  onClear,
  className,
}: {
  searchTerm: string;
  onClear?: () => void;
  className?: string;
}) {
  return (
    <EmptyState
      type="no-results"
      title={`No results for "${searchTerm}"`}
      description="Try a different search term or adjust your filters."
      actionText={onClear ? "Clear Search" : undefined}
      onAction={onClear}
      className={className}
    />
  );
}

export default EmptyState;

