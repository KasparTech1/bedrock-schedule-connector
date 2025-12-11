import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  ArrowLeft,
  Zap,
  Loader2,
  CheckCircle2,
  XCircle,
  Play,
  Package,
  Activity,
  Download,
  Clock,
  AlertTriangle,
  FileText,
  Layers,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api, OpenOrderLine, FlowOptimizerSummary } from "@/lib/api";

// Urgency badge component
function UrgencyBadge({ urgency }: { urgency: string }) {
  switch (urgency) {
    case "OVERDUE":
      return <Badge className="bg-red-500 hover:bg-red-600">Overdue</Badge>;
    case "TODAY":
      return <Badge className="bg-orange-500 hover:bg-orange-600">Today</Badge>;
    case "THIS_WEEK":
      return <Badge className="bg-yellow-500 hover:bg-yellow-600 text-black">This Week</Badge>;
    case "NEXT_WEEK":
      return <Badge className="bg-blue-500 hover:bg-blue-600">Next Week</Badge>;
    case "LATER":
      return <Badge variant="secondary">Later</Badge>;
    default:
      return <Badge variant="outline">{urgency}</Badge>;
  }
}

// Bed type badge
function BedTypeBadge({ bedType }: { bedType: string }) {
  const colors: Record<string, string> = {
    "Granite": "bg-gray-600",
    "Granite+": "bg-gray-700",
    "Diamond": "bg-blue-600",
    "Marble": "bg-purple-600",
    "Limestone": "bg-amber-600",
    "Platform": "bg-green-600",
    "Onyx": "bg-slate-800",
    "Quad": "bg-cyan-600",
    "Slate": "bg-zinc-600",
    "Other": "bg-neutral-500",
  };
  return (
    <Badge className={`${colors[bedType] || colors["Other"]} text-white`}>
      {bedType}
    </Badge>
  );
}

// Summary stat card
function StatCard({ 
  title, 
  value, 
  icon: Icon, 
  color 
}: { 
  title: string; 
  value: number | string; 
  icon: React.ElementType; 
  color: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
          </div>
          <div className={`p-3 rounded-lg ${color}`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// WIP Stage card
function WipStageCard({ 
  title, 
  value, 
  color 
}: { 
  title: string; 
  value: number; 
  color: string;
}) {
  return (
    <div className={`p-4 rounded-lg ${color} text-center`}>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

// Export to CSV matching Flow Optimizer format
function exportToCSV(orderLines: OpenOrderLine[]) {
  const headers = [
    "OrderNum", "OrderLine", "CustomerName", "OrderDate", "DueDate",
    "DaysUntilDue", "Urgency", "Item", "Model", "ItemDescription",
    "BedType", "BedLength", "QtyOrdered", "QtyShipped", "QtyRemaining",
    "Item_OnHand", "Item_AtWeld", "Item_AtBlast", "Item_AtPaint", "Item_AtAssy",
    "Item_TotalPipeline", "JobNumbers", "QtyReleased", "ReleasedDate",
    "LineValue", "FirstForItem", "ExportTimestamp"
  ];
  
  const timestamp = new Date().toISOString();
  
  const rows = orderLines.map(ol => [
    ol.order_num,
    ol.order_line,
    `"${(ol.customer_name || "").replace(/"/g, '""')}"`,
    ol.order_date || "",
    ol.due_date || "",
    ol.days_until_due,
    ol.urgency,
    ol.item,
    ol.model || "",
    `"${(ol.item_description || "").replace(/"/g, '""')}"`,
    ol.bed_type,
    ol.bed_length,
    ol.qty_ordered,
    ol.qty_shipped,
    ol.qty_remaining,
    ol.item_on_hand,
    ol.item_at_weld,
    ol.item_at_blast,
    ol.item_at_paint,
    ol.item_at_assy,
    ol.item_total_pipeline,
    `"${ol.job_numbers.replace(/"/g, '""')}"`,
    ol.qty_released,
    ol.released_date || "",
    ol.line_value.toFixed(2),
    ol.first_for_item ? "Y" : "",
    timestamp
  ]);
  
  const csv = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
  
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `bedrock-open-orders-${new Date().toISOString().split("T")[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export function BedrockFlowOptimizer() {
  // Filter state
  const [searchFilter, setSearchFilter] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState("all");
  const [bedTypeFilter, setBedTypeFilter] = useState("all");
  const [limit, setLimit] = useState("500");

  // Health check
  const healthQuery = useQuery({
    queryKey: ["bedrock-health"],
    queryFn: () => api.bedrock.health(),
    refetchInterval: 30000,
  });

  // Open orders query (manual trigger)
  const openOrdersMutation = useMutation({
    mutationFn: async () => {
      const data = await api.bedrock.openOrders(parseInt(limit) || 500);
      return data;
    },
  });

  const data = openOrdersMutation.data?.data;
  const summary = data?.summary;

  // Apply client-side filters
  let filteredOrders = data?.order_lines || [];
  
  if (searchFilter) {
    const search = searchFilter.toLowerCase();
    filteredOrders = filteredOrders.filter(ol => 
      ol.order_num.toLowerCase().includes(search) ||
      ol.customer_name.toLowerCase().includes(search) ||
      ol.item.toLowerCase().includes(search) ||
      (ol.model?.toLowerCase().includes(search)) ||
      ol.job_numbers.toLowerCase().includes(search)
    );
  }
  
  if (urgencyFilter && urgencyFilter !== "all") {
    filteredOrders = filteredOrders.filter(ol => ol.urgency === urgencyFilter);
  }
  
  if (bedTypeFilter && bedTypeFilter !== "all") {
    filteredOrders = filteredOrders.filter(ol => ol.bed_type === bedTypeFilter);
  }

  // Get unique bed types for filter
  const bedTypes = [...new Set(data?.order_lines.map(ol => ol.bed_type) || [])].sort();

  return (
    <div className="space-y-6 max-w-[1600px]">
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
            <div className="p-3 rounded-lg bg-green-500/10">
              <Zap className="w-8 h-8 text-green-500" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Open Orders</h1>
              <p className="text-muted-foreground">
                Import and manage production orders from your ERP system
              </p>
            </div>
          </div>
          {data && (
            <Button
              onClick={() => exportToCSV(filteredOrders)}
              disabled={filteredOrders.length === 0}
            >
              <Download className="w-4 h-4 mr-2" />
              Import Orders
            </Button>
          )}
        </div>
      </div>

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
              <span className="text-muted-foreground ml-4">Config:</span>
              <code className="text-xs font-mono">DUU6QAFE74D2YDYW_TRN_TBE2</code>
            </div>
            <Button
              onClick={() => openOrdersMutation.mutate()}
              disabled={openOrdersMutation.isPending || !healthQuery.data?.connected}
              size="sm"
            >
              {openOrdersMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Fetching...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Fetch Orders
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {summary && (
        <>
          {/* Top-level stats */}
          <div className="grid grid-cols-4 gap-4">
            <StatCard 
              title="Total Open Orders" 
              value={summary.total_orders} 
              icon={FileText}
              color="bg-blue-500"
            />
            <StatCard 
              title="In Production" 
              value={summary.in_production} 
              icon={Activity}
              color="bg-green-500"
            />
            <StatCard 
              title="Ready to Schedule" 
              value={summary.ready_to_schedule} 
              icon={Layers}
              color="bg-purple-500"
            />
            <StatCard 
              title="On Hand" 
              value={summary.on_hand} 
              icon={Package}
              color="bg-amber-500"
            />
          </div>

          {/* WIP by Stage */}
          <div className="grid grid-cols-4 gap-4">
            <WipStageCard title="WELD" value={summary.weld} color="bg-orange-100 dark:bg-orange-900/30" />
            <WipStageCard title="BLAST" value={summary.blast} color="bg-yellow-100 dark:bg-yellow-900/30" />
            <WipStageCard title="PAINT" value={summary.paint} color="bg-green-100 dark:bg-green-900/30" />
            <WipStageCard title="ASSEMBLY" value={summary.assembly} color="bg-blue-100 dark:bg-blue-900/30" />
          </div>
        </>
      )}

      {/* Filters */}
      {data && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Production Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search orders..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="w-48">
                <Select value={urgencyFilter} onValueChange={setUrgencyFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Urgencies" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Urgencies</SelectItem>
                    <SelectItem value="OVERDUE">Overdue</SelectItem>
                    <SelectItem value="TODAY">Today</SelectItem>
                    <SelectItem value="THIS_WEEK">This Week</SelectItem>
                    <SelectItem value="NEXT_WEEK">Next Week</SelectItem>
                    <SelectItem value="LATER">Later</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="w-48">
                <Select value={bedTypeFilter} onValueChange={setBedTypeFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Products" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Products</SelectItem>
                    {bedTypes.map(type => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
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
                    <th className="text-left p-3 font-medium">Item / Model</th>
                    <th className="text-left p-3 font-medium">Job #</th>
                    <th className="text-left p-3 font-medium">Released</th>
                    <th className="text-left p-3 font-medium">Product</th>
                    <th className="text-right p-3 font-medium">Qty Rem</th>
                    <th className="text-right p-3 font-medium">Weld</th>
                    <th className="text-right p-3 font-medium">Blast</th>
                    <th className="text-right p-3 font-medium">Paint</th>
                    <th className="text-right p-3 font-medium">Assy</th>
                    <th className="text-right p-3 font-medium">On Hand</th>
                    <th className="text-left p-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((ol, i) => (
                    <tr key={`${ol.order_num}-${ol.order_line}-${i}`} className="border-b hover:bg-muted/50">
                      <td className="p-3 font-mono text-xs">{ol.order_num}</td>
                      <td className="p-3 text-center">
                        <Badge variant="outline" className="font-mono">{ol.order_line}</Badge>
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
                        <p className="font-medium text-xs truncate max-w-[150px]" title={ol.customer_name}>
                          {ol.customer_name || "Unknown"}
                        </p>
                      </td>
                      <td className="p-3">
                        <div>
                          <p className="font-mono text-xs font-medium">{ol.item}</p>
                          {ol.model && ol.model !== ol.item && (
                            <p className="text-xs text-muted-foreground">{ol.model}</p>
                          )}
                        </div>
                      </td>
                      <td className="p-3">
                        {ol.job_numbers ? (
                          <span className="font-mono text-xs text-green-600">{ol.job_numbers.split(";")[0].trim()}</span>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </td>
                      <td className="p-3">
                        {ol.released_date ? (
                          <span className="text-xs">{new Date(ol.released_date).toLocaleDateString()}</span>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </td>
                      <td className="p-3">
                        <BedTypeBadge bedType={ol.bed_type} />
                      </td>
                      <td className="p-3 text-right font-medium">{ol.qty_remaining}</td>
                      <td className="p-3 text-right">
                        {ol.item_at_weld > 0 ? ol.item_at_weld : <span className="text-muted-foreground">-</span>}
                      </td>
                      <td className="p-3 text-right">
                        {ol.item_at_blast > 0 ? ol.item_at_blast : <span className="text-muted-foreground">-</span>}
                      </td>
                      <td className="p-3 text-right">
                        {ol.item_at_paint > 0 ? ol.item_at_paint : <span className="text-muted-foreground">-</span>}
                      </td>
                      <td className="p-3 text-right">
                        {ol.item_at_assy > 0 ? ol.item_at_assy : <span className="text-muted-foreground">-</span>}
                      </td>
                      <td className="p-3 text-right">
                        {ol.item_on_hand > 0 ? ol.item_on_hand : <span className="text-muted-foreground">-</span>}
                      </td>
                      <td className="p-3">
                        <UrgencyBadge urgency={ol.urgency} />
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
      {!data && !openOrdersMutation.isPending && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <Package className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold mb-2">No Data Loaded</h3>
            <p className="text-muted-foreground mb-4">
              Click "Fetch Orders" to load open orders from Bedrock SyteLine
            </p>
            <Button
              onClick={() => openOrdersMutation.mutate()}
              disabled={!healthQuery.data?.connected}
            >
              <Play className="w-4 h-4 mr-2" />
              Fetch Orders
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {openOrdersMutation.error && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Error Loading Orders
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{(openOrdersMutation.error as Error).message}</p>
          </CardContent>
        </Card>
      )}

      {/* Schema Info */}
      <Card className="bg-muted/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">CSV Export Schema (OPEN ORDERS V5)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 text-xs">
            {["OrderNum", "CustomerName", "DueDate", "Urgency", "Item", "Model", "BedType", 
              "QtyRemaining", "Item_AtWeld", "Item_AtBlast", "Item_AtPaint", "Item_AtAssy", 
              "Item_OnHand", "JobNumbers", "LineValue", "FirstForItem"].map(col => (
              <code key={col} className="px-2 py-1 bg-background rounded border">{col}</code>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
