import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Workflows from "./pages/Workflows";
import WorkflowGenerate from "./pages/WorkflowGenerate";
import WorkflowDetail from "./pages/WorkflowDetail";
import Executions from "./pages/Executions";
import ExecutionDetail from "./pages/ExecutionDetail";
import HumanTasks from "./pages/HumanTasks";
import Workspaces from "./pages/Workspaces";
import WorkspaceDetail from "./pages/WorkspaceDetail";
import WorkspaceBuildWorkflow from "./pages/WorkspaceBuildWorkflow";
import Catalog from "./pages/Catalog";
import KnowledgeIngestion from "./pages/KnowledgeIngestion";
import Analytics from "./pages/Analytics";
import Traces from "./pages/Traces";
import Prompts from "./pages/Prompts";
import Integrations from "./pages/Integrations";
import Configurations from "./pages/Configurations";
import Settings from "./pages/Settings";
// ── Runtime screens ───────────────────────────────────────────────────────────
import RuntimeWorkflows from "./pages/RuntimeWorkflows";
import RuntimeExecutionView from "./pages/RuntimeExecutionView";
import RuntimeRetrievalInspector from "./pages/RuntimeRetrievalInspector";
import RuntimeRuleInspector from "./pages/RuntimeRuleInspector";
import RuntimeRBACInspector from "./pages/RuntimeRBACInspector";

const App = () => {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* ── Existing routes ───────────────────────────────────────────── */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/workspaces" element={<Workspaces />} />
        <Route path="/workspaces/:id" element={<WorkspaceDetail />} />
        <Route path="/workspaces/:id/build" element={<WorkspaceBuildWorkflow />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/workflows/generate" element={<WorkflowGenerate />} />
        <Route path="/workflows/:id" element={<WorkflowDetail />} />
        <Route path="/executions" element={<Executions />} />
        <Route path="/executions/:id" element={<ExecutionDetail />} />
        <Route path="/human-tasks" element={<HumanTasks />} />
        <Route path="/catalog" element={<Catalog />} />
        <Route path="/knowledge" element={<KnowledgeIngestion />} />
        <Route path="/traces" element={<Traces />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/prompts" element={<Prompts />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/configurations" element={<Configurations />} />
        <Route path="/settings" element={<Settings />} />
        {/* ── Runtime screens ───────────────────────────────────────────── */}
        <Route path="/runtime/workflows" element={<RuntimeWorkflows />} />
        <Route path="/runtime/workflows/:id" element={<WorkflowDetail />} />
        <Route path="/runtime/executions/:id" element={<RuntimeExecutionView />} />
        <Route path="/runtime/retrieval" element={<RuntimeRetrievalInspector />} />
        <Route path="/runtime/rules" element={<RuntimeRuleInspector />} />
        <Route path="/runtime/rbac" element={<RuntimeRBACInspector />} />
      </Route>
    </Routes>
  );
};

export default App;
