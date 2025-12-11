import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  ArrowLeft,
  Play,
  Loader2,
  Database,
  Zap,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

interface DemoHealthResponse {
  status: string;
  base_url: string;
  config_name: string;
}

interface DemoItemsResponse {
  source: string;
  base_url: string;
  ido: string;
  records: Record<string, string | null>[];
  count: number;
}

export function DemoTryIt() {
  const [itemFilter, setItemFilter] = useState("");
  const [productCode, setProductCode] = useState("");
  const [limit, setLimit] = useState("10");

  // Health check query
  const healthQuery = useQuery<DemoHealthResponse>({
    queryKey: ["demo-health"],
    queryFn: async () => {
      const res = await fetch("/api/demo/health");
      if (!res.ok) throw new Error("Health check failed");
      return res.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Items query mutation (manual trigger)
  const itemsMutation = useMutation<DemoItemsResponse, Error>({
    mutationFn: async () => {
      const params = new URLSearchParams();
      if (itemFilter) params.set("item", itemFilter);
      if (productCode) params.set("product_code", productCode);
      params.set("limit", limit);
      
      const res = await fetch(`/api/demo/items?${params}`);
      if (!res.ok) throw new Error("Query failed");
      return res.json();
    },
  });

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div>
        <Link href="/connector/demo-syteline-items">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Connector Details
          </Button>
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-primary/10">
            <Zap className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Try DEMO - SyteLine Items</h1>
            <p className="text-muted-foreground">
              Live connection to Kaspar Development Workshop test environment
            </p>
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5" />
              Connection Status
            </CardTitle>
            {healthQuery.isLoading ? (
              <Badge variant="secondary">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                Checking...
              </Badge>
            ) : healthQuery.data?.status === "healthy" ? (
              <Badge className="bg-green-500 hover:bg-green-600">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge variant="destructive">
                <XCircle className="w-3 h-3 mr-1" />
                Disconnected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {healthQuery.data && (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Base URL:</span>
                <p className="font-mono text-xs mt-1">{healthQuery.data.base_url}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Config:</span>
                <p className="font-mono text-xs mt-1">{healthQuery.data.config_name}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Query Builder */}
      <Card>
        <CardHeader>
          <CardTitle>Query SLItems</CardTitle>
          <CardDescription>
            Filter and retrieve items from the live SyteLine 10 environment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="item">Item Filter</Label>
              <Input
                id="item"
                placeholder="e.g., 30"
                value={itemFilter}
                onChange={(e) => setItemFilter(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Partial match on item number</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="productCode">Product Code</Label>
              <Input
                id="productCode"
                placeholder="e.g., FG-100"
                value={productCode}
                onChange={(e) => setProductCode(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Exact match on product code</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="limit">Limit</Label>
              <Input
                id="limit"
                type="number"
                min="1"
                max="100"
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Max records (1-100)</p>
            </div>
          </div>

          <Button
            onClick={() => itemsMutation.mutate()}
            disabled={itemsMutation.isPending || healthQuery.data?.status !== "healthy"}
            className="w-full"
          >
            {itemsMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Querying Live SyteLine...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Execute Query
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {itemsMutation.data && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Results</CardTitle>
              <Badge variant="secondary">{itemsMutation.data.count} records</Badge>
            </div>
            <CardDescription>
              Data from {itemsMutation.data.ido} IDO
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-medium">Item</th>
                    <th className="text-left p-2 font-medium">Description</th>
                    <th className="text-left p-2 font-medium">Product Code</th>
                    <th className="text-left p-2 font-medium">UM</th>
                    <th className="text-left p-2 font-medium">Status</th>
                    <th className="text-left p-2 font-medium">Color 1</th>
                    <th className="text-left p-2 font-medium">Color 2</th>
                    <th className="text-left p-2 font-medium">Color 3</th>
                  </tr>
                </thead>
                <tbody>
                  {itemsMutation.data.records.map((record, i) => (
                    <tr key={i} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-mono">{record.Item || "-"}</td>
                      <td className="p-2">{record.Description || "-"}</td>
                      <td className="p-2">
                        {record.ProductCode && (
                          <Badge variant="outline">{record.ProductCode}</Badge>
                        )}
                      </td>
                      <td className="p-2">{record.UM || "-"}</td>
                      <td className="p-2">
                        {record.Stat === "A" ? (
                          <Badge className="bg-green-500">Active</Badge>
                        ) : (
                          <Badge variant="secondary">{record.Stat || "-"}</Badge>
                        )}
                      </td>
                      <td className="p-2">
                        {record.itmUf_colorcode01 && (
                          <Badge variant="outline">{record.itmUf_colorcode01}</Badge>
                        )}
                      </td>
                      <td className="p-2">
                        {record.itmUf_colorCode02 && (
                          <Badge variant="outline">{record.itmUf_colorCode02}</Badge>
                        )}
                      </td>
                      <td className="p-2">
                        {record.itmUf_ColorCode03 && (
                          <Badge variant="outline">{record.itmUf_ColorCode03}</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {itemsMutation.data.records.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No records found matching your filters
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {itemsMutation.error && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{itemsMutation.error.message}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
