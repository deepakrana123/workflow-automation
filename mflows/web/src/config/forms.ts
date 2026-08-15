import type { FormField } from "@/types/form";

export const INTEGRATION_FIELDS: FormField[] = [
  { name: "name", label: "Name", type: "text", required: true, placeholder: "Service name" },
  {
    name: "provider_type", label: "Provider Type", type: "select",
    options: [
      { label: "HTTP", value: "http" },
      { label: "SOAP", value: "soap" },
      { label: "gRPC", value: "grpc" },
      { label: "Kafka", value: "kafka" },
    ],
  },
  { name: "base_url", label: "Base URL", type: "text", required: true, placeholder: "https://api.example.com" },
  {
    name: "authentication_type", label: "Auth Type", type: "select",
    options: [
      { label: "Bearer Token", value: "bearer" },
      { label: "API Key", value: "api_key" },
      { label: "Basic Auth", value: "basic" },
      { label: "OAuth2", value: "oauth2" },
    ],
  },
  { name: "credentials", label: "Credentials (JSON)", type: "textarea", rows: 2, colSpan: 2, placeholder: '{"token": "..."}' },
  { name: "description", label: "Description", type: "text", colSpan: 2, placeholder: "Optional description" },
];

export const INTEGRATION_DEFAULTS: Record<string, unknown> = {
  name: "",
  provider_type: "http",
  base_url: "",
  authentication_type: "bearer",
  credentials: "{}",
  description: "",
};

export const CONFIGURATION_EDIT_FIELDS: FormField[] = [
  {
    name: "execution_type", label: "Execution Type", type: "select",
    options: [
      { label: "Python", value: "python" },
      { label: "HTTP", value: "http" },
    ],
  },
  { name: "workspace_integration_id", label: "Integration ID", type: "text", placeholder: "Optional" },
  { name: "configuration", label: "Configuration (JSON)", type: "textarea", rows: 5, colSpan: 2 },
];

export const WORKFLOW_GENERATE_FIELDS: FormField[] = [
  { name: "name", label: "Workflow Name", type: "text", required: true, placeholder: "loan_collection_flow", colSpan: 2 },
  { name: "user_request", label: "Instruction", type: "textarea", required: true, rows: 4, colSpan: 2, placeholder: "When payment is missed send reminder then assign recovery agent..." },
];

export const WORKFLOW_GENERATE_DEFAULTS: Record<string, unknown> = {
  name: "",
  user_request: "",
};
