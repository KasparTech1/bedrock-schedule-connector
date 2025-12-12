import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  ArrowLeft,
  Users,
  Loader2,
  CheckCircle2,
  XCircle,
  Play,
  Phone,
  Mail,
  MapPin,
  Building2,
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
import { api, BedrockCustomer } from "@/lib/api";

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "A":
      return <Badge className="bg-green-500">Active</Badge>;
    case "I":
      return <Badge className="bg-gray-500">Inactive</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

export function BedrockCustomerSearch() {
  // Filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [customerNumber, setCustomerNumber] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [limit, setLimit] = useState("50");

  // Health check
  const healthQuery = useQuery({
    queryKey: ["bedrock-health"],
    queryFn: () => api.bedrock.health(),
    refetchInterval: 30000,
  });

  // Customer search mutation (manual trigger)
  const customerMutation = useMutation({
    mutationFn: async () => {
      return api.bedrock.customers({
        search: searchTerm || undefined,
        customer_number: customerNumber || undefined,
        city: city || undefined,
        state: state || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        limit: parseInt(limit) || 50,
      });
    },
  });

  const data = customerMutation.data?.data;

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div>
        <Link href="/">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Library
          </Button>
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-primary/10">
            <Users className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Bedrock Customer Search</h1>
            <p className="text-muted-foreground">
              Live customer data from Bedrock Truck Beds SyteLine
            </p>
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5" />
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
          <CardTitle>Search Customers</CardTitle>
          <CardDescription>
            Search Bedrock Truck Beds customer records from the SLCustomers IDO
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search">Name / Number Search</Label>
              <Input
                id="search"
                placeholder="e.g., Acme or C001"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Search name or customer #</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="custNum">Customer Number</Label>
              <Input
                id="custNum"
                placeholder="Exact match"
                value={customerNumber}
                onChange={(e) => setCustomerNumber(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Exact customer number</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="A">Active</SelectItem>
                  <SelectItem value="I">Inactive</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Customer status</p>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                placeholder="e.g., Houston"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Filter by city</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="state">State</Label>
              <Input
                id="state"
                placeholder="e.g., TX"
                value={state}
                onChange={(e) => setState(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">State code</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="limit">Limit</Label>
              <Input
                id="limit"
                type="number"
                min="1"
                max="200"
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Max records (1-200)</p>
            </div>
          </div>

          <Button
            onClick={() => customerMutation.mutate()}
            disabled={customerMutation.isPending || !healthQuery.data?.connected}
            className="w-full"
          >
            {customerMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Searching Bedrock Customers...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Execute Search
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results Table */}
      {data && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Results</CardTitle>
              <Badge variant="secondary">{data.total_count} customers</Badge>
            </div>
            <CardDescription>
              Customer data from SLCustomers IDO
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-medium">Cust #</th>
                    <th className="text-left p-2 font-medium">Name</th>
                    <th className="text-left p-2 font-medium">Contact</th>
                    <th className="text-left p-2 font-medium">City</th>
                    <th className="text-left p-2 font-medium">State</th>
                    <th className="text-left p-2 font-medium">Phone</th>
                    <th className="text-left p-2 font-medium">Email</th>
                    <th className="text-left p-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.customers.map((cust, i) => (
                    <tr key={`${cust.cust_num}-${i}`} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-mono text-xs">{cust.cust_num}</td>
                      <td className="p-2 font-medium max-w-[200px] truncate" title={cust.name}>
                        {cust.name}
                      </td>
                      <td className="p-2">{cust.contact || "-"}</td>
                      <td className="p-2">{cust.city || "-"}</td>
                      <td className="p-2">{cust.state || "-"}</td>
                      <td className="p-2">
                        {cust.phone ? (
                          <span className="flex items-center gap-1">
                            <Phone className="w-3 h-3 text-muted-foreground" />
                            {cust.phone}
                          </span>
                        ) : "-"}
                      </td>
                      <td className="p-2">
                        {cust.email ? (
                          <span className="flex items-center gap-1 text-xs">
                            <Mail className="w-3 h-3 text-muted-foreground" />
                            <span className="truncate max-w-[150px]" title={cust.email}>
                              {cust.email}
                            </span>
                          </span>
                        ) : "-"}
                      </td>
                      <td className="p-2">
                        <StatusBadge status={cust.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.customers.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No customers found matching your search
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Customer Cards View (for smaller result sets) */}
      {data && data.customers.length > 0 && data.customers.length <= 10 && (
        <div className="grid grid-cols-2 gap-4">
          {data.customers.map((cust, i) => (
            <CustomerCard key={`card-${cust.cust_num}-${i}`} customer={cust} />
          ))}
        </div>
      )}

      {/* Error */}
      {customerMutation.error && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{(customerMutation.error as Error).message}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CustomerCard({ customer }: { customer: BedrockCustomer }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{customer.name}</CardTitle>
            <CardDescription className="font-mono">{customer.cust_num}</CardDescription>
          </div>
          <StatusBadge status={customer.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {customer.contact && (
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-muted-foreground" />
            {customer.contact}
          </div>
        )}
        {(customer.addr1 || customer.city) && (
          <div className="flex items-start gap-2">
            <MapPin className="w-4 h-4 text-muted-foreground mt-0.5" />
            <div>
              {customer.addr1 && <div>{customer.addr1}</div>}
              {customer.addr2 && <div>{customer.addr2}</div>}
              <div>
                {[customer.city, customer.state, customer.zip_code]
                  .filter(Boolean)
                  .join(", ")}
              </div>
              {customer.country && customer.country !== "US" && (
                <div>{customer.country}</div>
              )}
            </div>
          </div>
        )}
        {customer.phone && (
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4 text-muted-foreground" />
            {customer.phone}
          </div>
        )}
        {customer.email && (
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4 text-muted-foreground" />
            <span className="truncate">{customer.email}</span>
          </div>
        )}
        {customer.cust_type && (
          <div className="pt-2">
            <Badge variant="outline">{customer.cust_type}</Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}


