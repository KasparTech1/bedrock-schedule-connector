import { Link } from "wouter";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Copy, Trash2, Loader2, Eye, EyeOff, Circle, Construction } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ConnectorSummary } from "@/lib/api";

// Helper to determine if connector is "live"
const isLiveConnector = (connector: ConnectorSummary) => {
  return connector.category === "Demo" || connector.tags?.includes("live");
};

export function Connectors() {
  const queryClient = useQueryClient();

  // Fetch all connectors (including drafts)
  const { data: connectors = [], isLoading, error } = useQuery({
    queryKey: ["connectors", "all"],
    queryFn: () => api.connectors.list(false),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.connectors.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connectors"] });
    },
  });

  // Publish/Unpublish mutations
  const publishMutation = useMutation({
    mutationFn: (id: string) => api.connectors.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connectors"] });
    },
  });

  const unpublishMutation = useMutation({
    mutationFn: (id: string) => api.connectors.unpublish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connectors"] });
    },
  });

  const handleDelete = (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const handleTogglePublish = (connector: ConnectorSummary) => {
    if (connector.status === "published") {
      unpublishMutation.mutate(connector.id);
    } else {
      publishMutation.mutate(connector.id);
    }
  };

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Connectors</h1>
          <p className="text-muted-foreground mt-1">
            Manage your ERP connector configurations
          </p>
        </div>
        <Link href="/admin/connectors/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Connector
          </Button>
        </Link>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading...</span>
        </div>
      )}

      {/* Connectors Table */}
      {!isLoading && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">
              All Connectors ({connectors.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {connectors.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No connectors yet. Create your first one!
              </div>
            ) : (
              <div className="relative w-full overflow-auto">
                <table className="w-full caption-bottom text-sm">
                  <thead className="[&_tr]:border-b">
                    <tr className="border-b transition-colors">
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                        Name
                      </th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                        Category
                      </th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                        Version
                      </th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                        Tools
                      </th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                        Status
                      </th>
                      <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="[&_tr:last-child]:border-0">
                    {/* Sort: LIVE/Demo connectors first */}
                    {[...connectors]
                      .sort((a, b) => {
                        const aIsLive = isLiveConnector(a);
                        const bIsLive = isLiveConnector(b);
                        if (aIsLive && !bIsLive) return -1;
                        if (!aIsLive && bIsLive) return 1;
                        return a.name.localeCompare(b.name);
                      })
                      .map((connector) => {
                        const isLive = isLiveConnector(connector);
                        return (
                          <tr
                            key={connector.id}
                            className={`border-b transition-colors hover:bg-muted/50 ${
                              isLive ? "bg-green-50/50" : ""
                            }`}
                          >
                            <td className="p-4 align-middle font-medium">
                              <Link
                                href={`/connector/${connector.id}`}
                                className="hover:underline text-primary"
                              >
                                {connector.name}
                              </Link>
                            </td>
                            <td className="p-4 align-middle">
                              <Badge variant="secondary">{connector.category}</Badge>
                            </td>
                            <td className="p-4 align-middle text-muted-foreground">
                              v{connector.version}
                            </td>
                            <td className="p-4 align-middle text-muted-foreground">
                              {connector.tools_count}
                            </td>
                            <td className="p-4 align-middle">
                              {isLive ? (
                                <Badge className="bg-green-500 hover:bg-green-600">
                                  <Circle className="w-2 h-2 mr-1 fill-current animate-pulse" />
                                  LIVE
                                </Badge>
                              ) : (
                                <Badge className="bg-amber-500 hover:bg-amber-600">
                                  <Construction className="w-3 h-3 mr-1" />
                                  In Progress
                                </Badge>
                              )}
                            </td>
                            <td className="p-4 align-middle text-right">
                              <div className="flex items-center justify-end gap-1">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  title={
                                    connector.status === "published"
                                      ? "Unpublish"
                                      : "Publish"
                                  }
                                  onClick={() => handleTogglePublish(connector)}
                                >
                                  {connector.status === "published" ? (
                                    <EyeOff className="w-4 h-4" />
                                  ) : (
                                    <Eye className="w-4 h-4" />
                                  )}
                                </Button>
                                <Link href={`/admin/connectors/${connector.id}/edit`}>
                                  <Button variant="ghost" size="icon" title="Edit">
                                    <Pencil className="w-4 h-4" />
                                  </Button>
                                </Link>
                                <Button variant="ghost" size="icon" title="Duplicate">
                                  <Copy className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  title="Delete"
                                  className="text-destructive hover:text-destructive"
                                  onClick={() =>
                                    handleDelete(connector.id, connector.name)
                                  }
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
