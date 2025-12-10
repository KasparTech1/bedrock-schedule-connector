import { Route, Switch } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "@/components/Layout";
import { Library } from "@/pages/Library";
import { Connectors } from "@/pages/admin/Connectors";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Switch>
          <Route path="/" component={Library} />
          <Route path="/admin/connectors" component={Connectors} />
          <Route path="/admin/connectors/new">
            <div className="text-center py-12">
              <h1 className="text-2xl font-semibold">Create New Connector</h1>
              <p className="text-muted-foreground mt-2">Coming soon...</p>
            </div>
          </Route>
          <Route path="/admin/connections">
            <div className="text-center py-12">
              <h1 className="text-2xl font-semibold">Connections</h1>
              <p className="text-muted-foreground mt-2">Coming soon...</p>
            </div>
          </Route>
          <Route path="/admin/settings">
            <div className="text-center py-12">
              <h1 className="text-2xl font-semibold">Settings</h1>
              <p className="text-muted-foreground mt-2">Coming soon...</p>
            </div>
          </Route>
          <Route path="/connector/:id">
            {(params) => (
              <div className="text-center py-12">
                <h1 className="text-2xl font-semibold">
                  Connector: {params.id}
                </h1>
                <p className="text-muted-foreground mt-2">
                  Detail page coming soon...
                </p>
              </div>
            )}
          </Route>
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
