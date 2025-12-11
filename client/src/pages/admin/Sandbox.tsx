import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, FlaskConical } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ConnectorCard } from "@/components/ConnectorCard";
import { api } from "@/lib/api";

export function Sandbox() {
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch all connectors from API
  const { data: allConnectors = [], isLoading, error } = useQuery({
    queryKey: ["connectors", "all"],
    queryFn: () => api.connectors.list(false), // Include unpublished
  });

  // Filter to only Demo connectors
  const demoConnectors = allConnectors.filter(
    (c) => c.category === "Demo" || c.tags?.includes("demo")
  );

  // Apply search filter
  const filteredConnectors = demoConnectors.filter((connector) => {
    const matchesSearch =
      connector.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connector.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connector.tags.some((tag) =>
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      );
    return matchesSearch;
  });

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive">
          Failed to load connectors. Is the API running?
        </p>
        <p className="text-muted-foreground text-sm mt-2">
          {error instanceof Error ? error.message : "Unknown error"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-lg bg-amber-500/10">
          <FlaskConical className="w-8 h-8 text-amber-600" />
        </div>
        <div>
          <h1 className="text-3xl font-semibold">Sandbox</h1>
          <p className="text-muted-foreground mt-1">
            Demo connectors and test environments for development and experimentation
          </p>
        </div>
      </div>

      {/* Search */}
      {demoConnectors.length > 0 && (
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search demo connectors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading demo connectors...</span>
        </div>
      )}

      {/* Results Count */}
      {!isLoading && demoConnectors.length > 0 && (
        <div className="text-sm text-muted-foreground">
          Showing {filteredConnectors.length} demo connector
          {filteredConnectors.length !== 1 ? "s" : ""}
        </div>
      )}

      {/* Connector Grid */}
      {!isLoading && filteredConnectors.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredConnectors.map((connector) => (
            <ConnectorCard key={connector.id} {...connector} />
          ))}
        </div>
      )}

      {/* Empty State - No matching search */}
      {!isLoading && filteredConnectors.length === 0 && demoConnectors.length > 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No demo connectors found matching your search.
          </p>
        </div>
      )}

      {/* Empty State - No demo connectors at all */}
      {!isLoading && demoConnectors.length === 0 && (
        <div className="text-center py-12 space-y-4">
          <FlaskConical className="w-16 h-16 mx-auto text-muted-foreground/50" />
          <div>
            <p className="text-lg font-medium">No Demo Connectors</p>
            <p className="text-muted-foreground mt-1">
              Create a connector with category "Demo" or add the "demo" tag to see it here.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
