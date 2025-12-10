import { useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ConnectorCard } from "@/components/ConnectorCard";

// Mock data - will be replaced with API call
const mockConnectors = [
  {
    id: "bedrock-ops-scheduler",
    name: "Bedrock Ops Scheduler",
    description:
      "Production schedule visibility for Bedrock Truck Beds manufacturing operations. Track jobs, work centers, and completion status in real-time.",
    category: "Manufacturing",
    version: "1.0.0",
    tags: ["production", "jobs", "schedule", "work-centers"],
    icon: "factory",
  },
  {
    id: "sales-order-tracker",
    name: "Sales Order Tracker",
    description:
      "Track open sales orders, backlog, and customer orders. Monitor what needs to ship and identify late orders.",
    category: "Sales",
    version: "1.0.0",
    tags: ["orders", "customers", "shipping"],
    icon: "shopping-cart",
  },
  {
    id: "customer-search",
    name: "Customer Search",
    description:
      "Search and lookup customer information including contact details, addresses, and account status.",
    category: "Customers",
    version: "1.0.0",
    tags: ["customers", "contacts", "search"],
    icon: "users",
  },
  {
    id: "inventory-status",
    name: "Inventory Status",
    description:
      "Check current inventory levels, stock availability, and warehouse locations. Identify low-stock items.",
    category: "Inventory",
    version: "1.0.0",
    tags: ["inventory", "stock", "warehouse"],
    icon: "package",
  },
];

const categories = ["All", "Manufacturing", "Sales", "Customers", "Inventory"];

export function Library() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  const filteredConnectors = mockConnectors.filter((connector) => {
    const matchesSearch =
      connector.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connector.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connector.tags.some((tag) =>
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      );
    const matchesCategory =
      selectedCategory === "All" || connector.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

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

      {/* Results Count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredConnectors.length} connector
        {filteredConnectors.length !== 1 ? "s" : ""}
      </div>

      {/* Connector Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredConnectors.map((connector) => (
          <ConnectorCard key={connector.id} {...connector} />
        ))}
      </div>

      {/* Empty State */}
      {filteredConnectors.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No connectors found matching your search.
          </p>
        </div>
      )}
    </div>
  );
}
