import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  ArrowLeft,
  Factory,
  Loader2,
  CheckCircle2,
  XCircle,
  Play,
  Wrench,
  Package,
  Users,
  Activity,
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
import { api } from "@/lib/api";

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "R":
      return <Badge className="bg-blue-500">Released</Badge>;
    case "F":
      return <Badge className="bg-green-500">Finished</Badge>;
    case "C":
      return <Badge className="bg-gray-500">Closed</Badge>;
    case "S":
      return <Badge className="bg-yellow-500">Started</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

function ProgressBar({ percent }: { percent: number }) {
  const width = Math.min(percent, 100);
  return (
    <div className="w-full bg-muted rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all ${
          percent >= 100 ? "bg-green-500" : percent > 0 ? "bg-blue-500" : "bg-gray-300"
        }`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

export function BedrockLive() {
  // Filter state
  const [jobFilter, setJobFilter] = useState("");
  const [workCenterFilter, setWorkCenterFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [limit, setLimit] = useState("25");

  // Health check
  const healthQuery = useQuery({
    queryKey: ["bedrock-health"],
    queryFn: () => api.bedrock.health(),
    refetchInterval: 30000,
  });

  // Schedule query mutation (manual trigger)
  const scheduleMutation = useMutation({
    mutationFn: async () => {
      const includeComplete = statusFilter === "all" || statusFilter === "F";
      const data = await api.bedrock.schedule(includeComplete, parseInt(limit) || 25);
      
      // Apply client-side filters
      let jobs = data.data.jobs;
      
      if (jobFilter) {
        jobs = jobs.filter(j => 
          j.job.toLowerCase().includes(jobFilter.toLowerCase()) ||
          j.item.toLowerCase().includes(jobFilter.toLowerCase())
        );
      }
      
      if (workCenterFilter) {
        jobs = jobs.filter(j => 
          j.operations.some(op => 
            op.work_center.toLowerCase().includes(workCenterFilter.toLowerCase())
          )
        );
      }
      
      if (statusFilter && statusFilter !== "all") {
        jobs = jobs.filter(j => j.status === statusFilter);
      }
      
      return { ...data, data: { ...data.data, jobs } };
    },
  });

  const data = scheduleMutation.data?.data;

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div>
        <Link href="/connector/bedrock-ops-scheduler">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Connector Details
          </Button>
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-primary/10">
            <Factory className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Try Bedrock Ops Scheduler</h1>
            <p className="text-muted-foreground">
              Live connection to Bedrock Truck Beds production environment
            </p>
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Factory className="w-5 h-5" />
              Connection Status
            </CardTitle>
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
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Base URL:</span>
              <p className="font-mono text-xs mt-1">https://mingle-ionapi.inforcloudsuite.com</p>
            </div>
            <div>
              <span className="text-muted-foreground">Config:</span>
              <p className="font-mono text-xs mt-1">DUU6QAFE74D2YDYW_TRN_TBE2</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Query Builder */}
      <Card>
        <CardHeader>
          <CardTitle>Query Production Schedule</CardTitle>
          <CardDescription>
            Filter jobs and operations from the live Bedrock Truck Beds environment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="job">Job / Item Filter</Label>
              <Input
                id="job"
                placeholder="e.g., 10256"
                value={jobFilter}
                onChange={(e) => setJobFilter(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Search job number or item</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="workCenter">Work Center</Label>
              <Input
                id="workCenter"
                placeholder="e.g., LASER"
                value={workCenterFilter}
                onChange={(e) => setWorkCenterFilter(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Filter by work center</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="R">Released</SelectItem>
                  <SelectItem value="S">Started</SelectItem>
                  <SelectItem value="F">Finished</SelectItem>
                  <SelectItem value="C">Closed</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Job status filter</p>
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
            onClick={() => scheduleMutation.mutate()}
            disabled={scheduleMutation.isPending || !healthQuery.data?.connected}
            className="w-full"
          >
            {scheduleMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Querying Live Bedrock...
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

      {/* Stats Summary */}
      {data && (
        <div className="grid grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <Package className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{data.jobs.length}</p>
                  <p className="text-sm text-muted-foreground">Jobs Found</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-500/10">
                  <Activity className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{data.active_jobs}</p>
                  <p className="text-sm text-muted-foreground">Active Jobs</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-orange-500/10">
                  <Wrench className="w-5 h-5 text-orange-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{data.work_centers.length}</p>
                  <p className="text-sm text-muted-foreground">Work Centers</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10">
                  <Users className="w-5 h-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-lg font-bold truncate">{data.work_centers.join(", ") || "None"}</p>
                  <p className="text-sm text-muted-foreground">Work Centers</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Results Table */}
      {data && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Results</CardTitle>
              <Badge variant="secondary">{data.jobs.length} jobs</Badge>
            </div>
            <CardDescription>
              Production schedule data from SLJobs and SLJobRoutes IDOs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-medium">Job</th>
                    <th className="text-left p-2 font-medium">Item</th>
                    <th className="text-left p-2 font-medium">Description</th>
                    <th className="text-left p-2 font-medium">Status</th>
                    <th className="text-left p-2 font-medium">Progress</th>
                    <th className="text-right p-2 font-medium">Qty Released</th>
                    <th className="text-right p-2 font-medium">Qty Complete</th>
                    <th className="text-left p-2 font-medium">Work Centers</th>
                  </tr>
                </thead>
                <tbody>
                  {data.jobs.map((job, i) => (
                    <tr key={`${job.job}-${job.suffix}-${i}`} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-mono">
                        {job.job}
                        {job.suffix > 0 && <span className="text-muted-foreground">-{job.suffix}</span>}
                      </td>
                      <td className="p-2 font-mono text-xs">{job.item}</td>
                      <td className="p-2 max-w-[200px] truncate" title={job.item_description}>
                        {job.item_description}
                      </td>
                      <td className="p-2">
                        <StatusBadge status={job.status} />
                      </td>
                      <td className="p-2 min-w-[100px]">
                        <div className="flex items-center gap-2">
                          <ProgressBar percent={job.pct_complete} />
                          <span className="text-xs text-muted-foreground w-10">
                            {job.pct_complete}%
                          </span>
                        </div>
                      </td>
                      <td className="p-2 text-right">{job.qty_released}</td>
                      <td className="p-2 text-right">{job.qty_complete}</td>
                      <td className="p-2">
                        <div className="flex flex-wrap gap-1">
                          {job.operations.map((op, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {op.work_center}
                            </Badge>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.jobs.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No jobs found matching your filters
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {scheduleMutation.error && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{(scheduleMutation.error as Error).message}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

