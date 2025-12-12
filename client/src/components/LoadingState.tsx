import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  /** Optional message to display below the spinner */
  message?: string;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
  /** Whether to take full height of container */
  fullHeight?: boolean;
}

const sizeClasses = {
  sm: "h-4 w-4",
  md: "h-8 w-8",
  lg: "h-12 w-12",
};

/**
 * Loading state component with spinner and optional message.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <LoadingState />
 *
 * // With message
 * <LoadingState message="Loading production schedule..." />
 *
 * // Full height container
 * <LoadingState fullHeight message="Fetching data..." />
 * ```
 */
export function LoadingState({
  message,
  size = "md",
  className,
  fullHeight = false,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3",
        fullHeight && "min-h-[400px]",
        className
      )}
      role="status"
      aria-label={message || "Loading"}
    >
      <Loader2 className={cn("animate-spin text-muted-foreground", sizeClasses[size])} />
      {message && (
        <p className="text-sm text-muted-foreground animate-pulse">{message}</p>
      )}
    </div>
  );
}

/**
 * Skeleton loading placeholder for content.
 */
export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
      aria-hidden="true"
    />
  );
}

/**
 * Loading card skeleton for list items.
 */
export function LoadingCard() {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-4">
      <LoadingSkeleton className="h-6 w-3/4" />
      <LoadingSkeleton className="h-4 w-1/2" />
      <div className="flex gap-2">
        <LoadingSkeleton className="h-8 w-20" />
        <LoadingSkeleton className="h-8 w-20" />
      </div>
    </div>
  );
}

/**
 * Loading table skeleton.
 */
export function LoadingTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex gap-4 p-4 border-b">
        <LoadingSkeleton className="h-4 w-24" />
        <LoadingSkeleton className="h-4 w-32" />
        <LoadingSkeleton className="h-4 w-20" />
        <LoadingSkeleton className="h-4 w-28" />
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 p-4 border-b">
          <LoadingSkeleton className="h-4 w-24" />
          <LoadingSkeleton className="h-4 w-32" />
          <LoadingSkeleton className="h-4 w-20" />
          <LoadingSkeleton className="h-4 w-28" />
        </div>
      ))}
    </div>
  );
}

export default LoadingState;


