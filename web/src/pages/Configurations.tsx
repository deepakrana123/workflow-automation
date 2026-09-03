// ActionConfiguration was removed — execution configuration now lives on
// WorkflowActionMapping rows and is managed from the Workspace detail page.
// This file is a placeholder to prevent import errors from App.tsx.

const Configurations = () => (
  <div className="animate-in">
    <h1 className="text-xl font-semibold text-gray-900">Configurations</h1>
    <p className="text-sm text-gray-400 mt-2">
      Action execution configuration is now managed per workspace via the
      Workspace detail page (unmapped actions → custom execution template).
    </p>
  </div>
);

export default Configurations;
