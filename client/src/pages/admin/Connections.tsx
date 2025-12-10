import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Database,
  RefreshCw,
  Trash2,
  Loader2,
  CheckCircle2,
  Table2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";

export function Connections() {
  const queryClient = useQueryClient();
  const [selectedTable, setSelectedTable] = useState<string>("");
  const [queryLimit, setQueryLimit] = useState(50);

  // Fetch test database status
  const { data: status, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ["testdb", "status"],
    queryFn: () => api.testdb.status(),
  });

  // Fetch available tables
  const { data: tables = [] } = useQuery({
    queryKey: ["testdb", "tables"],
    queryFn: () => api.testdb.tables(),
  });

  // Fetch table data when selected
  const { data: tableData, isLoading: tableLoading } = useQuery({
    queryKey: ["testdb", "table", selectedTable, queryLimit],
    queryFn: () => api.testdb.getTableData(selectedTable, queryLimit),
    enabled: !!selectedTable,
  });

  // Seed mutation
  const seedMutation = useMutation({
    mutationFn: () => api.testdb.seed(20, 15),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["testdb"] });
    },
  });

  // Clear mutation
  const clearMutation = useMutation({
    mutationFn: () => api.testdb.clear(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["testdb"] });
    },
  });

  const handleClear = () => {
    if (confirm("Are you sure you want to clear all test data?")) {
      clearMutation.mutate();
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-semibold">Connections</h1>
        <p className="text-muted-foreground mt-1">
          Manage database connections and test data
        </p>
      </div>

      {/* Test Database Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Database className="w-6 h-6" />
              </div>
              <div>
                <CardTitle>Test Database</CardTitle>
                <CardDescription>
                  SQLite-based local database for testing connectors
                </CardDescription>
              </div>
            </div>
            {status?.connected && (
              <Badge variant="success" className="gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Connected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {statusLoading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading status...
            </div>
          )}

          {statusError && (
            <div className="text-destructive">
              Failed to connect to test database. Is the API running?
            </div>
          )}

          {status && (
            <>
              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(status.tables).map(([table, count]) => (
                  <div key={table} className="p-3 border rounded-lg">
                    <div className="text-2xl font-semibold">{count}</div>
                    <div className="text-sm text-muted-foreground">{table}</div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  onClick={() => seedMutation.mutate()}
                  disabled={seedMutation.isPending}
                >
                  {seedMutation.isPending ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4 mr-2" />
                  )}
                  Seed Test Data
                </Button>
                <Button
                  variant="outline"
                  onClick={handleClear}
                  disabled={clearMutation.isPending}
                >
                  {clearMutation.isPending ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4 mr-2" />
                  )}
                  Clear All Data
                </Button>
              </div>

              {(seedMutation.isSuccess || clearMutation.isSuccess) && (
                <div className="text-sm text-green-600 dark:text-green-400">
                  {seedMutation.data?.message || clearMutation.data?.message}
                </div>
              )}

              <Separator />

              {/* Query Interface */}
              <div className="space-y-4">
                <h3 className="font-medium flex items-center gap-2">
                  <Table2 className="w-4 h-4" />
                  Browse Tables
                </h3>

                <div className="flex gap-4 items-end">
                  <div className="space-y-2 flex-1 max-w-xs">
                    <Label>Table</Label>
                    <Select value={selectedTable} onValueChange={setSelectedTable}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a table..." />
                      </SelectTrigger>
                      <SelectContent>
                        {tables.map((table) => (
                          <SelectItem key={table} value={table}>
                            {table}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2 w-24">
                    <Label>Limit</Label>
                    <Input
                      type="number"
                      value={queryLimit}
                      onChange={(e) => setQueryLimit(parseInt(e.target.value) || 50)}
                      min={1}
                      max={1000}
                    />
                  </div>
                </div>

                {/* Results */}
                {tableLoading && (
                  <div className="flex items-center gap-2 text-muted-foreground py-4">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading data...
                  </div>
                )}

                {tableData && tableData.records.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <div className="p-2 bg-muted text-sm">
                      Showing {tableData.count} records from {tableData.ido || selectedTable}
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                          <tr>
                            {Object.keys(tableData.records[0]).map((col) => (
                              <th
                                key={col}
                                className="text-left p-2 font-medium border-b"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {tableData.records.map((row, i) => (
                            <tr key={i} className="border-b last:border-0">
                              {Object.values(row).map((val, j) => (
                                <td key={j} className="p-2 font-mono text-xs">
                                  {val === null ? (
                                    <span className="text-muted-foreground">null</span>
                                  ) : (
                                    String(val)
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {tableData && tableData.records.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground border rounded-lg">
                    No data in this table. Try seeding the database.
                  </div>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* SyteLine Connection Card (placeholder) */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-muted text-muted-foreground">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <CardTitle className="text-muted-foreground">
                SyteLine 10 Connection
              </CardTitle>
              <CardDescription>
                Configure your production SyteLine ERP connection
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            Production connection configuration coming soon. For now, use the
            Test Database above to develop and test your connectors.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
