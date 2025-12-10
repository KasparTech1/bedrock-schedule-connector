import { Link } from "wouter";
import { Plus, Pencil, Copy, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Mock data
const mockConnectors = [
  {
    id: "bedrock-ops-scheduler",
    name: "Bedrock Ops Scheduler",
    category: "Manufacturing",
    version: "1.0.0",
    status: "published",
    tools: 1,
  },
  {
    id: "sales-order-tracker",
    name: "Sales Order Tracker",
    category: "Sales",
    version: "1.0.0",
    status: "published",
    tools: 1,
  },
  {
    id: "customer-search",
    name: "Customer Search",
    category: "Customers",
    version: "1.0.0",
    status: "draft",
    tools: 1,
  },
  {
    id: "inventory-status",
    name: "Inventory Status",
    category: "Inventory",
    version: "1.0.0",
    status: "published",
    tools: 1,
  },
];

export function Connectors() {
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

      {/* Connectors Table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">All Connectors</CardTitle>
        </CardHeader>
        <CardContent>
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
                {mockConnectors.map((connector) => (
                  <tr
                    key={connector.id}
                    className="border-b transition-colors hover:bg-muted/50"
                  >
                    <td className="p-4 align-middle font-medium">
                      {connector.name}
                    </td>
                    <td className="p-4 align-middle">
                      <Badge variant="secondary">{connector.category}</Badge>
                    </td>
                    <td className="p-4 align-middle text-muted-foreground">
                      v{connector.version}
                    </td>
                    <td className="p-4 align-middle text-muted-foreground">
                      {connector.tools}
                    </td>
                    <td className="p-4 align-middle">
                      <Badge
                        variant={
                          connector.status === "published" ? "success" : "outline"
                        }
                      >
                        {connector.status}
                      </Badge>
                    </td>
                    <td className="p-4 align-middle text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link href={`/admin/connectors/${connector.id}/edit`}>
                          <Button variant="ghost" size="icon">
                            <Pencil className="w-4 h-4" />
                          </Button>
                        </Link>
                        <Button variant="ghost" size="icon">
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
