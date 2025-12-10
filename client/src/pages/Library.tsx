import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ConnectorCard } from "@/components/ConnectorCard";
import { api } from "@/lib/api";

export function Library() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  // Fetch published connectors from API
  const { data: connectors = [], isLoading, error } = useQuery({
    queryKey: ["connectors", "published"],
    queryFn: () => api.connectors.list(true),
  });

  // Get unique categories from connectors
  const categories = [
    "All",
    ...Array.from(new Set(connectors.map((c) => c.category))),
  ];

  // Filter connectors
  const filteredConnectors = connectors
    .filter((connector) => {
      const matchesSearch =
        connector.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        connector.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        connector.tags.some((tag) =>
          tag.toLowerCase().includes(searchQuery.toLowerCase())
        );
      const matchesCategory =
        selectedCategory === "All" || connector.category === selectedCategory;
      return matchesSearch && matchesCategory;
    })
    // Sort: LIVE/Demo connectors first, then alphabetically
    .sort((a, b) => {
      const aIsLive = a.category === "Demo" || a.tags?.includes("live");
      const bIsLive = b.category === "Demo" || b.tags?.includes("live");
      if (aIsLive && !bIsLive) return -1;
      if (!aIsLive && bIsLive) return 1;
      return a.name.localeCompare(b.name);
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
      <div>
        <h1 className="text-3xl font-semibold">Connector Library</h1>
        <p className="text-muted-foreground mt-1">
          Browse and explore available ERP connectors for SyteLine 10
        </p>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search connectors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map((category) => (
            <Badge
              key={category}
              variant={selectedCategory === category ? "default" : "outline"}
              className="cursor-pointer hover-elevate px-3 py-1"
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </Badge>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading connectors...</span>
        </div>
      )}

      {/* Results Count */}
      {!isLoading && (
        <div className="text-sm text-muted-foreground">
          Showing {filteredConnectors.length} connector
          {filteredConnectors.length !== 1 ? "s" : ""}
        </div>
      )}

      {/* Connector Grid */}
      {!isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredConnectors.map((connector) => (
            <ConnectorCard key={connector.id} {...connector} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredConnectors.length === 0 && connectors.length > 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No connectors found matching your search.
          </p>
        </div>
      )}

      {/* No Connectors at All */}
      {!isLoading && connectors.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No connectors available yet. Create one in the Admin section.
          </p>
        </div>
      )}
    </div>
  );
}
