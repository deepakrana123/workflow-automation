import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({ baseUrl: "/api" }),
  tagTypes: [
    "Workflows",
    "Executions",
    "Catalog",
    "Dashboard",
    "Traces",
    "Prompts",
    "Integrations",
    "Configurations",
    "HumanTasks",
    "Settings",
    "Health",
    "Workspaces",
  ],
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
    getDomainDistribution: builder.query<any[], void>({
      query: () => "/dashboard/domain-distribution",
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
    getWorkflowDsl: builder.query<any, number>({
      query: (id) => `/workflows/${id}/dsl`,
    }),
    getWorkflowAst: builder.query<any, number>({
      query: (id) => `/workflows/${id}/ast`,
    }),
    getWorkflowCompiled: builder.query<any, number>({
      query: (id) => `/workflows/${id}/compiled`,
    }),
    getWorkflowProvenance: builder.query<any, number>({
      query: (id) => `/workflows/${id}/provenance`,
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

    // ── Human Tasks ───────────────────────────────────────────────────────
    getHumanTasks: builder.query<any[], { status?: string; workflow_execution_id?: number } | void>({
      query: (params) => {
        const qs = new URLSearchParams();
        if (params?.status) qs.set("status", params.status);
        if (params?.workflow_execution_id)
          qs.set("workflow_execution_id", String(params.workflow_execution_id));
        const s = qs.toString();
        return s ? `/human-tasks?${s}` : "/human-tasks";
      },
      providesTags: ["HumanTasks"],
    }),
    getHumanTask: builder.query<any, number>({
      query: (id) => `/human-tasks/${id}`,
      providesTags: ["HumanTasks"],
    }),
    decideHumanTask: builder.mutation<any, { id: number; decision: "approve" | "reject" }>({
      query: ({ id, decision }) => ({
        url: `/human-tasks/${id}/decision`,
        method: "POST",
        body: { decision },
      }),
      invalidatesTags: ["HumanTasks", "Executions"],
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
    getTrigger: builder.query<any, number>({
      query: (id) => `/catalog/triggers/${id}`,
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
    getAction: builder.query<any, number>({
      query: (id) => `/catalog/actions/${id}`,
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
    getTrace: builder.query<any, string>({
      query: (traceId) => `/traces/${traceId}`,
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
    getPromptState: builder.query<any, string>({
      query: (name) => `/prompts/${name}/state`,
      providesTags: ["Prompts"],
    }),
    getPromptFailures: builder.query<any[], { name: string; limit?: number }>({
      query: ({ name, limit = 10 }) => `/prompts/${name}/failures?limit=${limit}`,
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

    // ── Workspace ─────────────────────────────────────────────────────────
    getWorkspaces: builder.query<any[], void>({
      query: () => "/workspaces",
      providesTags: ["Workspaces"],
    }),
    getWorkspace: builder.query<any, number>({
      query: (id) => `/workspaces/${id}`,
      providesTags: ["Workspaces"],
    }),
    createWorkspace: builder.mutation<any, { name: string; display_name: string; description?: string; organization_name?: string }>({
      query: (body) => ({ url: "/workspaces", method: "POST", body }),
      invalidatesTags: ["Workspaces"],
    }),
    getWorkspaceSynthesis: builder.query<any, number>({
      query: (workspaceId) => `/workspaces/${workspaceId}/synthesis`,
    }),
    getWorkspaceOverview: builder.query<any, number>({
      query: (workspaceId) => `/workspaces/${workspaceId}/overview`,
      providesTags: ["Workspaces"],
    }),
    getWorkspaceDocuments: builder.query<any, number>({
      query: (workspaceId) => `/workspaces/${workspaceId}/documents`,
      providesTags: ["Workspaces"],
    }),
    getWorkspaceBusinessRules: builder.query<any, number>({
      query: (workspaceId) => `/workspaces/${workspaceId}/business-rules`,
      providesTags: ["Workspaces"],
    }),
    getWorkspaceActions: builder.query<any, number>({
      query: (workspaceId) => `/workspaces/${workspaceId}/actions`,
      providesTags: ["Workspaces"],
    }),
    getWorkspaceDiagnostics: builder.query<any, number>({
      query: (workspaceId) => `/workspaces/${workspaceId}/diagnostics`,
      providesTags: ["Workspaces"],
    }),
    getWorkspaceWorkflows: builder.query<any[], number>({
      query: (workspaceId) => `/workflows?workspace_id=${workspaceId}`,
      providesTags: ["Workflows"],
    }),
    synthesizeWorkspaceWorkflow: builder.mutation<any, { workspaceId: number; name: string; domain: string }>({
      query: ({ workspaceId, ...body }) => ({
        url: `/workspaces/${workspaceId}/synthesize`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Workflows", "Workspaces"],
    }),
    generateWorkspaceWorkflow: builder.mutation<
      any,
      { workspaceId: number; name: string; user_request: string; domain?: string; selected_action_ids?: number[] }
    >({
      query: ({ workspaceId, ...body }) => ({
        url: `/workspaces/${workspaceId}/generate`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Workflows", "Workspaces"],
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
    getTriggerFrequency: builder.query<any[], string | void>({
      query: (startDate) =>
        startDate ? `/analytics/trigger-frequency?start_date=${startDate}` : "/analytics/trigger-frequency",
    }),
    getActionFrequency: builder.query<any[], string | void>({
      query: (startDate) =>
        startDate ? `/analytics/action-frequency?start_date=${startDate}` : "/analytics/action-frequency",
    }),
    getAnalyticsAll: builder.query<any, string | void>({
      query: (startDate) =>
        startDate ? `/analytics?start_date=${startDate}` : "/analytics",
    }),

    // ── Settings ──────────────────────────────────────────────────────────
    getSettings: builder.query<any, void>({
      query: () => "/settings",
      providesTags: ["Settings"],
    }),
    updateSettings: builder.mutation<any, any>({
      query: (body) => ({ url: "/settings", method: "PUT", body }),
      invalidatesTags: ["Settings"],
    }),

    // ── Health ────────────────────────────────────────────────────────────
    getHealth: builder.query<any, void>({
      query: () => "/health/ready",
      providesTags: ["Health"],
    }),
    getSystemHealth: builder.query<any, void>({
      query: () => "/health/",
      providesTags: ["Health"],
    }),
    getProviderHealth: builder.query<any, void>({
      query: () => "/health/providers",
      providesTags: ["Health"],
    }),
    resetProvider: builder.mutation<any, string>({
      query: (providerName) => ({
        url: `/health/providers/${providerName}/reset`,
        method: "POST",
      }),
      invalidatesTags: ["Health"],
    }),
  }),
});

export const {
  // Dashboard
  useGetDashboardStatsQuery,
  useGetExecutionTrendQuery,
  useGetWorkflowUsageQuery,
  useGetDomainDistributionQuery,
  // Workflows
  useGetWorkflowsQuery,
  useGetWorkflowQuery,
  useGenerateWorkflowMutation,
  useGetWorkflowDslQuery,
  useGetWorkflowAstQuery,
  useGetWorkflowCompiledQuery,
  useGetWorkflowProvenanceQuery,
  // Execute
  useExecuteWorkflowMutation,
  usePauseExecutionMutation,
  useResumeExecutionMutation,
  // Executions
  useGetExecutionsQuery,
  useGetExecutionQuery,
  // Human Tasks
  useGetHumanTasksQuery,
  useGetHumanTaskQuery,
  useDecideHumanTaskMutation,
  // Catalog
  useGetTriggersQuery,
  useGetTriggerQuery,
  useGetActionsQuery,
  useGetActionQuery,
  useSemanticSearchMutation,
  // Knowledge
  useUploadBRDMutation,
  // Traces
  useGetTracesQuery,
  useGetTraceQuery,
  // Prompts
  useGetPromptsQuery,
  useGetPromptStatsQuery,
  useGetPromptStateQuery,
  useGetPromptFailuresQuery,
  useActivatePromptMutation,
  useRollbackPromptMutation,
  // Workspace
  useGetWorkspacesQuery,
  useGetWorkspaceQuery,
  useCreateWorkspaceMutation,
  useGetWorkspaceSynthesisQuery,
  useGetWorkspaceOverviewQuery,
  useGetWorkspaceDocumentsQuery,
  useGetWorkspaceBusinessRulesQuery,
  useGetWorkspaceActionsQuery,
  useGetWorkspaceDiagnosticsQuery,
  useGetWorkspaceWorkflowsQuery,
  useSynthesizeWorkspaceWorkflowMutation,
  useGenerateWorkspaceWorkflowMutation,
  // Integrations
  useGetIntegrationsQuery,
  useCreateIntegrationMutation,
  useUpdateIntegrationMutation,
  useDeleteIntegrationMutation,
  // Configurations
  useGetConfigurationsQuery,
  useGetConfigurationQuery,
  useUpdateConfigurationMutation,
  useActivateConfigurationMutation,
  useDeactivateConfigurationMutation,
  // Analytics
  useGetExecutionVolumeQuery,
  useGetFailuresQuery,
  useGetRetriesQuery,
  useGetWorkflowCreationQuery,
  useGetTriggerFrequencyQuery,
  useGetActionFrequencyQuery,
  useGetAnalyticsAllQuery,
  // Settings
  useGetSettingsQuery,
  useUpdateSettingsMutation,
  // Health
  useGetHealthQuery,
  useGetSystemHealthQuery,
  useGetProviderHealthQuery,
  useResetProviderMutation,
} = api;
