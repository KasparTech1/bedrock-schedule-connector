import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  ArrowLeft,
  Key,
  Copy,
  Check,
  AlertTriangle,
  Shield,
  Clock,
  Activity,
  Code,
  ExternalLink,
  Eye,
  EyeOff,
  Plus,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Code example component
function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-sm overflow-x-auto">
        <code>{code}</code>
      </pre>
      <Button
        variant="ghost"
        size="sm"
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleCopy}
      >
        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      </Button>
    </div>
  );
}

export function APISettings() {
  const [showKey, setShowKey] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  
  // For demo purposes - in production this would come from the API
  const demoApiKey = "kai_live_demo_abc123xyz789";
  const baseUrl = window.location.origin;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link href="/admin/settings">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Settings
          </Button>
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-blue-500/10">
            <Key className="w-8 h-8 text-blue-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">API Connection & Settings</h1>
            <p className="text-muted-foreground">
              Configure external API access to KAI ERP connectors
            </p>
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="examples">Code Examples</TabsTrigger>
          <TabsTrigger value="keys">API Keys</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Quick Start</CardTitle>
              <CardDescription>
                Access Bedrock SyteLine data via REST API
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground text-xs">Base URL</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="bg-muted px-3 py-2 rounded flex-1 text-sm">
                      {baseUrl}/api/v1
                    </code>
                    <Button variant="outline" size="sm" onClick={() => navigator.clipboard.writeText(`${baseUrl}/api/v1`)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div>
                  <Label className="text-muted-foreground text-xs">Authentication</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="bg-muted px-3 py-2 rounded flex-1 text-sm">
                      X-API-Key: your_api_key
                    </code>
                  </div>
                </div>
              </div>

              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-amber-800 dark:text-amber-200">API Key Required</h4>
                    <p className="text-sm text-amber-700 dark:text-amber-300">
                      All API requests require authentication. Create an API key in the "API Keys" tab.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Available Connectors */}
          <Card>
            <CardHeader>
              <CardTitle>Available API Endpoints</CardTitle>
              <CardDescription>Data accessible via the public API</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">GET</Badge>
                    <code className="text-sm">/customers</code>
                  </div>
                  <h4 className="font-semibold">Customer Search</h4>
                  <p className="text-sm text-muted-foreground">
                    Search and retrieve customer information, addresses, contacts.
                  </p>
                  <div className="mt-2">
                    <Badge variant="secondary" className="text-xs">customers:read</Badge>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">GET</Badge>
                    <code className="text-sm">/orders/availability</code>
                  </div>
                  <h4 className="font-semibold">Order Availability</h4>
                  <p className="text-sm text-muted-foreground">
                    Order coverage analysis with inventory allocation from production stages.
                  </p>
                  <div className="mt-2">
                    <Badge variant="secondary" className="text-xs">orders:read</Badge>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">GET</Badge>
                    <code className="text-sm">/jobs</code>
                  </div>
                  <h4 className="font-semibold">Production Jobs</h4>
                  <p className="text-sm text-muted-foreground">
                    Manufacturing jobs with operations, work centers, and status.
                  </p>
                  <div className="mt-2">
                    <Badge variant="secondary" className="text-xs">jobs:read</Badge>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">GET</Badge>
                    <code className="text-sm">/health</code>
                  </div>
                  <h4 className="font-semibold">Health Check</h4>
                  <p className="text-sm text-muted-foreground">
                    Check API health and SyteLine connectivity status.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Rate Limits */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Rate Limits
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <p className="text-3xl font-bold">60</p>
                  <p className="text-sm text-muted-foreground">requests/minute</p>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <p className="text-3xl font-bold">10K</p>
                  <p className="text-sm text-muted-foreground">requests/day</p>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <p className="text-3xl font-bold">30s</p>
                  <p className="text-sm text-muted-foreground">timeout</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Endpoints Tab */}
        <TabsContent value="endpoints" className="space-y-6 mt-4">
          {/* Customer Search Endpoint */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Badge className="bg-green-500">GET</Badge>
                    /api/v1/customers
                  </CardTitle>
                  <CardDescription>Search for customers</CardDescription>
                </div>
                <Badge variant="outline">customers:read</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Query Parameters</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Parameter</th>
                        <th className="text-left p-2">Type</th>
                        <th className="text-left p-2">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="p-2"><code>search</code></td>
                        <td className="p-2">string</td>
                        <td className="p-2">Search term (matches name or customer number)</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2"><code>customer_number</code></td>
                        <td className="p-2">string</td>
                        <td className="p-2">Exact customer number lookup</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2"><code>city</code></td>
                        <td className="p-2">string</td>
                        <td className="p-2">Filter by city</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2"><code>state</code></td>
                        <td className="p-2">string</td>
                        <td className="p-2">Filter by state code (e.g., TX, CA)</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2"><code>status</code></td>
                        <td className="p-2">string</td>
                        <td className="p-2">A=Active, I=Inactive (default: A)</td>
                      </tr>
                      <tr>
                        <td className="p-2"><code>limit</code></td>
                        <td className="p-2">integer</td>
                        <td className="p-2">Max results (1-200, default: 50)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Example Response</h4>
                <CodeBlock
                  language="json"
                  code={`{
  "success": true,
  "data": {
    "total_count": 1,
    "customers": [
      {
        "cust_num": "C000123",
        "name": "Acme Trucking Co",
        "addr1": "123 Main St",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77001",
        "phone": "555-123-4567",
        "contact": "John Smith",
        "status": "A"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-12-11T15:30:00Z"
  }
}`}
                />
              </div>
            </CardContent>
          </Card>

          {/* Order Availability Endpoint */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Badge className="bg-green-500">GET</Badge>
                    /api/v1/orders/availability
                  </CardTitle>
                  <CardDescription>Get order availability with allocation analysis</CardDescription>
                </div>
                <Badge variant="outline">orders:read</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Query Parameters</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Parameter</th>
                        <th className="text-left p-2">Type</th>
                        <th className="text-left p-2">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="p-2"><code>customer</code></td>
                        <td className="p-2">string</td>
                        <td className="p-2">Filter by customer name (partial match)</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2"><code>item</code></td>
                        <td className="p-2">string</td>
                        <td className="p-2">Filter by item number (partial match)</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2"><code>shortage_only</code></td>
                        <td className="p-2">boolean</td>
                        <td className="p-2">Only return orders with shortages</td>
                      </tr>
                      <tr>
                        <td className="p-2"><code>limit</code></td>
                        <td className="p-2">integer</td>
                        <td className="p-2">Max order lines (1-1000, default: 500)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Code Examples Tab */}
        <TabsContent value="examples" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>cURL</CardTitle>
              <CardDescription>Command line examples</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm">Search Customers</Label>
                <CodeBlock
                  code={`curl -X GET "${baseUrl}/api/v1/customers?search=acme&limit=10" \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Accept: application/json"`}
                />
              </div>
              <div>
                <Label className="text-sm">Get Order Availability</Label>
                <CodeBlock
                  code={`curl -X GET "${baseUrl}/api/v1/orders/availability?shortage_only=true" \\
  -H "X-API-Key: your_api_key_here"`}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Python</CardTitle>
              <CardDescription>Using requests library</CardDescription>
            </CardHeader>
            <CardContent>
              <CodeBlock
                language="python"
                code={`import requests

API_KEY = "your_api_key_here"
BASE_URL = "${baseUrl}/api/v1"

headers = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

# Search customers
response = requests.get(
    f"{BASE_URL}/customers",
    headers=headers,
    params={"search": "acme", "limit": 10}
)
customers = response.json()

# Get order availability with shortages
response = requests.get(
    f"{BASE_URL}/orders/availability",
    headers=headers,
    params={"shortage_only": True}
)
orders = response.json()

# Print summary
print(f"Found {orders['data']['summary']['total_lines']} order lines")
print(f"Coverage: {orders['data']['summary']['coverage_percentage']}%")`}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>JavaScript / TypeScript</CardTitle>
              <CardDescription>Using fetch API</CardDescription>
            </CardHeader>
            <CardContent>
              <CodeBlock
                language="typescript"
                code={`const API_KEY = "your_api_key_here";
const BASE_URL = "${baseUrl}/api/v1";

async function searchCustomers(searchTerm: string) {
  const response = await fetch(
    \`\${BASE_URL}/customers?search=\${encodeURIComponent(searchTerm)}&limit=10\`,
    {
      headers: {
        "X-API-Key": API_KEY,
        "Accept": "application/json"
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(\`API error: \${response.status}\`);
  }
  
  return response.json();
}

async function getOrderAvailability(shortageOnly = false) {
  const params = new URLSearchParams();
  if (shortageOnly) params.set("shortage_only", "true");
  
  const response = await fetch(
    \`\${BASE_URL}/orders/availability?\${params}\`,
    {
      headers: { "X-API-Key": API_KEY }
    }
  );
  
  return response.json();
}

// Usage
const customers = await searchCustomers("acme");
const orders = await getOrderAvailability(true);
console.log(\`Coverage: \${orders.data.summary.coverage_percentage}%\`);`}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Power Automate / n8n</CardTitle>
              <CardDescription>Integration platform configuration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-muted p-4 rounded-lg">
                <h4 className="font-semibold mb-2">HTTP Request Configuration</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <Label className="text-muted-foreground">Method</Label>
                    <p className="font-mono">GET</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">URL</Label>
                    <p className="font-mono">{baseUrl}/api/v1/customers</p>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-muted-foreground">Headers</Label>
                    <pre className="bg-background p-2 rounded text-xs mt-1">
{`X-API-Key: {{your_api_key}}
Accept: application/json`}
                    </pre>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="keys" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Your API Keys</CardTitle>
                  <CardDescription>Manage API keys for external access</CardDescription>
                </div>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Create New Key
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Demo key */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Key className="w-4 h-4 text-muted-foreground" />
                      <span className="font-semibold">Development Key</span>
                      <Badge variant="secondary">Active</Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" onClick={() => setShowKey(!showKey)}>
                        {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <code className="bg-muted px-3 py-1 rounded text-sm flex-1">
                      {showKey ? demoApiKey : "kai_live_••••••••••••••••"}
                    </code>
                    <Button variant="outline" size="sm" onClick={() => navigator.clipboard.writeText(demoApiKey)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>Created: Dec 11, 2025</span>
                    <span>Last used: Just now</span>
                    <span>Requests today: 42</span>
                    <span>Scopes: all</span>
                  </div>
                </div>

                {/* Info about scopes */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <h4 className="font-semibold mb-2">Available Scopes</h4>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">customers:read</Badge>
                    <Badge variant="outline">orders:read</Badge>
                    <Badge variant="outline">jobs:read</Badge>
                    <Badge variant="outline">inventory:read</Badge>
                    <Badge variant="outline">schedule:read</Badge>
                    <Badge variant="outline">admin</Badge>
                    <Badge variant="outline">* (all)</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
