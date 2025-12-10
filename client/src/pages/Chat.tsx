import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  MessageSquare,
  Send,
  Loader2,
  Trash2,
  Bot,
  User,
  AlertCircle,
  CheckCircle2,
  Settings,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

interface ChatMessage {
  role: string;
  content: string;
  timestamp: string;
}

interface OllamaStatus {
  available: boolean;
  base_url: string;
  model: string;
  models_installed: string[] | null;
  error: string | null;
}

export function Chat() {
  const [message, setMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check Ollama status
  const statusQuery = useQuery<OllamaStatus>({
    queryKey: ["ollama-status"],
    queryFn: async () => {
      const res = await fetch("/api/chat/status");
      if (!res.ok) throw new Error("Failed to check status");
      return res.json();
    },
    refetchInterval: 30000,
  });

  // Get chat history
  const historyQuery = useQuery<ChatMessage[]>({
    queryKey: ["chat-history"],
    queryFn: async () => {
      const res = await fetch("/api/chat/history");
      if (!res.ok) throw new Error("Failed to get history");
      return res.json();
    },
  });

  // Send message mutation
  const sendMutation = useMutation({
    mutationFn: async (msg: string) => {
      const res = await fetch("/api/chat/send-simple", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      if (!res.ok) throw new Error("Failed to send message");
      return res.json();
    },
    onSuccess: () => {
      historyQuery.refetch();
    },
  });

  // Clear history mutation
  const clearMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch("/api/chat/clear", { method: "POST" });
      if (!res.ok) throw new Error("Failed to clear history");
      return res.json();
    },
    onSuccess: () => {
      historyQuery.refetch();
    },
  });

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [historyQuery.data]);

  const handleSend = () => {
    if (!message.trim() || sendMutation.isPending) return;
    sendMutation.mutate(message);
    setMessage("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <MessageSquare className="w-8 h-8" />
            ERP Chat Assistant
          </h1>
          <p className="text-muted-foreground mt-1">
            Chat with your ERP data using AI
          </p>
        </div>
        <div className="flex items-center gap-2">
          {statusQuery.data?.available ? (
            <Badge className="bg-green-500">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              {statusQuery.data.model}
            </Badge>
          ) : (
            <Badge variant="destructive">
              <AlertCircle className="w-3 h-3 mr-1" />
              LLM Offline
            </Badge>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => clearMutation.mutate()}
            disabled={clearMutation.isPending}
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Clear
          </Button>
        </div>
      </div>

      {/* Status Card (if offline) */}
      {!statusQuery.data?.available && (
        <Card className="mb-4 border-amber-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-amber-600 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Local LLM Not Available
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-2">
              {statusQuery.data?.error || "Ollama is not running"}
            </p>
            <p className="text-sm">To start Ollama:</p>
            <pre className="bg-muted p-2 rounded text-xs mt-2">
{`# Start Ollama container
docker-compose --profile llm up -d

# Pull a small model
docker exec kai-ollama ollama pull llama3.2:1b`}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Messages */}
      <Card className="flex-1 overflow-hidden flex flex-col">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {historyQuery.data?.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium">Start a conversation</p>
              <p className="text-sm mt-1">
                Ask about items, customers, inventory, or any ERP data
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {[
                  "Show me the first 5 items",
                  "What products do we have?",
                  "Find items starting with 30",
                ].map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setMessage(suggestion);
                    }}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {historyQuery.data?.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role !== "user" && (
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                <p className="text-xs opacity-60 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}

          {sendMutation.isPending && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <div className="bg-muted rounded-lg p-3">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        {/* Input */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                statusQuery.data?.available
                  ? "Ask about items, customers, inventory..."
                  : "Start Ollama to enable chat"
              }
              disabled={!statusQuery.data?.available || sendMutation.isPending}
              className="resize-none"
              rows={2}
            />
            <Button
              onClick={handleSend}
              disabled={
                !message.trim() ||
                !statusQuery.data?.available ||
                sendMutation.isPending
              }
              className="px-6"
            >
              {sendMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          {statusQuery.data?.models_installed && (
            <p className="text-xs text-muted-foreground mt-2">
              Available models: {statusQuery.data.models_installed.join(", ")}
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
