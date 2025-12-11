import { Link } from "wouter";
import { Factory, ShoppingCart, Users, Package, ExternalLink, Zap, Circle, Construction, Archive } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface ConnectorCardProps {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  tags: string[];
  icon?: string;
  status?: string;
  isLive?: boolean;
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  factory: Factory,
  "shopping-cart": ShoppingCart,
  users: Users,
  package: Package,
  zap: Zap,
};

export function ConnectorCard({
  id,
  name,
  description,
  category,
  version,
  tags,
  icon = "factory",
  status = "published",
  isLive = false,
}: ConnectorCardProps) {
  const Icon = iconMap[icon] || Factory;

  // Determine if this is a live connector (DEMO or explicitly marked)
  const isLiveConnector = isLive || category === "Demo" || tags.includes("live");
  
  // Determine if this is a legacy connector
  const isLegacyConnector = tags.includes("LEGACY") || category === "Legacy";

  return (
    <Card className={`hover-elevate cursor-pointer active-elevate-2 transition-all ${isLiveConnector ? "border-green-500/50 ring-1 ring-green-500/20" : isLegacyConnector ? "border-amber-500/50 ring-1 ring-amber-500/20" : ""}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isLiveConnector ? "bg-green-500/10 text-green-600" : isLegacyConnector ? "bg-amber-500/10 text-amber-600" : "bg-primary/10 text-primary"}`}>
              <Icon className="w-6 h-6" />
            </div>
            <div>
              <CardTitle className="text-lg">{name}</CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="secondary" className="text-xs">
                  {category}
                </Badge>
                <span className="text-xs text-muted-foreground">v{version}</span>
              </div>
            </div>
          </div>
          {/* Status Badge */}
          {isLegacyConnector ? (
            <Badge className="bg-amber-100 text-amber-700 border border-amber-300 hover:bg-amber-200 text-xs">
              <Archive className="w-3 h-3 mr-1" />
              LEGACY
            </Badge>
          ) : isLiveConnector ? (
            <Badge className="bg-green-500 hover:bg-green-600 text-xs">
              <Circle className="w-2 h-2 mr-1 fill-current animate-pulse" />
              LIVE
            </Badge>
          ) : status === "draft" ? (
            <Badge variant="outline" className="text-xs">
              Draft
            </Badge>
          ) : (
            <Badge className="bg-amber-500 hover:bg-amber-600 text-xs">
              <Construction className="w-3 h-3 mr-1" />
              In Progress
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <CardDescription className="line-clamp-2">{description}</CardDescription>
        
        {/* Tags */}
        <div className="flex flex-wrap gap-1">
          {tags.slice(0, 3).map((tag) => (
            <Badge 
              key={tag} 
              variant="outline" 
              className={`text-xs font-normal ${tag === "LEGACY" ? "bg-amber-50 text-amber-700 border-amber-200" : ""}`}
            >
              {tag}
            </Badge>
          ))}
          {tags.length > 3 && (
            <Badge variant="outline" className="text-xs font-normal">
              +{tags.length - 3}
            </Badge>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Link href={`/connector/${id}`} className="flex-1">
            <Button variant="outline" className="w-full" size="sm">
              View Details
            </Button>
          </Link>
          <Link href={`/connector/${id}/try`}>
            <Button size="sm">
              Try It
              <ExternalLink className="w-3 h-3 ml-1" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
