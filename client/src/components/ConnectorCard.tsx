import { Link } from "wouter";
import { Factory, ShoppingCart, Users, Package, ExternalLink } from "lucide-react";
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
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  factory: Factory,
  "shopping-cart": ShoppingCart,
  users: Users,
  package: Package,
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
}: ConnectorCardProps) {
  const Icon = iconMap[icon] || Factory;

  return (
    <Card className="hover-elevate cursor-pointer active-elevate-2 transition-all">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
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
          {status === "draft" && (
            <Badge variant="outline" className="text-xs">
              Draft
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <CardDescription className="line-clamp-2">{description}</CardDescription>
        
        {/* Tags */}
        <div className="flex flex-wrap gap-1">
          {tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs font-normal">
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
