import { useState } from "react";
import { Link, useLocation } from "wouter";
import {
  Library,
  Puzzle,
  Database,
  Settings,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  section?: string;
}

const navItems: NavItem[] = [
  { title: "Connector Library", href: "/", icon: Library, section: "Browse" },
  { title: "Connectors", href: "/admin/connectors", icon: Puzzle, section: "Admin" },
  { title: "Connections", href: "/admin/connections", icon: Database, section: "Admin" },
  { title: "Settings", href: "/admin/settings", icon: Settings, section: "Admin" },
];

export function AppSidebar() {
  const [location] = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
  };

  const browseItems = navItems.filter((item) => item.section === "Browse");
  const adminItems = navItems.filter((item) => item.section === "Admin");

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex flex-col h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300",
          collapsed ? "w-[var(--sidebar-width-icon)]" : "w-[var(--sidebar-width)]"
        )}
      >
        {/* Logo */}
        <div className="flex items-center h-16 px-4 border-b border-sidebar-border">
          <Link href="/" className="flex items-center gap-3">
            <img
              src="/favicon.png"
              alt="KAI"
              className="w-8 h-8"
            />
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-semibold text-sidebar-foreground">
                  KAI ERP
                </span>
                <span className="text-xs text-muted-foreground">
                  Connector Catalog
                </span>
              </div>
            )}
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 overflow-y-auto">
          {/* Browse Section */}
          {!collapsed && (
            <div className="px-4 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Browse
            </div>
          )}
          <div className="space-y-1 px-2">
            {browseItems.map((item) => (
              <NavLink
                key={item.href}
                item={item}
                isActive={location === item.href}
                collapsed={collapsed}
              />
            ))}
          </div>

          <Separator className="my-4" />

          {/* Admin Section */}
          {!collapsed && (
            <div className="px-4 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Admin
            </div>
          )}
          <div className="space-y-1 px-2">
            {adminItems.map((item) => (
              <NavLink
                key={item.href}
                item={item}
                isActive={location === item.href || location.startsWith(item.href + "/")}
                collapsed={collapsed}
              />
            ))}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-2 border-t border-sidebar-border space-y-1">
          {/* Dark Mode Toggle */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "default"}
                className={cn(
                  "w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent",
                  collapsed && "justify-center"
                )}
                onClick={toggleDarkMode}
              >
                {darkMode ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
                {!collapsed && (
                  <span className="ml-2">
                    {darkMode ? "Light Mode" : "Dark Mode"}
                  </span>
                )}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">
                {darkMode ? "Light Mode" : "Dark Mode"}
              </TooltipContent>
            )}
          </Tooltip>

          {/* Collapse Toggle */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "default"}
                className={cn(
                  "w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent",
                  collapsed && "justify-center"
                )}
                onClick={() => setCollapsed(!collapsed)}
              >
                {collapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
                {!collapsed && <span className="ml-2">Collapse</span>}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">
                Expand Sidebar
              </TooltipContent>
            )}
          </Tooltip>
        </div>
      </aside>
    </TooltipProvider>
  );
}

function NavLink({
  item,
  isActive,
  collapsed,
}: {
  item: NavItem;
  isActive: boolean;
  collapsed: boolean;
}) {
  const Icon = item.icon;

  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Link href={item.href}>
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "w-full text-sidebar-foreground",
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary"
                  : "hover:bg-sidebar-accent"
              )}
            >
              <Icon className="h-4 w-4" />
            </Button>
          </Link>
        </TooltipTrigger>
        <TooltipContent side="right">{item.title}</TooltipContent>
      </Tooltip>
    );
  }

  return (
    <Link href={item.href}>
      <Button
        variant="ghost"
        className={cn(
          "w-full justify-start text-sidebar-foreground",
          isActive
            ? "bg-sidebar-accent text-sidebar-primary"
            : "hover:bg-sidebar-accent"
        )}
      >
        <Icon className="h-4 w-4 mr-3" />
        {item.title}
      </Button>
    </Link>
  );
}
