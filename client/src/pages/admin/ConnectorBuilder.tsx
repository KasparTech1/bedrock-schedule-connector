import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation } from "wouter";
import {
  ArrowLeft,
  Save,
  Loader2,
  Plus,
  Trash2,
  GripVertical,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { api, ConnectorConfig, IDOConfig, PropertyConfig, ToolConfig, ToolParameterConfig } from "@/lib/api";

interface ConnectorBuilderProps {
  id?: string;
}

const CATEGORIES = ["Manufacturing", "Sales", "Customers", "Inventory", "General"];
const ICONS = ["factory", "shopping-cart", "users", "package", "puzzle", "database", "zap"];
const PROPERTY_TYPES = ["string", "number", "date", "boolean"];
const VOLUME_OPTIONS = ["low", "medium", "high"];
const FRESHNESS_OPTIONS = ["real-time", "near-real-time", "batch"];

function generateId(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function ConnectorBuilder({ id }: ConnectorBuilderProps) {
  const [, navigate] = useLocation();
  const queryClient = useQueryClient();
  const isNew = !id;

  // Default connector config
  const defaultConfig: ConnectorConfig = {
    id: "",
    name: "",
    description: "",
    version: "1.0.0",
    category: "General",
    icon: "puzzle",
    tags: [],
    status: "draft",
    idos: [],
    joins: [],
    join_sql: "",
    output_fields: [],
    tools: [],
    estimated_volume: "medium",
    freshness_requirement: "real-time",
  };

  const [config, setConfig] = useState<ConnectorConfig>(defaultConfig);
  const [tagInput, setTagInput] = useState("");
  const [autoGenerateId, setAutoGenerateId] = useState(true);

  // Fetch existing connector if editing
  const { data: existingConnector, isLoading } = useQuery({
    queryKey: ["connector", id],
    queryFn: () => api.connectors.get(id!),
    enabled: !!id,
  });

  useEffect(() => {
    if (existingConnector) {
      setConfig(existingConnector);
      setAutoGenerateId(false);
    }
  }, [existingConnector]);

  // Create/Update mutations
  const createMutation = useMutation({
    mutationFn: (config: ConnectorConfig) => api.connectors.create(config),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["connectors"] });
      navigate(`/connector/${data.id}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (config: ConnectorConfig) => api.connectors.update(config.id, config),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["connectors"] });
      queryClient.invalidateQueries({ queryKey: ["connector", data.id] });
      navigate(`/connector/${data.id}`);
    },
  });

  const handleSave = () => {
    if (isNew) {
      createMutation.mutate(config);
    } else {
      updateMutation.mutate(config);
    }
  };

  const handleNameChange = (name: string) => {
    setConfig((prev) => ({
      ...prev,
      name,
      id: autoGenerateId && isNew ? generateId(name) : prev.id,
    }));
  };

  const addTag = () => {
    if (tagInput.trim() && !config.tags.includes(tagInput.trim())) {
      setConfig((prev) => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()],
      }));
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setConfig((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tag),
    }));
  };

  // IDO management
  const addIDO = () => {
    const newIDO: IDOConfig = {
      name: "",
      alias: "",
      description: "",
      properties: [],
      default_filter: "",
    };
    setConfig((prev) => ({ ...prev, idos: [...prev.idos, newIDO] }));
  };

  const updateIDO = (index: number, updates: Partial<IDOConfig>) => {
    setConfig((prev) => ({
      ...prev,
      idos: prev.idos.map((ido, i) => (i === index ? { ...ido, ...updates } : ido)),
    }));
  };

  const removeIDO = (index: number) => {
    setConfig((prev) => ({
      ...prev,
      idos: prev.idos.filter((_, i) => i !== index),
    }));
  };

  // Property management within IDO
  const addProperty = (idoIndex: number) => {
    const newProp: PropertyConfig = {
      name: "",
      alias: "",
      type: "string",
      description: "",
      filterable: false,
      sortable: false,
      primary_key: false,
    };
    setConfig((prev) => ({
      ...prev,
      idos: prev.idos.map((ido, i) =>
        i === idoIndex ? { ...ido, properties: [...ido.properties, newProp] } : ido
      ),
    }));
  };

  const updateProperty = (
    idoIndex: number,
    propIndex: number,
    updates: Partial<PropertyConfig>
  ) => {
    setConfig((prev) => ({
      ...prev,
      idos: prev.idos.map((ido, i) =>
        i === idoIndex
          ? {
              ...ido,
              properties: ido.properties.map((p, j) =>
                j === propIndex ? { ...p, ...updates } : p
              ),
            }
          : ido
      ),
    }));
  };

  const removeProperty = (idoIndex: number, propIndex: number) => {
    setConfig((prev) => ({
      ...prev,
      idos: prev.idos.map((ido, i) =>
        i === idoIndex
          ? { ...ido, properties: ido.properties.filter((_, j) => j !== propIndex) }
          : ido
      ),
    }));
  };

  // Tool management
  const addTool = () => {
    const newTool: ToolConfig = {
      name: "",
      description: "",
      parameters: [],
    };
    setConfig((prev) => ({ ...prev, tools: [...prev.tools, newTool] }));
  };

  const updateTool = (index: number, updates: Partial<ToolConfig>) => {
    setConfig((prev) => ({
      ...prev,
      tools: prev.tools.map((tool, i) => (i === index ? { ...tool, ...updates } : tool)),
    }));
  };

  const removeTool = (index: number) => {
    setConfig((prev) => ({
      ...prev,
      tools: prev.tools.filter((_, i) => i !== index),
    }));
  };

  // Tool parameter management
  const addToolParam = (toolIndex: number) => {
    const newParam: ToolParameterConfig = {
      name: "",
      type: "string",
      description: "",
      required: false,
    };
    setConfig((prev) => ({
      ...prev,
      tools: prev.tools.map((tool, i) =>
        i === toolIndex ? { ...tool, parameters: [...tool.parameters, newParam] } : tool
      ),
    }));
  };

  const updateToolParam = (
    toolIndex: number,
    paramIndex: number,
    updates: Partial<ToolParameterConfig>
  ) => {
    setConfig((prev) => ({
      ...prev,
      tools: prev.tools.map((tool, i) =>
        i === toolIndex
          ? {
              ...tool,
              parameters: tool.parameters.map((p, j) =>
                j === paramIndex ? { ...p, ...updates } : p
              ),
            }
          : tool
      ),
    }));
  };

  const removeToolParam = (toolIndex: number, paramIndex: number) => {
    setConfig((prev) => ({
      ...prev,
      tools: prev.tools.map((tool, i) =>
        i === toolIndex
          ? { ...tool, parameters: tool.parameters.filter((_, j) => j !== paramIndex) }
          : tool
      ),
    }));
  };

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const saveError = createMutation.error || updateMutation.error;

  if (!isNew && isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Link href="/admin/connectors">
            <Button variant="ghost" size="sm" className="mb-2">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Connectors
            </Button>
          </Link>
          <h1 className="text-3xl font-semibold">
            {isNew ? "New Connector" : `Edit: ${config.name}`}
          </h1>
        </div>
        <Button onClick={handleSave} disabled={isSaving || !config.id || !config.name}>
          {isSaving ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          {isNew ? "Create Connector" : "Save Changes"}
        </Button>
      </div>

      {saveError && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive p-4 rounded-lg">
          {saveError instanceof Error ? saveError.message : "Failed to save connector"}
        </div>
      )}

      {/* Tabbed Form */}
      <Tabs defaultValue="identity" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-flex">
          <TabsTrigger value="identity">Identity</TabsTrigger>
          <TabsTrigger value="data-sources">Data Sources</TabsTrigger>
          <TabsTrigger value="join-sql">Join SQL</TabsTrigger>
          <TabsTrigger value="tools">MCP Tools</TabsTrigger>
        </TabsList>

        {/* Identity Tab */}
        <TabsContent value="identity">
          <Card>
            <CardHeader>
              <CardTitle>Connector Identity</CardTitle>
              <CardDescription>
                Basic information about this connector
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={config.name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="e.g., Production Schedule Tracker"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="id">ID (slug) *</Label>
                  <Input
                    id="id"
                    value={config.id}
                    onChange={(e) => {
                      setAutoGenerateId(false);
                      setConfig((prev) => ({ ...prev, id: e.target.value }));
                    }}
                    placeholder="e.g., production-schedule-tracker"
                    disabled={!isNew}
                  />
                  <p className="text-xs text-muted-foreground">
                    Unique identifier, auto-generated from name
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  value={config.description}
                  onChange={(e) =>
                    setConfig((prev) => ({ ...prev, description: e.target.value }))
                  }
                  placeholder="Describe what this connector does..."
                  rows={3}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-4">
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select
                    value={config.category}
                    onValueChange={(v) =>
                      setConfig((prev) => ({ ...prev, category: v }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat}>
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Icon</Label>
                  <Select
                    value={config.icon}
                    onValueChange={(v) =>
                      setConfig((prev) => ({ ...prev, icon: v }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ICONS.map((icon) => (
                        <SelectItem key={icon} value={icon}>
                          {icon}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="version">Version</Label>
                  <Input
                    id="version"
                    value={config.version}
                    onChange={(e) =>
                      setConfig((prev) => ({ ...prev, version: e.target.value }))
                    }
                    placeholder="1.0.0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={config.status}
                    onValueChange={(v) =>
                      setConfig((prev) => ({ ...prev, status: v }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="draft">Draft</SelectItem>
                      <SelectItem value="published">Published</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="flex gap-2 flex-wrap mb-2">
                  {config.tags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="secondary"
                      className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                      onClick={() => removeTag(tag)}
                    >
                      {tag} ×
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addTag())}
                    placeholder="Add a tag..."
                    className="max-w-xs"
                  />
                  <Button type="button" variant="outline" onClick={addTag}>
                    Add Tag
                  </Button>
                </div>
              </div>

              <Separator />

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Estimated Volume</Label>
                  <Select
                    value={config.estimated_volume}
                    onValueChange={(v) =>
                      setConfig((prev) => ({ ...prev, estimated_volume: v }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VOLUME_OPTIONS.map((opt) => (
                        <SelectItem key={opt} value={opt}>
                          {opt}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Freshness Requirement</Label>
                  <Select
                    value={config.freshness_requirement}
                    onValueChange={(v) =>
                      setConfig((prev) => ({ ...prev, freshness_requirement: v }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FRESHNESS_OPTIONS.map((opt) => (
                        <SelectItem key={opt} value={opt}>
                          {opt}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Sources Tab */}
        <TabsContent value="data-sources">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>IDO Data Sources</CardTitle>
                  <CardDescription>
                    SyteLine IDOs this connector will query
                  </CardDescription>
                </div>
                <Button onClick={addIDO} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add IDO
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {config.idos.length === 0 && (
                <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
                  <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No IDOs configured yet. Add an IDO to start defining data sources.</p>
                </div>
              )}

              {config.idos.map((ido, idoIndex) => (
                <Card key={idoIndex} className="border-2">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <GripVertical className="w-4 h-4 text-muted-foreground" />
                        <Input
                          value={ido.name}
                          onChange={(e) => updateIDO(idoIndex, { name: e.target.value })}
                          placeholder="IDO Name (e.g., SLJobs)"
                          className="max-w-[200px] font-mono"
                        />
                        <Input
                          value={ido.alias || ""}
                          onChange={(e) => updateIDO(idoIndex, { alias: e.target.value })}
                          placeholder="Alias"
                          className="max-w-[150px]"
                        />
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive"
                        onClick={() => removeIDO(idoIndex)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Description</Label>
                      <Input
                        value={ido.description || ""}
                        onChange={(e) =>
                          updateIDO(idoIndex, { description: e.target.value })
                        }
                        placeholder="What data does this IDO provide?"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Default Filter</Label>
                      <Input
                        value={ido.default_filter || ""}
                        onChange={(e) =>
                          updateIDO(idoIndex, { default_filter: e.target.value })
                        }
                        placeholder="e.g., Status = 'O'"
                        className="font-mono"
                      />
                    </div>

                    <Separator />

                    {/* Properties */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Properties ({ido.properties.length})</Label>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => addProperty(idoIndex)}
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          Add Property
                        </Button>
                      </div>

                      {ido.properties.length > 0 && (
                        <div className="border rounded-lg overflow-hidden">
                          <table className="w-full text-sm">
                            <thead className="bg-muted">
                              <tr>
                                <th className="text-left p-2">Name</th>
                                <th className="text-left p-2">Alias</th>
                                <th className="text-left p-2">Type</th>
                                <th className="text-left p-2">Flags</th>
                                <th className="p-2 w-10"></th>
                              </tr>
                            </thead>
                            <tbody>
                              {ido.properties.map((prop, propIndex) => (
                                <tr key={propIndex} className="border-t">
                                  <td className="p-2">
                                    <Input
                                      value={prop.name}
                                      onChange={(e) =>
                                        updateProperty(idoIndex, propIndex, {
                                          name: e.target.value,
                                        })
                                      }
                                      placeholder="PropertyName"
                                      className="h-8 font-mono text-xs"
                                    />
                                  </td>
                                  <td className="p-2">
                                    <Input
                                      value={prop.alias || ""}
                                      onChange={(e) =>
                                        updateProperty(idoIndex, propIndex, {
                                          alias: e.target.value,
                                        })
                                      }
                                      placeholder="alias"
                                      className="h-8 text-xs"
                                    />
                                  </td>
                                  <td className="p-2">
                                    <Select
                                      value={prop.type}
                                      onValueChange={(v) =>
                                        updateProperty(idoIndex, propIndex, { type: v })
                                      }
                                    >
                                      <SelectTrigger className="h-8 text-xs">
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {PROPERTY_TYPES.map((t) => (
                                          <SelectItem key={t} value={t}>
                                            {t}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </td>
                                  <td className="p-2">
                                    <div className="flex gap-1">
                                      <Badge
                                        variant={prop.primary_key ? "default" : "outline"}
                                        className="text-[10px] cursor-pointer"
                                        onClick={() =>
                                          updateProperty(idoIndex, propIndex, {
                                            primary_key: !prop.primary_key,
                                          })
                                        }
                                      >
                                        PK
                                      </Badge>
                                      <Badge
                                        variant={prop.filterable ? "default" : "outline"}
                                        className="text-[10px] cursor-pointer"
                                        onClick={() =>
                                          updateProperty(idoIndex, propIndex, {
                                            filterable: !prop.filterable,
                                          })
                                        }
                                      >
                                        F
                                      </Badge>
                                      <Badge
                                        variant={prop.sortable ? "default" : "outline"}
                                        className="text-[10px] cursor-pointer"
                                        onClick={() =>
                                          updateProperty(idoIndex, propIndex, {
                                            sortable: !prop.sortable,
                                          })
                                        }
                                      >
                                        S
                                      </Badge>
                                    </div>
                                  </td>
                                  <td className="p-2">
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-7 w-7 text-destructive"
                                      onClick={() => removeProperty(idoIndex, propIndex)}
                                    >
                                      <Trash2 className="w-3 h-3" />
                                    </Button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Join SQL Tab */}
        <TabsContent value="join-sql">
          <Card>
            <CardHeader>
              <CardTitle>Join SQL</CardTitle>
              <CardDescription>
                Custom SQL for joining IDOs in DuckDB staging. Use table aliases
                from your IDO configurations.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={config.join_sql || ""}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, join_sql: e.target.value }))
                }
                placeholder={`SELECT 
  jr.Job as job_number,
  jr.Wc as work_center,
  j.Item as item_number
FROM job_routes jr
INNER JOIN jobs j ON jr.Job = j.Job`}
                rows={15}
                className="font-mono text-sm"
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* MCP Tools Tab */}
        <TabsContent value="tools">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>MCP Tools</CardTitle>
                  <CardDescription>
                    AI-callable tools exposed by this connector
                  </CardDescription>
                </div>
                <Button onClick={addTool} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Tool
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {config.tools.length === 0 && (
                <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
                  <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No tools configured. Add a tool to define the AI interface.</p>
                </div>
              )}

              {config.tools.map((tool, toolIndex) => (
                <Card key={toolIndex} className="border-2">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <Input
                        value={tool.name}
                        onChange={(e) =>
                          updateTool(toolIndex, { name: e.target.value })
                        }
                        placeholder="tool_name (snake_case)"
                        className="max-w-[250px] font-mono"
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive"
                        onClick={() => removeTool(toolIndex)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Description (for AI)</Label>
                      <Textarea
                        value={tool.description}
                        onChange={(e) =>
                          updateTool(toolIndex, { description: e.target.value })
                        }
                        placeholder="Describe what this tool does for the AI..."
                        rows={2}
                      />
                    </div>

                    <Separator />

                    {/* Parameters */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Parameters ({tool.parameters.length})</Label>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => addToolParam(toolIndex)}
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          Add Parameter
                        </Button>
                      </div>

                      {tool.parameters.length > 0 && (
                        <div className="space-y-2">
                          {tool.parameters.map((param, paramIndex) => (
                            <div
                              key={paramIndex}
                              className="flex gap-2 items-start border p-3 rounded-lg"
                            >
                              <Input
                                value={param.name}
                                onChange={(e) =>
                                  updateToolParam(toolIndex, paramIndex, {
                                    name: e.target.value,
                                  })
                                }
                                placeholder="param_name"
                                className="max-w-[150px] font-mono text-sm"
                              />
                              <Select
                                value={param.type}
                                onValueChange={(v) =>
                                  updateToolParam(toolIndex, paramIndex, { type: v })
                                }
                              >
                                <SelectTrigger className="w-[100px]">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {PROPERTY_TYPES.map((t) => (
                                    <SelectItem key={t} value={t}>
                                      {t}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              <Input
                                value={param.description}
                                onChange={(e) =>
                                  updateToolParam(toolIndex, paramIndex, {
                                    description: e.target.value,
                                  })
                                }
                                placeholder="Parameter description..."
                                className="flex-1 text-sm"
                              />
                              <Badge
                                variant={param.required ? "default" : "outline"}
                                className="cursor-pointer"
                                onClick={() =>
                                  updateToolParam(toolIndex, paramIndex, {
                                    required: !param.required,
                                  })
                                }
                              >
                                {param.required ? "Required" : "Optional"}
                              </Badge>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-destructive"
                                onClick={() => removeToolParam(toolIndex, paramIndex)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
