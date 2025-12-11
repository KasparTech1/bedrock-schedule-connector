import { AlertCircle, RefreshCw, WifiOff, ServerCrash, ShieldX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  /** Error title */
  title?: string;
  /** Error message */
  message?: string;
  /** Error object for detailed info */
  error?: Error | unknown;
  /** Callback for retry action */
  onRetry?: () => void;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
}

type ErrorType = "network" | "server" | "auth" | "unknown";

function getErrorType(error?: Error | unknown): ErrorType {
  if (!error) return "unknown";

  const message = error instanceof Error ? error.message : String(error);
  const lowerMessage = message.toLowerCase();

  if (lowerMessage.includes("network") || lowerMessage.includes("fetch")) {
    return "network";
  }
  if (lowerMessage.includes("401") || lowerMessage.includes("unauthorized") || lowerMessage.includes("403")) {
    return "auth";
  }
  if (lowerMessage.includes("500") || lowerMessage.includes("server")) {
    return "server";
  }

  return "unknown";
}

const errorIcons = {
  network: WifiOff,
  server: ServerCrash,
  auth: ShieldX,
  unknown: AlertCircle,
};

const errorTitles = {
  network: "Connection Error",
  server: "Server Error",
  auth: "Authentication Required",
  unknown: "Something went wrong",
};

const errorMessages = {
  network: "Unable to connect to the server. Please check your internet connection.",
  server: "The server encountered an error. Please try again later.",
  auth: "You need to be authenticated to access this resource.",
  unknown: "An unexpected error occurred. Please try again.",
};

/**
 * Error state component for displaying errors with retry option.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <ErrorState error={error} onRetry={refetch} />
 *
 * // Custom message
 * <ErrorState
 *   title="Failed to load schedule"
 *   message="Could not fetch production data"
 *   onRetry={refetch}
 * />
 * ```
 */
export function ErrorState({
  title,
  message,
  error,
  onRetry,
  size = "md",
  className,
}: ErrorStateProps) {
  const errorType = getErrorType(error);
  const Icon = errorIcons[errorType];

  const displayTitle = title || errorTitles[errorType];
  const displayMessage = message || (error instanceof Error ? error.message : errorMessages[errorType]);

  const iconSize = size === "sm" ? "h-8 w-8" : size === "lg" ? "h-16 w-16" : "h-12 w-12";
  const textSize = size === "sm" ? "text-sm" : size === "lg" ? "text-xl" : "text-base";

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 text-center p-6",
        size === "lg" && "min-h-[400px]",
        className
      )}
      role="alert"
    >
      <div className="rounded-full bg-destructive/10 p-4">
        <Icon className={cn("text-destructive", iconSize)} />
      </div>

      <div className="space-y-2">
        <h3 className={cn("font-semibold text-foreground", textSize)}>{displayTitle}</h3>
        <p className="text-muted-foreground max-w-md">{displayMessage}</p>
      </div>

      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-2">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
}

/**
 * Inline error message for form fields or small areas.
 */
export function InlineError({
  message,
  className,
}: {
  message: string;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-2 text-sm text-destructive", className)}>
      <AlertCircle className="h-4 w-4 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
}

export default ErrorState;

