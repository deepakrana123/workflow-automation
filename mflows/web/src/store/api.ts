import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({ baseUrl: "/api" }),
  tagTypes: ["Workflows", "Executions", "Catalog", "Dashboard", "Traces", "Prompts", "Integrations", "Configurations"],
  endpoints: (builder) => ({
    // ── Dashboard ─────────────────────────────────────────────────────────
    getDashboardStats: builder.query<any, void>({
      query: () => "/dashboard/stats",
      providesTags: ["Dashboard"],
    }),
    getExecutionTrend: builder.query<any[], number>({
      query: (days) => `/dashboard/execution-trend?days=${days}`,
    }),
    getWorkflowUsage: builder.query<any[], void>({
      query: () => "/dashboard/workflow-usage",
    }),

    // ── Workflows ─────────────────────────────────────────────────────────
    getWorkflows: builder.query<any[], string | void>({
      query: (domain) => (domain ? `/workflows?domain=${domain}` : "/workflows"),
      providesTags: ["Workflows"],
    }),
    getWorkflow: builder.query<any, number>({
      query: (id) => `/workflows/${id}`,
    }),
    generateWorkflow: builder.mutation<any, { user_request: string; name: string; domain: string }>({
      query: (body) => ({ url: "/workflows/generate", method: "POST", body }),
      invalidatesTags: ["Workflows"],
    }),

    // ── Execute ───────────────────────────────────────────────────────────
    executeWorkflow: builder.mutation<any, { workflow_id: number; entity_id: string }>({
      query: (body) => ({ url: "/execute/", method: "POST", body }),
      invalidatesTags: ["Executions"],
    }),
    pauseExecution: builder.mutation<any, number>({
      query: (id) => ({ url: `/execute/${id}/pause`, method: "POST" }),
      invalidatesTags: ["Executions"],
    }),
    resumeExecution: builder.mutation<any, number>({
      query: (id) => ({ url: `/execute/${id}/resume`, method: "POST" }),
      invalidatesTags: ["Executions"],
    }),

    // ── Executions ────────────────────────────────────────────────────────
    getExecutions: builder.query<any, { page?: number; page_size?: number; status?: string }>({
      query: (params) => {
        const qs = new URLSearchParams();
        if (params.page) qs.set("page", String(params.page));
        if (params.page_size) qs.set("page_size", String(params.page_size));
        if (params.status && params.status !== "all") qs.set("status", params.status);
        return `/executions?${qs.toString()}`;
      },
      providesTags: ["Executions"],
    }),
    getExecution: builder.query<any, string>({
      query: (id) => `/executions/${id}`,
      providesTags: ["Executions"],
    }),

    // ── Catalog ───────────────────────────────────────────────────────────
    getTriggers: builder.query<any, { page?: number; page_size?: number; search?: string }>({
      query: (params) => {
        const qs = new URLSearchParams();
        if (params.page) qs.set("page", String(params.page));
        if (params.page_size) qs.set("page_size", String(params.page_size));
        if (params.search) qs.set("search", params.search);
        return `/catalog/triggers?${qs.toString()}`;
      },
      providesTags: ["Catalog"],
    }),
    getActions: builder.query<any, { page?: number; page_size?: number; search?: string }>({
      query: (params) => {
        const qs = new URLSearchParams();
        if (params.page) qs.set("page", String(params.page));
        if (params.page_size) qs.set("page_size", String(params.page_size));
        if (params.search) qs.set("search", params.search);
        return `/catalog/actions?${qs.toString()}`;
      },
      providesTags: ["Catalog"],
    }),
    semanticSearch: builder.mutation<any, { query: string; top_k?: number }>({
      query: (body) => ({ url: "/search/semantic", method: "POST", body }),
    }),

    // ── Knowledge Ingestion ───────────────────────────────────────────────
    uploadBRD: builder.mutation<any, FormData>({
      query: (formData) => ({
        url: "/knowledge-ingestion/upload",
        method: "POST",
        body: formData,
      }),
    }),

    // ── Traces ────────────────────────────────────────────────────────────
    getTraces: builder.query<any, { page?: number; page_size?: number; execution_id?: string; status?: string }>({
      query: (params) => {
        const qs = new URLSearchParams();
        if (params.page) qs.set("page", String(params.page));
        if (params.page_size) qs.set("page_size", String(params.page_size));
        if (params.execution_id) qs.set("execution_id", params.execution_id);
        if (params.status) qs.set("status", params.status);
        return `/traces?${qs.toString()}`;
      },
      providesTags: ["Traces"],
    }),

    // ── Prompts ───────────────────────────────────────────────────────────
    getPrompts: builder.query<any[], void>({
      query: () => "/prompts",
      providesTags: ["Prompts"],
    }),
    getPromptStats: builder.query<any[], void>({
      query: () => "/prompts/stats",
    }),
    activatePrompt: builder.mutation<any, { name: string; version: string }>({
      query: ({ name, version }) => ({
        url: `/prompts/${name}/activate`,
        method: "POST",
        body: { version },
      }),
      invalidatesTags: ["Prompts"],
    }),
    rollbackPrompt: builder.mutation<any, string>({
      query: (name) => ({ url: `/prompts/${name}/rollback`, method: "POST" }),
      invalidatesTags: ["Prompts"],
    }),

    // ── Workspace Integrations ────────────────────────────────────────────
    getIntegrations: builder.query<any[], number>({
      query: (workspaceId) => `/workspaces/${workspaceId}/integrations`,
      providesTags: ["Integrations"],
    }),
    createIntegration: builder.mutation<any, { workspaceId: number; body: any }>({
      query: ({ workspaceId, body }) => ({
        url: `/workspaces/${workspaceId}/integrations`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Integrations"],
    }),
    updateIntegration: builder.mutation<any, { id: number; body: any }>({
      query: ({ id, body }) => ({
        url: `/workspace-integrations/${id}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["Integrations"],
    }),
    deleteIntegration: builder.mutation<any, number>({
      query: (id) => ({ url: `/workspace-integrations/${id}`, method: "DELETE" }),
      invalidatesTags: ["Integrations"],
    }),

    // ── Action Configurations ─────────────────────────────────────────────
    getConfigurations: builder.query<any[], number>({
      query: (workflowKnowledgeId) =>
        `/workflows/${workflowKnowledgeId}/action-configurations`,
      providesTags: ["Configurations"],
    }),
    getConfiguration: builder.query<any, number>({
      query: (id) => `/action-configurations/${id}`,
    }),
    updateConfiguration: builder.mutation<any, { id: number; body: any }>({
      query: ({ id, body }) => ({
        url: `/action-configurations/${id}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["Configurations"],
    }),
    activateConfiguration: builder.mutation<any, number>({
      query: (id) => ({ url: `/action-configurations/${id}/activate`, method: "PATCH" }),
      invalidatesTags: ["Configurations"],
    }),
    deactivateConfiguration: builder.mutation<any, number>({
      query: (id) => ({ url: `/action-configurations/${id}/deactivate`, method: "PATCH" }),
      invalidatesTags: ["Configurations"],
    }),

    // ── Analytics (full) ──────────────────────────────────────────────────
    getExecutionVolume: builder.query<any[], string | void>({
      query: (startDate) =>
        startDate ? `/analytics/execution-volume?start_date=${startDate}` : "/analytics/execution-volume",
    }),
    getFailures: builder.query<any[], string | void>({
      query: (startDate) =>
        startDate ? `/analytics/failures?start_date=${startDate}` : "/analytics/failures",
    }),
    getRetries: builder.query<any[], string | void>({
      query: (startDate) =>
        startDate ? `/analytics/retries?start_date=${startDate}` : "/analytics/retries",
    }),
    getWorkflowCreation: builder.query<any[], string | void>({
      query: (startDate) =>
        startDate ? `/analytics/workflow-creation?start_date=${startDate}` : "/analytics/workflow-creation",
    }),

    // ── Health ────────────────────────────────────────────────────────────
    getHealth: builder.query<any, void>({
      query: () => "/health/ready",
    }),
  }),
});

export const {
  useGetDashboardStatsQuery,
  useGetExecutionTrendQuery,
  useGetWorkflowUsageQuery,
  useGetWorkflowsQuery,
  useGetWorkflowQuery,
  useGenerateWorkflowMutation,
  useExecuteWorkflowMutation,
  usePauseExecutionMutation,
  useResumeExecutionMutation,
  useGetExecutionsQuery,
  useGetExecutionQuery,
  useGetTriggersQuery,
  useGetActionsQuery,
  useSemanticSearchMutation,
  useUploadBRDMutation,
  useGetTracesQuery,
  useGetPromptsQuery,
  useGetPromptStatsQuery,
  useActivatePromptMutation,
  useRollbackPromptMutation,
  useGetIntegrationsQuery,
  useCreateIntegrationMutation,
  useUpdateIntegrationMutation,
  useDeleteIntegrationMutation,
  useGetConfigurationsQuery,
  useGetConfigurationQuery,
  useUpdateConfigurationMutation,
  useActivateConfigurationMutation,
  useDeactivateConfigurationMutation,
  useGetExecutionVolumeQuery,
  useGetFailuresQuery,
  useGetRetriesQuery,
  useGetWorkflowCreationQuery,
  useGetHealthQuery,
} = api;
