import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Settings as SettingsIcon,
  Database,
  Server,
  Palette,
  FlaskConical,
  FolderCog,
  Save,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Loader2,
  Eye,
  EyeOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface AppSettings {
  // SyteLine Connection
  syteline: {
    baseUrl: string;
    configName: string;
    username: string;
    password: string;
    timeout: number;
  };
  // Demo Environment
  demo: {
    enabled: boolean;
    baseUrl: string;
    configName: string;
    username: string;
    password: string;
  };
  // Registry
  registry: {
    configDirectory: string;
    autoPublish: boolean;
  };
  // Test Database
  testDb: {
    databasePath: string;
    autoSeed: boolean;
  };
  // Appearance
  appearance: {
    theme: "light" | "dark" | "system";
    sidebarDefault: "expanded" | "collapsed";
  };
}

const DEFAULT_SETTINGS: AppSettings = {
  syteline: {
    baseUrl: "",
    configName: "",
    username: "",
    password: "",
    timeout: 30,
  },
  demo: {
    enabled: true,
    baseUrl: "https://Csi10g.erpsl.inforcloudsuite.com",
    configName: "DUU6QAFE74D2YDYW_TST_DALS",
    username: "",
    password: "",
  },
  registry: {
    configDirectory: "src/kai_erp/connectors_config",
    autoPublish: false,
  },
  testDb: {
    databasePath: "test_database.db",
    autoSeed: true,
  },
  appearance: {
    theme: "system",
    sidebarDefault: "expanded",
  },
};

export function Settings() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [showPasswords, setShowPasswords] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("kai-erp-settings");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      } catch {
        // Use defaults if parsing fails
      }
    }
  }, []);

  // Test SyteLine connection
  const testConnectionMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch("/api/demo/health");
      if (!res.ok) throw new Error("Connection failed");
      return res.json();
    },
  });

  // Update a nested setting
  const updateSetting = <K extends keyof AppSettings>(
    section: K,
    key: keyof AppSettings[K],
    value: AppSettings[K][keyof AppSettings[K]]
  ) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
    setHasChanges(true);
    setSavedMessage(null);
  };

  // Save settings
  const handleSave = () => {
    localStorage.setItem("kai-erp-settings", JSON.stringify(settings));
    setHasChanges(false);
    setSavedMessage("Settings saved successfully!");
    setTimeout(() => setSavedMessage(null), 3000);
  };

  // Reset to defaults
  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    setHasChanges(true);
    setSavedMessage(null);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <SettingsIcon className="w-8 h-8" />
            Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure connector catalog and connection settings
          </p>
        </div>
        <div className="flex items-center gap-2">
          {savedMessage && (
            <Badge className="bg-green-500">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              {savedMessage}
            </Badge>
          )}
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges}>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      {/* SyteLine Connection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            SyteLine Connection
          </CardTitle>
          <CardDescription>
            Configure your primary SyteLine 10 CloudSuite connection
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sl-baseUrl">Base URL</Label>
              <Input
                id="sl-baseUrl"
                placeholder="https://your-instance.inforcloudsuite.com"
                value={settings.syteline.baseUrl}
                onChange={(e) => updateSetting("syteline", "baseUrl", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sl-configName">Config Name</Label>
              <Input
                id="sl-configName"
                placeholder="TENANT_ENV_DB"
                value={settings.syteline.configName}
                onChange={(e) => updateSetting("syteline", "configName", e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sl-username">Username</Label>
              <Input
                id="sl-username"
                placeholder="API username"
                value={settings.syteline.username}
                onChange={(e) => updateSetting("syteline", "username", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sl-password">Password</Label>
              <div className="relative">
                <Input
                  id="sl-password"
                  type={showPasswords ? "text" : "password"}
                  placeholder="API password"
                  value={settings.syteline.password}
                  onChange={(e) => updateSetting("syteline", "password", e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowPasswords(!showPasswords)}
                >
                  {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sl-timeout">Timeout (seconds)</Label>
              <Input
                id="sl-timeout"
                type="number"
                min="5"
                max="300"
                value={settings.syteline.timeout}
                onChange={(e) => updateSetting("syteline", "timeout", parseInt(e.target.value) || 30)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Demo Environment */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5" />
            Demo Environment
          </CardTitle>
          <CardDescription>
            Kaspar Development Workshop test environment for demos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div>
              <p className="font-medium">Enable Demo Mode</p>
              <p className="text-sm text-muted-foreground">
                Use the demo environment for testing connectors
              </p>
            </div>
            <Select
              value={settings.demo.enabled ? "enabled" : "disabled"}
              onValueChange={(v) => updateSetting("demo", "enabled", v === "enabled")}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="enabled">Enabled</SelectItem>
                <SelectItem value="disabled">Disabled</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {settings.demo.enabled && (
            <>
              <Separator />
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="demo-baseUrl">Base URL</Label>
                  <Input
                    id="demo-baseUrl"
                    value={settings.demo.baseUrl}
                    onChange={(e) => updateSetting("demo", "baseUrl", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="demo-configName">Config Name</Label>
                  <Input
                    id="demo-configName"
                    value={settings.demo.configName}
                    onChange={(e) => updateSetting("demo", "configName", e.target.value)}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="demo-username">Username</Label>
                  <Input
                    id="demo-username"
                    value={settings.demo.username}
                    onChange={(e) => updateSetting("demo", "username", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="demo-password">Password</Label>
                  <Input
                    id="demo-password"
                    type={showPasswords ? "text" : "password"}
                    value={settings.demo.password}
                    onChange={(e) => updateSetting("demo", "password", e.target.value)}
                  />
                </div>
              </div>
              <Button
                variant="outline"
                onClick={() => testConnectionMutation.mutate()}
                disabled={testConnectionMutation.isPending}
              >
                {testConnectionMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : testConnectionMutation.isSuccess ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2 text-green-500" />
                    Connected
                  </>
                ) : testConnectionMutation.isError ? (
                  <>
                    <XCircle className="w-4 h-4 mr-2 text-red-500" />
                    Failed - Retry
                  </>
                ) : (
                  "Test Connection"
                )}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Registry Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderCog className="w-5 h-5" />
            Connector Registry
          </CardTitle>
          <CardDescription>
            Configure connector configuration storage
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="registry-dir">Config Directory</Label>
            <Input
              id="registry-dir"
              value={settings.registry.configDirectory}
              onChange={(e) => updateSetting("registry", "configDirectory", e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Path to YAML connector configuration files
            </p>
          </div>
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div>
              <p className="font-medium">Auto-publish New Connectors</p>
              <p className="text-sm text-muted-foreground">
                New connectors are published by default
              </p>
            </div>
            <Select
              value={settings.registry.autoPublish ? "yes" : "no"}
              onValueChange={(v) => updateSetting("registry", "autoPublish", v === "yes")}
            >
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="yes">Yes</SelectItem>
                <SelectItem value="no">No</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Test Database */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Test Database
          </CardTitle>
          <CardDescription>
            Local SQLite database for testing connectors
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="testdb-path">Database Path</Label>
            <Input
              id="testdb-path"
              value={settings.testDb.databasePath}
              onChange={(e) => updateSetting("testDb", "databasePath", e.target.value)}
            />
          </div>
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div>
              <p className="font-medium">Auto-seed on Startup</p>
              <p className="text-sm text-muted-foreground">
                Populate sample data when server starts
              </p>
            </div>
            <Select
              value={settings.testDb.autoSeed ? "yes" : "no"}
              onValueChange={(v) => updateSetting("testDb", "autoSeed", v === "yes")}
            >
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="yes">Yes</SelectItem>
                <SelectItem value="no">No</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Appearance
          </CardTitle>
          <CardDescription>
            Customize the look and feel
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Theme</Label>
              <Select
                value={settings.appearance.theme}
                onValueChange={(v) => updateSetting("appearance", "theme", v as "light" | "dark" | "system")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Sidebar Default</Label>
              <Select
                value={settings.appearance.sidebarDefault}
                onValueChange={(v) => updateSetting("appearance", "sidebarDefault", v as "expanded" | "collapsed")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="expanded">Expanded</SelectItem>
                  <SelectItem value="collapsed">Collapsed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
