import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  ExternalLink,
  Loader2,
  RefreshCw,
  Server,
  Shield,
  XCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type HealthStatus = "healthy" | "warning" | "error";

interface GlobalShopHealthResponse {
  status: HealthStatus;
  response_time_ms?: number;
  message?: string;
  bridge_url: string;
}

interface ProductLineResponse {
  product_lines: Record<string, unknown>[];
  summary: Record<string, unknown>;
}

interface GlobalShopQueryResponse {
  data: Record<string, unknown>[];
  summary: Record<string, unknown>;
}

export function LegacyConnectors() {
  const [health, setHealth] = useState<GlobalShopHealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [productLine, setProductLine] = useState("");
  const [salesperson, setSalesperson] = useState("");
  const [limit, setLimit] = useState("500");

  const [productLinesLoading, setProductLinesLoading] = useState(false);
  const [productLines, setProductLines] = useState<ProductLineResponse | null>(null);
  const [productLinesError, setProductLinesError] = useState<string | null>(null);

  const [salespersonsLoading, setSalespersonsLoading] = useState(false);
  const [salespersons, setSalespersons] = useState<GlobalShopQueryResponse | null>(null);
  const [salespersonsError, setSalespersonsError] = useState<string | null>(null);

  const checkHealth = async () => {
    setHealthLoading(true);
    setHealthError(null);

    try {
      const res = await fetch("/api/legacy/global-shop/health");
      const data = (await res.json()) as GlobalShopHealthResponse;
      if (!res.ok) throw new Error(data?.message || "Health check failed");
      setHealth(data);
    } catch (e) {
      setHealth(null);
      setHealthError(e instanceof Error ? e.message : "Health check failed");
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const fetchProductLines = async () => {
    setProductLinesLoading(true);
    setProductLinesError(null);

    try {
      const params = new URLSearchParams();
      if (productLine.trim()) params.set("product_line", productLine.trim());
      params.set("limit", limit);

      const res = await fetch(`/api/legacy/global-shop/product-lines?${params.toString()}`);
      const data = (await res.json()) as ProductLineResponse;
      if (!res.ok) throw new Error((data as any)?.detail || "Product line query failed");

      setProductLines(data);
    } catch (e) {
      setProductLines(null);
      setProductLinesError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setProductLinesLoading(false);
    }
  };

  const fetchSalespersons = async () => {
    setSalespersonsLoading(true);
    setSalespersonsError(null);

    try {
      const params = new URLSearchParams();
      if (salesperson.trim()) params.set("salesperson", salesperson.trim());
      params.set("limit", limit);

      const res = await fetch(`/api/legacy/global-shop/salespersons?${params.toString()}`);
      const data = (await res.json()) as GlobalShopQueryResponse;
      if (!res.ok) throw new Error((data as any)?.detail || "Salesperson query failed");

      setSalespersons(data);
    } catch (e) {
      setSalespersons(null);
      setSalespersonsError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setSalespersonsLoading(false);
    }
  };

  const status = health?.status;
  const statusBadge = (() => {
    if (!status) return <Badge variant="secondary">Unknown</Badge>;
    if (status === "healthy") return <Badge className="bg-green-100 text-green-800 border-green-200">Healthy</Badge>;
    if (status === "warning") return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Warning</Badge>;
    return <Badge className="bg-red-100 text-red-800 border-red-200">Error</Badge>;
  })();

  const statusIcon = (() => {
    if (!status) return <Activity className="h-5 w-5 text-muted-foreground" />;
    if (status === "healthy") return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    if (status === "warning") return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    return <XCircle className="h-5 w-5 text-red-500" />;
  })();

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold">Legacy Systems</h1>
            <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Transitional
            </Badge>
          </div>
          <p className="text-muted-foreground mt-2">
            Isolated connectors for legacy systems during ERP migration. These are sunset-bound and intentionally
            separated from the main connector catalog.
          </p>
        </div>
      </div>

      {/* Legacy Global Shop */}
      <Card className="border-l-4 border-l-amber-500">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-amber-100 rounded-lg">
                <Database className="h-6 w-6 text-amber-600" />
              </div>
              <div>
                <CardTitle className="text-xl">Legacy Global Shop</CardTitle>
                <CardDescription>Circle Brands • Pervasive SQL via Bridge API</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {statusIcon}
              {statusBadge}
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <Tabs defaultValue="overview" className="w-full">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="health">Health & Metrics</TabsTrigger>
              <TabsTrigger value="architecture">Architecture</TabsTrigger>
              <TabsTrigger value="try">Try It</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">Migration Timeline</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">6-10 months</div>
                    <p className="text-xs text-muted-foreground">Target: SyteLine 10</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">Subsidiary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">Circle Brands</div>
                    <p className="text-xs text-muted-foreground">Legacy ERP system</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">Database Type</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">Pervasive SQL</div>
                    <p className="text-xs text-muted-foreground">Accessed via secure bridge</p>
                  </CardContent>
                </Card>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Isolation Policy</h3>
                <ul className="list-disc list-inside text-sm text-muted-foreground mt-2 space-y-1">
                  <li>Temporary solution during migration (sunset-bound)</li>
                  <li>Bespoke architecture with on-prem bridge requirements</li>
                  <li>Different patterns than SyteLine 10 connector stack</li>
                </ul>
              </div>
            </TabsContent>

            <TabsContent value="health" className="space-y-4 mt-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Connection Health</h3>
                <Button variant="outline" size="sm" onClick={checkHealth} disabled={healthLoading}>
                  {healthLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Refresh
                </Button>
              </div>

              {healthError && (
                <div className="p-3 rounded-lg text-sm bg-red-50 text-red-700">{healthError}</div>
              )}

              {health && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Activity className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Status</span>
                      </div>
                      <div className="mt-2 flex items-center gap-2">
                        {statusIcon}
                        <span className="font-semibold capitalize">{health.status}</span>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Response Time</span>
                      </div>
                      <div className="mt-2">
                        <span className="text-2xl font-bold">
                          {health.response_time_ms ? `${health.response_time_ms}ms` : "--"}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Server className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Bridge Endpoint</span>
                      </div>
                      <div className="mt-2">
                        <span className="text-xs font-mono text-muted-foreground">{health.bridge_url}</span>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Auth</span>
                      </div>
                      <div className="mt-2">
                        <span className="text-sm font-semibold">Via server env</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {health?.message && (
                <div className="p-3 rounded-lg text-sm bg-slate-50 text-slate-700">{health.message}</div>
              )}

              <Separator />

              <div>
                <h4 className="font-medium mb-2">Health Thresholds</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    <span>Healthy: &lt; 2s response</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <span>Warning: 2-5s response</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-red-500" />
                    <span>Error: &gt; 5s or timeout</span>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="architecture" className="space-y-4 mt-4">
              <Card>
                <CardContent className="pt-4 space-y-4">
                  <div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wide">Endpoint</div>
                    <code className="text-sm font-mono">POST https://bridge-api.kaiville.io/query</code>
                  </div>
                  <Separator />
                  <div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wide">Bridge Auth</div>
                    <div className="mt-1 space-y-1 font-mono text-sm">
                      <div>Content-Type: application/json</div>
                      <div>X-API-Key: [PERVASIVE_API_KEY]</div>
                    </div>
                  </div>
                  <Separator />
                  <div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wide">Documentation</div>
                    <Button variant="link" className="p-0 h-auto" asChild>
                      <a href="/docs/LEGACY_ERP_CONNECTORS.md" target="_blank" rel="noreferrer">
                        View Legacy Connector Docs
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="try" className="space-y-4 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="pl">Product Line</Label>
                  <Input
                    id="pl"
                    placeholder="e.g., ELEC"
                    value={productLine}
                    onChange={(e) => setProductLine(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">Optional exact filter</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sp">Salesperson</Label>
                  <Input
                    id="sp"
                    placeholder="e.g., SP001"
                    value={salesperson}
                    onChange={(e) => setSalesperson(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">Optional exact filter</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="limit">Limit</Label>
                  <Input
                    id="limit"
                    type="number"
                    min="1"
                    max="1000"
                    value={limit}
                    onChange={(e) => setLimit(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">1-1000</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button onClick={fetchProductLines} disabled={productLinesLoading}>
                  {productLinesLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Loading product lines...
                    </>
                  ) : (
                    "Get Product Lines"
                  )}
                </Button>

                <Button onClick={fetchSalespersons} disabled={salespersonsLoading} variant="outline">
                  {salespersonsLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Loading salespersons...
                    </>
                  ) : (
                    "Get Salespersons"
                  )}
                </Button>
              </div>

              {productLinesError && (
                <Card className="border-destructive">
                  <CardHeader>
                    <CardTitle className="text-destructive">Product Line Error</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{productLinesError}</p>
                  </CardContent>
                </Card>
              )}

              {productLines && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>Product Lines</CardTitle>
                      <Badge variant="secondary">{productLines.product_lines.length} rows</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ResultTable rows={productLines.product_lines} />
                  </CardContent>
                </Card>
              )}

              {salespersonsError && (
                <Card className="border-destructive">
                  <CardHeader>
                    <CardTitle className="text-destructive">Salesperson Error</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{salespersonsError}</p>
                  </CardContent>
                </Card>
              )}

              {salespersons && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>Salespersons</CardTitle>
                      <Badge variant="secondary">{salespersons.data.length} rows</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ResultTable rows={salespersons.data} />
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Legacy SyteLine 8 (placeholder) */}
      <Card className="border-l-4 border-l-slate-300">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-100 rounded-lg">
                <Database className="h-6 w-6 text-slate-600" />
              </div>
              <div>
                <CardTitle className="text-xl">Legacy SyteLine 8</CardTitle>
                <CardDescription>On-prem • Direct SQL via pyodbc (planned)</CardDescription>
              </div>
            </div>
            <Badge variant="secondary">Coming soon</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            This adapter will support on-prem SyteLine 8 environments where direct database access is still
            available. It will be exposed through the same connector layer (normalized outputs) once implemented.
          </p>
        </CardContent>
      </Card>

      {/* Sunset Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <h4 className="font-semibold text-amber-800">Sunset Plan</h4>
              <p className="text-sm text-amber-700 mt-1">
                Legacy systems are transitional. As migrations complete, these connectors will be deprecated,
                moved to read-only, and then removed.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ResultTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) {
    return <p className="text-sm text-muted-foreground">No rows returned.</p>;
  }

  const columns = Object.keys(rows[0]).slice(0, 10);

  return (
    <div className="overflow-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            {columns.map((col) => (
              <th key={col} className="text-left p-2 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 50).map((row, i) => (
            <tr key={i} className="border-b hover:bg-muted/50">
              {columns.map((col) => (
                <td key={col} className="p-2 font-mono text-xs">
                  {String(row[col] ?? "").trim() || "-"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 50 && (
        <p className="text-xs text-muted-foreground mt-2">Showing 50 of {rows.length} rows.</p>
      )}
    </div>
  );
}
