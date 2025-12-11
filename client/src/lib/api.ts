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

// Bedrock Schedule Types
export interface BedrockJob {
  job: string;
  suffix: number;
  item: string;
  item_description: string;
  qty_released: number;
  qty_complete: number;
  pct_complete: number;
  status: string;
  customer_num: string | null;
  customer_name: string | null;
  operations: BedrockOperation[];
}

export interface BedrockOperation {
  operation_num: number;
  work_center: string;
  qty_complete: number;
  qty_scrapped?: number;
}

export interface BedrockScheduleResponse {
  success: boolean;
  data: {
    total_jobs: number;
    active_jobs: number;
    jobs_by_status: Record<string, number>;
    work_centers: string[];
    jobs: BedrockJob[];
    fetched_at: string;
  };
}

export interface BedrockHealthResponse {
  status: string;
  connected: boolean;
  work_centers_available?: number;
  error?: string;
}

export interface BedrockWorkCenterQueue {
  success: boolean;
  work_center: string;
  operation_count: number;
  queue: {
    job: string;
    suffix: number;
    operation_num: number;
    work_center: string;
    item: string;
    qty_released: number;
    qty_complete: number;
    job_status: string;
  }[];
}

// Bedrock Customer Types
export interface BedrockCustomer {
  cust_num: string;
  name: string;
  addr1: string | null;
  addr2: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  country: string | null;
  phone: string | null;
  contact: string | null;
  email: string | null;
  cust_type: string | null;
  status: string;
}

export interface BedrockCustomerSearchResponse {
  success: boolean;
  data: {
    total_count: number;
    customers: BedrockCustomer[];
    fetched_at: string;
  };
}

// Flow Optimizer Types (matches OPEN ORDERS V5 schema)
export interface OpenOrderLine {
  order_num: string;
  order_line: number;
  customer_name: string;
  order_date: string | null;
  due_date: string | null;
  days_until_due: number;
  urgency: "OVERDUE" | "TODAY" | "THIS_WEEK" | "NEXT_WEEK" | "LATER";
  item: string;
  model: string | null;
  item_description: string;
  bed_type: string;
  bed_length: number;
  qty_ordered: number;
  qty_shipped: number;
  qty_remaining: number;
  item_on_hand: number;
  item_at_weld: number;
  item_at_blast: number;
  item_at_paint: number;
  item_at_assy: number;
  item_total_pipeline: number;
  job_numbers: string;
  qty_released: number;
  released_date: string | null;
  line_value: number;
  first_for_item: boolean;
}

export interface FlowOptimizerSummary {
  total_orders: number;
  total_lines: number;
  in_production: number;    // Total WIP at work centers
  ready_to_schedule: number; // Orders without jobs yet
  on_hand: number;           // Finished goods inventory
  weld: number;
  blast: number;
  paint: number;
  assembly: number;
}

export interface FlowOptimizerResponse {
  success: boolean;
  data: {
    summary: FlowOptimizerSummary;
    work_centers: string[];
    order_lines: OpenOrderLine[];
    fetched_at: string;
  };
}

// Order Availability Types (matches TBE_Customer_Order_Availability stored procedure)
export interface OrderAvailabilityLine {
  co_data_id: number;
  co_num: string;
  co_line: number;
  co_release: number;
  customer_name: string;
  order_date: string | null;
  due_date: string | null;
  released_date: string | null;
  weld_fab_completion_date: string | null;
  blast_completion_date: string | null;
  paint_assembly_completion_date: string | null;
  item: string;
  model: string | null;
  item_description: string;
  qty_ordered: number;
  qty_shipped: number;
  qty_remaining: number;
  qty_remaining_covered: number;
  qty_on_hand: number;
  current_on_hand: number;
  qty_nf: number;
  qty_alloc_co: number;
  qty_wip: number;
  qty_released: number;
  total_in_paint: number;
  allocated_from_paint: number;
  total_in_blast: number;
  allocated_from_blast: number;
  total_in_released_weld_fab: number;
  allocated_from_released_weld_fab: number;
  jobs: string;
  line_amount: number;
  is_fully_covered: boolean;
  shortage: number;
  coverage_percentage: number;
}

export interface OrderAvailabilitySummary {
  total_lines: number;
  total_qty_remaining: number;
  total_qty_covered: number;
  total_shortage: number;
  total_line_amount: number;
  lines_fully_covered: number;
  lines_with_shortage: number;
  coverage_percentage: number;
}

export interface OrderAvailabilityResponse {
  success: boolean;
  data: {
    order_lines: OrderAvailabilityLine[];
    summary: OrderAvailabilitySummary;
    fetched_at: string;
  };
}

// Connector Anatomy Types
export interface IDOSpec {
  name: string;
  description: string;
  properties: string[];
  filter: string | null;
  record_cap: number;
}

export interface ConnectorAnatomy {
  name: string;
  description: string;
  data_sources: {
    idos: IDOSpec[];
    total_ido_count: number;
  };
  processing: {
    join_description: string;
    steps: string[];
  };
  expected_volumes: Record<string, number>;
  allocation_logic?: string[];
  calendar_config?: {
    business_days: string;
    friday: string;
    weekend: string;
    holidays_2025: string[];
    completion_estimates: Record<string, string>;
  };
}

export interface IDOCallMetric {
  ido_name: string;
  properties_count: number;
  filter_expression: string | null;
  record_cap: number;
  records_returned: number;
  duration_ms: number;
  success: boolean;
  error: string | null;
}

export interface ConnectorRunSummary {
  total_api_calls: number;
  parallel_batches: number;
  max_concurrent: number;
  total_records_fetched: number;
  output_records: number;
  api_time_ms: number;
  processing_time_ms: number;
  total_time_ms: number;
}

export interface ConnectorRunMetric {
  connector_name: string;
  run_id: string;
  started_at: string;
  completed_at: string | null;
  ido_calls: IDOCallMetric[];
  summary: ConnectorRunSummary;
  filters: Record<string, unknown>;
  success: boolean;
  error: string | null;
}

export interface ConnectorMetricsStats {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  timing?: {
    avg_total_ms: number;
    avg_api_ms: number;
    min_total_ms: number;
    max_total_ms: number;
  };
  records?: {
    avg_output: number;
    avg_api_calls: number;
  };
  ido_stats?: Record<string, {
    call_count: number;
    total_records: number;
    total_duration_ms: number;
    avg_records: number;
    avg_duration_ms: number;
  }>;
  last_run?: ConnectorRunMetric;
}

export interface ConnectorAnatomyResponse {
  success: boolean;
  data: {
    connector: ConnectorAnatomy;
    metrics: ConnectorMetricsStats;
  };
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

  bedrock: {
    health: async (): Promise<BedrockHealthResponse> => {
      const response = await fetch(`${API_BASE}/bedrock/health`);
      return handleResponse<BedrockHealthResponse>(response);
    },

    schedule: async (includeComplete = true, limit = 100): Promise<BedrockScheduleResponse> => {
      const params = new URLSearchParams({
        include_complete: String(includeComplete),
        limit: String(limit),
      });
      const response = await fetch(`${API_BASE}/bedrock/schedule?${params}`);
      return handleResponse<BedrockScheduleResponse>(response);
    },

    workCenters: async (): Promise<{ success: boolean; work_centers: string[]; count: number }> => {
      const response = await fetch(`${API_BASE}/bedrock/work-centers`);
      return handleResponse<{ success: boolean; work_centers: string[]; count: number }>(response);
    },

    workCenterQueue: async (workCenter: string, limit = 50): Promise<BedrockWorkCenterQueue> => {
      const response = await fetch(
        `${API_BASE}/bedrock/schedule/work-center/${encodeURIComponent(workCenter)}/queue?limit=${limit}`
      );
      return handleResponse<BedrockWorkCenterQueue>(response);
    },

    job: async (jobNumber: string, suffix = 0): Promise<{ success: boolean; job: BedrockJob }> => {
      const response = await fetch(
        `${API_BASE}/bedrock/job/${encodeURIComponent(jobNumber)}?suffix=${suffix}`
      );
      return handleResponse<{ success: boolean; job: BedrockJob }>(response);
    },

    // Customer Search
    customers: async (params: {
      search?: string;
      customer_number?: string;
      city?: string;
      state?: string;
      status?: string;
      limit?: number;
    } = {}): Promise<BedrockCustomerSearchResponse> => {
      const searchParams = new URLSearchParams();
      if (params.search) searchParams.set("search", params.search);
      if (params.customer_number) searchParams.set("customer_number", params.customer_number);
      if (params.city) searchParams.set("city", params.city);
      if (params.state) searchParams.set("state", params.state);
      if (params.status) searchParams.set("status", params.status);
      if (params.limit) searchParams.set("limit", String(params.limit));
      
      const response = await fetch(`${API_BASE}/bedrock/customers?${searchParams}`);
      return handleResponse<BedrockCustomerSearchResponse>(response);
    },

    customer: async (customerNumber: string): Promise<{ success: boolean; customer: BedrockCustomer }> => {
      const response = await fetch(
        `${API_BASE}/bedrock/customers/${encodeURIComponent(customerNumber)}`
      );
      return handleResponse<{ success: boolean; customer: BedrockCustomer }>(response);
    },

    // Flow Optimizer - Open Orders
    openOrders: async (limit = 500): Promise<FlowOptimizerResponse> => {
      const response = await fetch(`${API_BASE}/bedrock/open-orders?limit=${limit}`);
      return handleResponse<FlowOptimizerResponse>(response);
    },

    // Order Availability
    orderAvailability: async (params: {
      customer?: string;
      item?: string;
      shortage_only?: boolean;
      limit?: number;
    } = {}): Promise<OrderAvailabilityResponse> => {
      const searchParams = new URLSearchParams();
      if (params.customer) searchParams.set("customer", params.customer);
      if (params.item) searchParams.set("item", params.item);
      if (params.shortage_only) searchParams.set("shortage_only", String(params.shortage_only));
      if (params.limit) searchParams.set("limit", String(params.limit));
      
      const response = await fetch(`${API_BASE}/bedrock/order-availability?${searchParams}`);
      return handleResponse<OrderAvailabilityResponse>(response);
    },

    // Connector Anatomy
    orderAvailabilityAnatomy: async (): Promise<ConnectorAnatomyResponse> => {
      const response = await fetch(`${API_BASE}/bedrock/order-availability/anatomy`);
      return handleResponse<ConnectorAnatomyResponse>(response);
    },

    connectorAnatomy: async (connectorId: string): Promise<ConnectorAnatomyResponse> => {
      const response = await fetch(`${API_BASE}/bedrock/connector/${connectorId}/anatomy`);
      return handleResponse<ConnectorAnatomyResponse>(response);
    },
  },
};
