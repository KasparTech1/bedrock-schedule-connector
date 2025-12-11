import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  ArrowLeft,
  Package,
  Loader2,
  CheckCircle2,
  XCircle,
  Play,
  Activity,
  Download,
  Clock,
  AlertTriangle,
  FileText,
  Search,
  TrendingUp,
  AlertCircle,
  Database,
  Cpu,
  Timer,
  Layers,
  Code,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api, OrderAvailabilityLine, OrderAvailabilitySummary, ConnectorAnatomyResponse } from "@/lib/api";

// Coverage badge component
function CoverageBadge({ percentage, isFullyCovered }: { percentage: number; isFullyCovered: boolean }) {
  if (isFullyCovered) {
    return <Badge className="bg-green-500 hover:bg-green-600">100% Covered</Badge>;
  } else if (percentage >= 75) {
    return <Badge className="bg-yellow-500 hover:bg-yellow-600 text-black">{percentage.toFixed(0)}% Covered</Badge>;
  } else if (percentage >= 50) {
    return <Badge className="bg-orange-500 hover:bg-orange-600">{percentage.toFixed(0)}% Covered</Badge>;
  } else if (percentage > 0) {
    return <Badge className="bg-red-500 hover:bg-red-600">{percentage.toFixed(0)}% Covered</Badge>;
  } else {
    return <Badge variant="destructive">No Coverage</Badge>;
  }
}

// Summary stat card
function StatCard({ 
  title, 
  value, 
  icon: Icon, 
  color,
  subtitle,
}: { 
  title: string; 
  value: number | string; 
  icon: React.ElementType; 
  color: string;
  subtitle?: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
          </div>
          <div className={`p-3 rounded-lg ${color}`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Allocation source card
function AllocationCard({ 
  title, 
  total,
  allocated, 
  color 
}: { 
  title: string; 
  total: number;
  allocated: number;
  color: string;
}) {
  return (
    <div className={`p-4 rounded-lg ${color} text-center`}>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{title}</p>
      <p className="text-2xl font-bold mt-1">{allocated}</p>
      {total !== allocated && (
        <p className="text-xs text-muted-foreground">of {total} available</p>
      )}
    </div>
  );
}

// Export to CSV
function exportToCSV(orderLines: OrderAvailabilityLine[]) {
  const headers = [
    "CO_Num", "CO_Line", "CustomerName", "DueDate", "Item", "ItemDescription",
    "QtyOrdered", "QtyShipped", "QtyRemaining", "QtyCovered", "Shortage",
    "CoveragePercent", "QtyOnHand", "AllocFromPaint", "AllocFromBlast", 
    "AllocFromWeldFab", "Jobs", "ReleasedDate", "WeldFabCompletionDate",
    "BlastCompletionDate", "PaintCompletionDate", "LineAmount"
  ];
  
  const rows = orderLines.map(ol => [
    ol.co_num,
    ol.co_line,
    `"${(ol.customer_name || "").replace(/"/g, '""')}"`,
    ol.due_date || "",
    ol.item,
    `"${(ol.item_description || "").replace(/"/g, '""')}"`,
    ol.qty_ordered,
    ol.qty_shipped,
    ol.qty_remaining,
    ol.qty_remaining_covered,
    ol.shortage,
    ol.coverage_percentage,
    ol.qty_on_hand,
    ol.allocated_from_paint,
    ol.allocated_from_blast,
    ol.allocated_from_released_weld_fab,
    `"${(ol.jobs || "").replace(/"/g, '""')}"`,
    ol.released_date || "",
    ol.weld_fab_completion_date || "",
    ol.blast_completion_date || "",
    ol.paint_assembly_completion_date || "",
    ol.line_amount.toFixed(2),
  ]);
  
  const csv = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
  
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `bedrock-order-availability-${new Date().toISOString().split("T")[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// Anatomy view component
function AnatomyView({ data }: { data: ConnectorAnatomyResponse["data"] | undefined }) {
  if (!data) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-muted-foreground" />
        <p className="mt-2 text-muted-foreground">Loading anatomy...</p>
      </div>
    );
  }

  const { connector, metrics } = data;

  return (
    <div className="space-y-6">
      {/* Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="w-5 h-5" />
            Connector Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold mb-2">{connector.name}</h4>
            <p className="text-sm text-muted-foreground whitespace-pre-line">
              {connector.description.trim()}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Run Statistics */}
      {metrics.total_runs > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Run Statistics ({metrics.total_runs} runs)
            </CardTitle>
            <CardDescription>
              {metrics.successful_runs} successful, {metrics.failed_runs} failed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 mb-4">
              {metrics.timing && (
                <>
                  <div className="p-3 bg-muted rounded-lg text-center">
                    <p className="text-xs text-muted-foreground">Avg Total Time</p>
                    <p className="text-xl font-bold">{(metrics.timing.avg_total_ms / 1000).toFixed(1)}s</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg text-center">
                    <p className="text-xs text-muted-foreground">Avg API Time</p>
                    <p className="text-xl font-bold">{(metrics.timing.avg_api_ms / 1000).toFixed(1)}s</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg text-center">
                    <p className="text-xs text-muted-foreground">Min Time</p>
                    <p className="text-xl font-bold">{(metrics.timing.min_total_ms / 1000).toFixed(1)}s</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg text-center">
                    <p className="text-xs text-muted-foreground">Max Time</p>
                    <p className="text-xl font-bold">{(metrics.timing.max_total_ms / 1000).toFixed(1)}s</p>
                  </div>
                </>
              )}
            </div>
            {metrics.records && (
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-muted rounded-lg text-center">
                  <p className="text-xs text-muted-foreground">Avg Output Records</p>
                  <p className="text-xl font-bold">{metrics.records.avg_output.toFixed(0)}</p>
                </div>
                <div className="p-3 bg-muted rounded-lg text-center">
                  <p className="text-xs text-muted-foreground">Avg API Calls</p>
                  <p className="text-xl font-bold">{metrics.records.avg_api_calls.toFixed(0)}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Last Run Details */}
      {metrics.last_run && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Timer className="w-5 h-5" />
              Last Run Details
            </CardTitle>
            <CardDescription>
              Run ID: {metrics.last_run.run_id} • {new Date(metrics.last_run.started_at).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-3 mb-4">
              <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-center">
                <p className="text-xs text-muted-foreground">API Calls</p>
                <p className="text-lg font-bold">{metrics.last_run.summary.total_api_calls}</p>
              </div>
              <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded text-center">
                <p className="text-xs text-muted-foreground">Records Fetched</p>
                <p className="text-lg font-bold">{metrics.last_run.summary.total_records_fetched}</p>
              </div>
              <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded text-center">
                <p className="text-xs text-muted-foreground">Output Records</p>
                <p className="text-lg font-bold">{metrics.last_run.summary.output_records}</p>
              </div>
              <div className="p-2 bg-amber-50 dark:bg-amber-900/20 rounded text-center">
                <p className="text-xs text-muted-foreground">Total Time</p>
                <p className="text-lg font-bold">{(metrics.last_run.summary.total_time_ms / 1000).toFixed(1)}s</p>
              </div>
            </div>
            
            {/* IDO Call Details */}
            <div className="mt-4">
              <h4 className="font-semibold text-sm mb-2">IDO API Calls</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">IDO Name</th>
                      <th className="text-right p-2">Props</th>
                      <th className="text-right p-2">Record Cap</th>
                      <th className="text-right p-2">Records</th>
                      <th className="text-right p-2">Duration</th>
                      <th className="text-center p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.last_run.ido_calls.map((call, i) => (
                      <tr key={i} className="border-b">
                        <td className="p-2 font-mono">{call.ido_name}</td>
                        <td className="p-2 text-right">{call.properties_count}</td>
                        <td className="p-2 text-right">{call.record_cap}</td>
                        <td className="p-2 text-right font-medium">{call.records_returned}</td>
                        <td className="p-2 text-right">{call.duration_ms.toFixed(0)}ms</td>
                        <td className="p-2 text-center">
                          {call.success ? (
                            <Badge variant="outline" className="text-green-600">OK</Badge>
                          ) : (
                            <Badge variant="destructive">Error</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Sources */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Data Sources ({connector.data_sources.total_ido_count} IDOs)
          </CardTitle>
          <CardDescription>
            All IDOs are fetched in parallel (max 5 concurrent)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {connector.data_sources.idos.map((ido, i) => (
              <div key={i} className="p-3 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <code className="font-mono font-semibold">{ido.name}</code>
                    <p className="text-xs text-muted-foreground">{ido.description}</p>
                  </div>
                  <Badge variant="outline">cap: {ido.record_cap}</Badge>
                </div>
                <div className="flex flex-wrap gap-1 mb-2">
                  {ido.properties.map((prop, j) => (
                    <code key={j} className="text-xs px-1.5 py-0.5 bg-muted rounded">
                      {prop}
                    </code>
                  ))}
                </div>
                {ido.filter && (
                  <p className="text-xs">
                    <span className="text-muted-foreground">Filter: </span>
                    <code className="text-orange-600">{ido.filter}</code>
                  </p>
                )}
                {metrics.ido_stats?.[ido.name] && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Avg: {metrics.ido_stats[ido.name].avg_records.toFixed(0)} records in {metrics.ido_stats[ido.name].avg_duration_ms.toFixed(0)}ms
                  </p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Processing Logic */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="w-5 h-5" />
            Processing Logic
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold text-sm mb-2">Join Strategy</h4>
            <pre className="text-xs bg-muted p-3 rounded whitespace-pre-wrap">
              {connector.processing.join_description}
            </pre>
          </div>
          <div>
            <h4 className="font-semibold text-sm mb-2">Processing Steps</h4>
            <ol className="text-xs space-y-1 list-none">
              {connector.processing.steps.map((step, i) => (
                <li key={i} className={`p-2 rounded ${step.startsWith("   ") ? "ml-4 bg-muted/50" : "bg-muted"}`}>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        </CardContent>
      </Card>

      {/* Allocation Logic */}
      {connector.allocation_logic && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5" />
              Allocation Algorithm
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {connector.allocation_logic.map((line, i) => (
                <p key={i} className={`text-sm ${line.startsWith("Priority") ? "font-medium" : "text-muted-foreground"}`}>
                  {line || <br />}
                </p>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Calendar Config */}
      {connector.calendar_config && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Business Day Calendar
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Business Days</p>
                <p className="font-medium">{connector.calendar_config.business_days}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Friday</p>
                <p className="font-medium">{connector.calendar_config.friday}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Weekend</p>
                <p className="font-medium">{connector.calendar_config.weekend}</p>
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Completion Estimates</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(connector.calendar_config.completion_estimates).map(([key, value]) => (
                  <Badge key={key} variant="outline">
                    {key}: {value}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">2025 Holidays</p>
              <div className="flex flex-wrap gap-1">
                {connector.calendar_config.holidays_2025.map((holiday, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {holiday}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export function BedrockOrderAvailability() {
  // Tab state
  const [activeTab, setActiveTab] = useState("data");
  
  // Filter state
  const [searchFilter, setSearchFilter] = useState("");
  const [coverageFilter, setCoverageFilter] = useState("all");
  const [customerFilter, setCustomerFilter] = useState("");
  const [itemFilter, setItemFilter] = useState("");
  const [shortageOnly, setShortageOnly] = useState(false);

  // Health check
  const healthQuery = useQuery({
    queryKey: ["bedrock-health"],
    queryFn: () => api.bedrock.health(),
    refetchInterval: 30000,
  });

  // Anatomy query
  const anatomyQuery = useQuery({
    queryKey: ["order-availability-anatomy"],
    queryFn: () => api.bedrock.orderAvailabilityAnatomy(),
    enabled: activeTab === "anatomy",
  });

  // Order availability query (manual trigger)
  const availabilityMutation = useMutation({
    mutationFn: async () => {
      const data = await api.bedrock.orderAvailability({
        customer: customerFilter || undefined,
        item: itemFilter || undefined,
        shortage_only: shortageOnly,
        limit: 500,
      });
      return data;
    },
  });

  const data = availabilityMutation.data?.data;
  const summary = data?.summary;

  // Apply client-side filters
  let filteredOrders = data?.order_lines || [];
  
  if (searchFilter) {
    const search = searchFilter.toLowerCase();
    filteredOrders = filteredOrders.filter(ol => 
      ol.co_num.toLowerCase().includes(search) ||
      ol.customer_name.toLowerCase().includes(search) ||
      ol.item.toLowerCase().includes(search) ||
      (ol.jobs?.toLowerCase().includes(search))
    );
  }
  
  if (coverageFilter && coverageFilter !== "all") {
    switch (coverageFilter) {
      case "full":
        filteredOrders = filteredOrders.filter(ol => ol.is_fully_covered);
        break;
      case "partial":
        filteredOrders = filteredOrders.filter(ol => !ol.is_fully_covered && ol.coverage_percentage > 0);
        break;
      case "none":
        filteredOrders = filteredOrders.filter(ol => ol.coverage_percentage === 0);
        break;
      case "shortage":
        filteredOrders = filteredOrders.filter(ol => ol.shortage > 0);
        break;
    }
  }

  // Calculate allocation totals for display
  const totalAllocatedOnHand = filteredOrders.reduce((sum, ol) => sum + ol.qty_on_hand, 0);
  const totalAllocatedPaint = filteredOrders.reduce((sum, ol) => sum + ol.allocated_from_paint, 0);
  const totalAllocatedBlast = filteredOrders.reduce((sum, ol) => sum + ol.allocated_from_blast, 0);
  const totalAllocatedWeldFab = filteredOrders.reduce((sum, ol) => sum + ol.allocated_from_released_weld_fab, 0);

  return (
    <div className="space-y-6 max-w-[1800px]">
      {/* Header */}
      <div>
        <Link href="/">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Library
          </Button>
        </Link>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-purple-500/10">
              <Package className="w-8 h-8 text-purple-500" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Order Availability</h1>
              <p className="text-muted-foreground">
                Customer order allocation from inventory and production stages
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {data && activeTab === "data" && (
              <Button
                onClick={() => exportToCSV(filteredOrders)}
                disabled={filteredOrders.length === 0}
              >
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="data" className="gap-2">
            <Database className="w-4 h-4" />
            Data
          </TabsTrigger>
          <TabsTrigger value="anatomy" className="gap-2">
            <Code className="w-4 h-4" />
            Anatomy
          </TabsTrigger>
        </TabsList>

        <TabsContent value="anatomy" className="mt-4">
          <AnatomyView data={anatomyQuery.data?.data} />
        </TabsContent>

        <TabsContent value="data" className="mt-4 space-y-6">

      {/* Connection Status */}
      <Card className="border-none shadow-sm bg-muted/30">
        <CardContent className="py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm">
              <span className="text-muted-foreground">Connection:</span>
              {healthQuery.isLoading ? (
                <Badge variant="secondary">
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  Checking...
                </Badge>
              ) : healthQuery.data?.connected ? (
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
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Customer filter..."
                  value={customerFilter}
                  onChange={(e) => setCustomerFilter(e.target.value)}
                  className="w-40 h-8 text-sm"
                />
                <Input
                  placeholder="Item filter..."
                  value={itemFilter}
                  onChange={(e) => setItemFilter(e.target.value)}
                  className="w-32 h-8 text-sm"
                />
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={shortageOnly}
                    onChange={(e) => setShortageOnly(e.target.checked)}
                    className="rounded"
                  />
                  Shortages Only
                </label>
              </div>
              <Button
                onClick={() => availabilityMutation.mutate()}
                disabled={availabilityMutation.isPending || !healthQuery.data?.connected}
                size="sm"
              >
                {availabilityMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Fetch Data
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {summary && (
        <>
          {/* Top-level stats */}
          <div className="grid grid-cols-5 gap-4">
            <StatCard 
              title="Total Order Lines" 
              value={summary.total_lines} 
              icon={FileText}
              color="bg-blue-500"
            />
            <StatCard 
              title="Total Qty Remaining" 
              value={summary.total_qty_remaining.toFixed(0)} 
              icon={Package}
              color="bg-purple-500"
            />
            <StatCard 
              title="Qty Covered" 
              value={summary.total_qty_covered.toFixed(0)} 
              icon={CheckCircle2}
              color="bg-green-500"
              subtitle={`${summary.coverage_percentage}% coverage`}
            />
            <StatCard 
              title="Total Shortage" 
              value={summary.total_shortage.toFixed(0)} 
              icon={AlertCircle}
              color="bg-red-500"
              subtitle={`${summary.lines_with_shortage} lines`}
            />
            <StatCard 
              title="Line Amount" 
              value={`$${(summary.total_line_amount / 1000).toFixed(0)}K`} 
              icon={TrendingUp}
              color="bg-amber-500"
            />
          </div>

          {/* Allocation by Source */}
          <div className="grid grid-cols-4 gap-4">
            <AllocationCard 
              title="On Hand" 
              total={totalAllocatedOnHand}
              allocated={totalAllocatedOnHand} 
              color="bg-green-100 dark:bg-green-900/30" 
            />
            <AllocationCard 
              title="From Paint" 
              total={totalAllocatedPaint}
              allocated={totalAllocatedPaint} 
              color="bg-blue-100 dark:bg-blue-900/30" 
            />
            <AllocationCard 
              title="From Blast" 
              total={totalAllocatedBlast}
              allocated={totalAllocatedBlast} 
              color="bg-yellow-100 dark:bg-yellow-900/30" 
            />
            <AllocationCard 
              title="From Weld/Fab" 
              total={totalAllocatedWeldFab}
              allocated={totalAllocatedWeldFab} 
              color="bg-orange-100 dark:bg-orange-900/30" 
            />
          </div>
        </>
      )}

      {/* Filters */}
      {data && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Order Lines ({filteredOrders.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search orders, customers, items, jobs..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="w-48">
                <Select value={coverageFilter} onValueChange={setCoverageFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Coverage" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Coverage</SelectItem>
                    <SelectItem value="full">Fully Covered</SelectItem>
                    <SelectItem value="partial">Partially Covered</SelectItem>
                    <SelectItem value="none">No Coverage</SelectItem>
                    <SelectItem value="shortage">Has Shortage</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Table */}
      {data && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-3 font-medium">Order #</th>
                    <th className="text-center p-3 font-medium">Line</th>
                    <th className="text-left p-3 font-medium">Due Date</th>
                    <th className="text-left p-3 font-medium">Customer</th>
                    <th className="text-left p-3 font-medium">Item</th>
                    <th className="text-right p-3 font-medium">Qty Rem</th>
                    <th className="text-right p-3 font-medium">On Hand</th>
                    <th className="text-right p-3 font-medium">Paint</th>
                    <th className="text-right p-3 font-medium">Blast</th>
                    <th className="text-right p-3 font-medium">Weld/Fab</th>
                    <th className="text-right p-3 font-medium">Covered</th>
                    <th className="text-right p-3 font-medium">Shortage</th>
                    <th className="text-left p-3 font-medium">Coverage</th>
                    <th className="text-left p-3 font-medium">Est. Completion</th>
                    <th className="text-left p-3 font-medium">Job #</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((ol, i) => (
                    <tr key={`${ol.co_num}-${ol.co_line}-${i}`} className={`border-b hover:bg-muted/50 ${ol.shortage > 0 ? 'bg-red-50 dark:bg-red-900/10' : ''}`}>
                      <td className="p-3 font-mono text-xs">{ol.co_num}</td>
                      <td className="p-3 text-center">
                        <Badge variant="outline" className="font-mono">{ol.co_line}</Badge>
                      </td>
                      <td className="p-3">
                        {ol.due_date ? (
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-muted-foreground" />
                            <span className="text-xs">{new Date(ol.due_date).toLocaleDateString()}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-xs">No date</span>
                        )}
                      </td>
                      <td className="p-3">
                        <p className="font-medium text-xs truncate max-w-[120px]" title={ol.customer_name}>
                          {ol.customer_name || "Unknown"}
                        </p>
                      </td>
                      <td className="p-3">
                        <div>
                          <p className="font-mono text-xs font-medium">{ol.item}</p>
                          {ol.model && ol.model !== ol.item && (
                            <p className="text-xs text-muted-foreground truncate max-w-[100px]">{ol.model}</p>
                          )}
                        </div>
                      </td>
                      <td className="p-3 text-right font-medium">{ol.qty_remaining}</td>
                      <td className="p-3 text-right">
                        {ol.qty_on_hand > 0 ? (
                          <span className="text-green-600 font-medium">{ol.qty_on_hand}</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        {ol.allocated_from_paint > 0 ? (
                          <span className="text-blue-600 font-medium">{ol.allocated_from_paint}</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        {ol.allocated_from_blast > 0 ? (
                          <span className="text-yellow-600 font-medium">{ol.allocated_from_blast}</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        {ol.allocated_from_released_weld_fab > 0 ? (
                          <span className="text-orange-600 font-medium">{ol.allocated_from_released_weld_fab}</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="p-3 text-right font-medium">{ol.qty_remaining_covered}</td>
                      <td className="p-3 text-right">
                        {ol.shortage > 0 ? (
                          <span className="text-red-600 font-bold">{ol.shortage}</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="p-3">
                        <CoverageBadge percentage={ol.coverage_percentage} isFullyCovered={ol.is_fully_covered} />
                      </td>
                      <td className="p-3">
                        {ol.paint_assembly_completion_date ? (
                          <div className="text-xs">
                            <span className="text-muted-foreground">Paint: </span>
                            {new Date(ol.paint_assembly_completion_date).toLocaleDateString()}
                          </div>
                        ) : ol.blast_completion_date ? (
                          <div className="text-xs">
                            <span className="text-muted-foreground">Blast: </span>
                            {new Date(ol.blast_completion_date).toLocaleDateString()}
                          </div>
                        ) : ol.is_fully_covered ? (
                          <span className="text-green-600 text-xs">Ready</span>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </td>
                      <td className="p-3">
                        {ol.jobs ? (
                          <span className="font-mono text-xs text-green-600">{ol.jobs.split(";")[0].trim()}</span>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredOrders.length === 0 && (
              <div className="text-center py-12">
                <Package className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No orders found matching your filters</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Initial state - prompt to fetch */}
      {!data && !availabilityMutation.isPending && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <Package className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold mb-2">No Data Loaded</h3>
            <p className="text-muted-foreground mb-4">
              Click "Fetch Data" to load order availability from Bedrock SyteLine
            </p>
            <Button
              onClick={() => availabilityMutation.mutate()}
              disabled={!healthQuery.data?.connected}
            >
              <Play className="w-4 h-4 mr-2" />
              Fetch Data
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {availabilityMutation.error && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Error Loading Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{(availabilityMutation.error as Error).message}</p>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card className="bg-muted/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">About Order Availability</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p className="mb-2">
            This tool emulates the <code className="bg-background px-1 rounded">TBE_Customer_Order_Availability_Add_Release_Date</code> stored procedure from Syteline 8.
          </p>
          <p className="mb-2">
            <strong>Allocation Priority:</strong> Inventory is allocated to orders in due date order from:
          </p>
          <div className="flex gap-4 mb-2">
            <span>1. On Hand → </span>
            <span>2. Paint Queue → </span>
            <span>3. Blast Queue → </span>
            <span>4. Released Weld/Fab</span>
          </div>
          <p>
            <strong>Completion Dates:</strong> WeldFab (4 days), Blast (7 days), Paint/Assembly (10 business days from release)
          </p>
        </CardContent>
      </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

