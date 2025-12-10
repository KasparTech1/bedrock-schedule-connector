import { Route, Switch } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "@/components/Layout";
import { Library } from "@/pages/Library";
import { Connectors } from "@/pages/admin/Connectors";
import { ConnectorDetail } from "@/pages/ConnectorDetail";
import { ConnectorBuilder } from "@/pages/admin/ConnectorBuilder";
import { Connections } from "@/pages/admin/Connections";
import { DemoTryIt } from "@/pages/DemoTryIt";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Switch>
          <Route path="/" component={Library} />
          <Route path="/admin/connectors" component={Connectors} />
          <Route path="/admin/connectors/new">
            <ConnectorBuilder />
          </Route>
          <Route path="/admin/connectors/:id/edit">
            {(params) => <ConnectorBuilder id={params.id} />}
          </Route>
          <Route path="/admin/connections" component={Connections} />
          <Route path="/admin/settings">
            <div className="text-center py-12">
              <h1 className="text-2xl font-semibold">Settings</h1>
              <p className="text-muted-foreground mt-2">Coming soon...</p>
            </div>
          </Route>
          <Route path="/connector/:id">
            {(params) => <ConnectorDetail id={params.id} />}
          </Route>
          <Route path="/connector/demo-syteline-items/try" component={DemoTryIt} />
          <Route>
            <div className="text-center py-12">
              <h1 className="text-2xl font-semibold">404 - Not Found</h1>
              <p className="text-muted-foreground mt-2">
                The page you're looking for doesn't exist.
              </p>
            </div>
          </Route>
        </Switch>
      </Layout>
    </QueryClientProvider>
  );
}

export default App;
