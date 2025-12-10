/**
 * API client for KAI ERP Connector Catalog
 */

const API_BASE = "/api";

export interface ConnectorSummary {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  icon: string;
  tags: string[];
  status: string;
  tools_count: number;
}

export interface PropertyConfig {
  name: string;
  alias?: string;
  type: string;
  description?: string;
  filterable: boolean;
  sortable: boolean;
  primary_key: boolean;
}

export interface IDOConfig {
  name: string;
  alias?: string;
  description?: string;
  properties: PropertyConfig[];
  default_filter?: string;
}

export interface JoinConfig {
  type: string;
  left_ido: string;
  right_ido: string;
  left_key: string;
  right_key: string;
}

export interface ToolParameterConfig {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: string;
  enum?: string[];
}

export interface ToolConfig {
  name: string;
  description: string;
  parameters: ToolParameterConfig[];
}

export interface ConnectorConfig {
  id: string;
  name: string;
  description: string;
  version: string;
  category: string;
  icon: string;
  tags: string[];
  status: string;
  idos: IDOConfig[];
  joins: JoinConfig[];
  join_sql?: string;
  output_fields: PropertyConfig[];
  tools: ToolConfig[];
  estimated_volume: string;
  freshness_requirement: string;
}

export interface TestDbStatus {
  connected: boolean;
  db_path: string;
  tables: Record<string, number>;
  total_records: number;
}

export interface TestDbQueryResult {
  ido: string;
  records: Record<string, unknown>[];
  count: number;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "API request failed");
  }
  return response.json();
}

export const api = {
  connectors: {
    list: async (publishedOnly = false): Promise<ConnectorSummary[]> => {
      const url = `${API_BASE}/connectors/?published_only=${publishedOnly}`;
      const response = await fetch(url);
      return handleResponse<ConnectorSummary[]>(response);
    },

    get: async (id: string): Promise<ConnectorConfig> => {
      const response = await fetch(`${API_BASE}/connectors/${id}`);
      return handleResponse<ConnectorConfig>(response);
    },

    create: async (config: ConnectorConfig): Promise<ConnectorConfig> => {
      const response = await fetch(`${API_BASE}/connectors/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      return handleResponse<ConnectorConfig>(response);
    },

    update: async (id: string, config: ConnectorConfig): Promise<ConnectorConfig> => {
      const response = await fetch(`${API_BASE}/connectors/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      return handleResponse<ConnectorConfig>(response);
    },

    delete: async (id: string): Promise<void> => {
      const response = await fetch(`${API_BASE}/connectors/${id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || "Delete failed");
      }
    },

    publish: async (id: string): Promise<ConnectorConfig> => {
      const response = await fetch(`${API_BASE}/connectors/${id}/publish`, {
        method: "POST",
      });
      return handleResponse<ConnectorConfig>(response);
    },

    unpublish: async (id: string): Promise<ConnectorConfig> => {
      const response = await fetch(`${API_BASE}/connectors/${id}/unpublish`, {
        method: "POST",
      });
      return handleResponse<ConnectorConfig>(response);
    },

    duplicate: async (id: string, newId: string): Promise<ConnectorConfig> => {
      const response = await fetch(`${API_BASE}/connectors/${id}/duplicate?new_id=${encodeURIComponent(newId)}`, {
        method: "POST",
      });
      return handleResponse<ConnectorConfig>(response);
    },
  },

  testdb: {
    status: async (): Promise<TestDbStatus> => {
      const response = await fetch(`${API_BASE}/testdb/status`);
      return handleResponse<TestDbStatus>(response);
    },

    seed: async (numJobs = 20, numOrders = 15): Promise<{ message: string }> => {
      const response = await fetch(`${API_BASE}/testdb/seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ num_jobs: numJobs, num_orders: numOrders }),
      });
      return handleResponse<{ message: string }>(response);
    },

    clear: async (): Promise<{ message: string }> => {
      const response = await fetch(`${API_BASE}/testdb/clear`, {
        method: "POST",
      });
      return handleResponse<{ message: string }>(response);
    },

    query: async (
      idoName: string,
      properties?: string[],
      filterExpr?: string,
      limit = 100
    ): Promise<TestDbQueryResult> => {
      const response = await fetch(`${API_BASE}/testdb/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ido_name: idoName,
          properties,
          filter_expr: filterExpr,
          limit,
        }),
      });
      return handleResponse<TestDbQueryResult>(response);
    },

    tables: async (): Promise<string[]> => {
      const response = await fetch(`${API_BASE}/testdb/tables`);
      return handleResponse<string[]>(response);
    },

    getTableData: async (tableName: string, limit = 50): Promise<TestDbQueryResult> => {
      const response = await fetch(`${API_BASE}/testdb/tables/${tableName}?limit=${limit}`);
      return handleResponse<TestDbQueryResult>(response);
    },
  },
};
