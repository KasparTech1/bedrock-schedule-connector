import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  ArrowLeft,
  Loader2,
  Database,
  GitBranch,
  Wrench,
  Code2,
  FileJson,
  Key,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";

// API endpoint mapping for connectors
const API_ENDPOINTS: Record<string, { endpoint: string; scope: string; description: string }> = {
  "customer-search": {
    endpoint: "/api/v1/customers",
    scope: "customers:read",
    description: "Search and retrieve customer information",
  },
  "order-availability": {
    endpoint: "/api/v1/orders/availability",
    scope: "orders:read",
    description: "Get order availability with allocation analysis",
  },
  "bedrock-ops-scheduler": {
    endpoint: "/api/v1/jobs",
    scope: "jobs:read",
    description: "Get production jobs and schedule data",
  },
};

interface ConnectorDetailProps {
  id: string;
}

export function ConnectorDetail({ id }: ConnectorDetailProps) {
  const { data: connector, isLoading, error } = useQuery({
    queryKey: ["connector", id],
    queryFn: () => api.connectors.get(id),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !connector) {
    return (
      <div className="space-y-4">
        <Link href="/">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Library
          </Button>
        </Link>
        <div className="text-center py-12">
          <p className="text-destructive">
            Connector not found or failed to load.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <Link href="/">
            <Button variant="ghost" size="sm" className="mb-2">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Library
            </Button>
          </Link>
          <h1 className="text-3xl font-semibold">{connector.name}</h1>
          <p className="text-muted-foreground">{connector.description}</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary">{connector.category}</Badge>
            <span className="text-sm text-muted-foreground">
              v{connector.version}
            </span>
            <Badge variant={connector.status === "published" ? "success" : "outline"}>
              {connector.status}
            </Badge>
          </div>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2">
        {connector.tags.map((tag) => (
          <Badge key={tag} variant="outline">
            {tag}
          </Badge>
        ))}
      </div>

      <Separator />

      {/* Main Content Grid - 2x2 layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Row 1: Data Sources | MCP Tools */}
        {/* IDO Data Sources */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" />
              Data Sources ({connector.idos.length})
            </CardTitle>
            <CardDescription>
              SyteLine IDOs used by this connector
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {connector.idos.map((ido) => (
              <div key={ido.name} className="border rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <code className="font-mono text-sm font-semibold text-primary">
                    {ido.name}
                  </code>
                  {ido.alias && (
                    <span className="text-xs text-muted-foreground">
                      as {ido.alias}
                    </span>
                  )}
                </div>
                {ido.description && (
                  <p className="text-sm text-muted-foreground">
                    {ido.description}
                  </p>
                )}
                <div className="text-xs text-muted-foreground">
                  {ido.properties.length} properties
                </div>
                {ido.default_filter && (
                  <div className="text-xs">
                    <span className="text-muted-foreground">Default filter: </span>
                    <code className="font-mono bg-muted px-1 rounded">
                      {ido.default_filter}
                    </code>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* MCP Tools */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wrench className="w-5 h-5 text-primary" />
              MCP Tools ({connector.tools.length})
            </CardTitle>
            <CardDescription>
              AI-callable tools exposed by this connector
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {connector.tools.map((tool) => (
              <div key={tool.name} className="border rounded-lg p-4 space-y-2">
                <code className="font-mono text-sm font-semibold text-primary">
                  {tool.name}
                </code>
                <p className="text-sm text-muted-foreground">
                  {tool.description}
                </p>
                {tool.parameters.length > 0 && (
                  <div className="space-y-1 mt-2">
                    <div className="text-xs font-medium">Parameters:</div>
                    {tool.parameters.map((param) => (
                      <div
                        key={param.name}
                        className="text-xs flex items-center gap-2"
                      >
                        <code className="font-mono bg-muted px-1 rounded">
                          {param.name}
                        </code>
                        <span className="text-muted-foreground">
                          : {param.type}
                        </span>
                        {param.required && (
                          <Badge variant="destructive" className="text-[10px] px-1 py-0">
                            required
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Row 2: Output Schema | API Access */}
        {/* Output Schema */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileJson className="w-5 h-5 text-primary" />
              Output Schema ({connector.output_fields.length} fields)
            </CardTitle>
            <CardDescription>
              Fields returned by this connector
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-2 font-medium">Field</th>
                    <th className="text-left p-2 font-medium">Type</th>
                    <th className="text-left p-2 font-medium hidden md:table-cell">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {connector.output_fields.map((field) => (
                    <tr key={field.name} className="border-t">
                      <td className="p-2 font-mono text-xs">{field.name}</td>
                      <td className="p-2 text-muted-foreground">{field.type}</td>
                      <td className="p-2 text-muted-foreground text-xs hidden md:table-cell">
                        {field.description}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* API Access Card - in grid */}
        <APIAccessCard connectorId={id} />
      </div>

      {/* Join Configuration - Full width when present */}
      {(connector.joins.length > 0 || connector.join_sql) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-primary" />
              Join Configuration
            </CardTitle>
            <CardDescription>
              How data sources are combined
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {connector.joins.map((join, i) => (
              <div key={i} className="text-sm">
                <span className="font-mono">{join.left_ido}</span>
                <span className="text-muted-foreground"> {join.type} JOIN </span>
                <span className="font-mono">{join.right_ido}</span>
                <span className="text-muted-foreground"> ON </span>
                <span className="font-mono">
                  {join.left_key} = {join.right_key}
                </span>
              </div>
            ))}
            {connector.join_sql && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Custom SQL:</div>
                <pre className="bg-muted p-3 rounded-lg text-xs overflow-x-auto font-mono">
                  {connector.join_sql}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Performance Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code2 className="w-5 h-5 text-primary" />
            Performance Hints
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div>
              <span className="text-sm text-muted-foreground">
                Estimated Volume:{" "}
              </span>
              <Badge variant="secondary">{connector.estimated_volume}</Badge>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">
                Freshness:{" "}
              </span>
              <Badge variant="secondary">{connector.freshness_requirement}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// API Access Card Component
function APIAccessCard({ connectorId }: { connectorId: string }) {
  const [copied, setCopied] = useState(false);
  const apiConfig = API_ENDPOINTS[connectorId];
  const baseUrl = window.location.origin;

  // If no API config for this connector, don't show the card
  if (!apiConfig) {
    return null;
  }

  const fullEndpoint = `${baseUrl}${apiConfig.endpoint}`;
  const curlExample = `curl -X GET "${fullEndpoint}" \\
  -H "X-API-Key: your_api_key" \\
  -H "Accept: application/json"`;

  const handleCopy = () => {
    navigator.clipboard.writeText(curlExample);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50/50 to-transparent dark:from-blue-900/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Key className="w-5 h-5 text-blue-500" />
          API Access
        </CardTitle>
        <CardDescription>
          Access this connector's data via REST API
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Endpoint Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted-foreground uppercase tracking-wide">
              Endpoint
            </label>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="bg-green-500/10 text-green-700 border-green-300">
                GET
              </Badge>
              <code className="text-sm font-mono bg-muted px-2 py-1 rounded">
                {apiConfig.endpoint}
              </code>
            </div>
          </div>
          <div>
            <label className="text-xs text-muted-foreground uppercase tracking-wide">
              Required Scope
            </label>
            <div className="mt-1">
              <Badge variant="secondary">{apiConfig.scope}</Badge>
            </div>
          </div>
        </div>

        {/* Quick Example */}
        <div>
          <label className="text-xs text-muted-foreground uppercase tracking-wide">
            Quick Example
          </label>
          <div className="relative mt-1 group">
            <pre className="bg-slate-900 text-slate-100 p-3 rounded-lg text-xs overflow-x-auto">
              <code>{curlExample}</code>
            </pre>
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 hover:bg-slate-700 text-white"
              onClick={handleCopy}
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Authentication Note */}
        <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <Key className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <span className="font-medium text-amber-800 dark:text-amber-200">
              Authentication Required
            </span>
            <p className="text-amber-700 dark:text-amber-300 text-xs mt-0.5">
              All API requests require an API key via the <code className="bg-amber-100 dark:bg-amber-800 px-1 rounded">X-API-Key</code> header.
            </p>
          </div>
        </div>

        {/* Link to Full Docs */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-muted-foreground">
            {apiConfig.description}
          </p>
          <Link href="/admin/api">
            <Button variant="outline" size="sm" className="gap-2">
              <ExternalLink className="w-4 h-4" />
              Full API Docs
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
