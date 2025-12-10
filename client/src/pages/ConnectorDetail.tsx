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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";

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

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

        {/* Join Configuration */}
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
      </div>

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
