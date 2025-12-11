import { Route, Switch } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "@/components/Layout";
import { ErrorBoundary, PageErrorBoundary } from "@/components/ErrorBoundary";
import { Library } from "@/pages/Library";
import { Connectors } from "@/pages/admin/Connectors";
import { ConnectorDetail } from "@/pages/ConnectorDetail";
import { ConnectorBuilder } from "@/pages/admin/ConnectorBuilder";
import { Connections } from "@/pages/admin/Connections";
import { Settings } from "@/pages/admin/Settings";
import { Sandbox } from "@/pages/admin/Sandbox";
import { BedrockFlowOptimizer } from "@/pages/BedrockFlowOptimizer";
import { BedrockCustomerSearch } from "@/pages/BedrockCustomerSearch";
import { BedrockOrderAvailability } from "@/pages/BedrockOrderAvailability";
import { APISettings } from "@/pages/APISettings";
import { LegacyConnectors } from "@/pages/LegacyConnectors";

const queryClient = new QueryClient();

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Layout>
          <PageErrorBoundary>
            <Switch>
              <Route path="/" component={Library} />
              <Route path="/legacy" component={LegacyConnectors} />
              <Route path="/admin/connectors" component={Connectors} />
              <Route path="/admin/connectors/new">
                <ConnectorBuilder />
              </Route>
              <Route path="/admin/connectors/:id/edit">
                {(params) => <ConnectorBuilder id={params.id} />}
              </Route>
              <Route path="/admin/connections" component={Connections} />
              <Route path="/admin/sandbox" component={Sandbox} />
              <Route path="/admin/settings" component={Settings} />
              <Route path="/admin/api" component={APISettings} />
              <Route path="/connector/:id">
                {(params) => <ConnectorDetail id={params.id} />}
              </Route>
              <Route path="/connector/bedrock-ops-scheduler/try" component={BedrockFlowOptimizer} />
              <Route path="/connector/customer-search/try" component={BedrockCustomerSearch} />
              {/* Live Tool Connectors */}
              <Route path="/tools/flow-optimizer" component={BedrockFlowOptimizer} />
              <Route path="/tools/customer-search" component={BedrockCustomerSearch} />
              <Route path="/tools/order-availability" component={BedrockOrderAvailability} />
              <Route path="/connector/order-availability/try" component={BedrockOrderAvailability} />
              <Route>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-semibold">404 - Not Found</h1>
                  <p className="text-muted-foreground mt-2">
                    The page you're looking for doesn't exist.
                  </p>
                </div>
              </Route>
            </Switch>
          </PageErrorBoundary>
        </Layout>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
