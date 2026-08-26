/**
 * Screen D: Rule Inspector
 * Shows the layered effective rule set for the workspace with pass/fail evaluation.
 */
import { useState, useEffect } from "react";
import { Shield, CheckCircle, XCircle, Lock, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";

const USER_ID = "user_1";
const WORKSPACE_ID = "1";

interface Rule {
  id: number;
  description: string;
  field: string | null;
  op: string | null;
  value: any;
  allowed_roles: string[];
  locked: boolean;
  evaluable: boolean;
  scope_workspace_id: number;
}

function RuleRow({ rule, testValue, onTest }: {
  rule: Rule;
  testValue: string;
  onTest: (ruleId: number, val: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50"
      >
        {rule.locked ? (
          <Lock size={14} className="text-red-400 shrink-0" />
        ) : (
          <Shield size={14} className="text-blue-400 shrink-0" />
        )}
        <span className="flex-1 text-sm text-gray-800">{rule.description}</span>
        <div className="flex items-center gap-2 shrink-0">
          {rule.locked && (
            <span className="text-xs px-1.5 py-0.5 bg-red-50 text-red-600 border border-red-200 rounded">
              LOCKED
            </span>
          )}
          {rule.evaluable ? (
            <span className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-600 border border-blue-200 rounded font-mono">
              {rule.field} {rule.op} {JSON.stringify(rule.value)}
            </span>
          ) : (
            <span className="text-xs px-1.5 py-0.5 bg-gray-50 text-gray-500 border border-gray-200 rounded">
              info only
            </span>
          )}
          {expanded ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 px-4 pb-3 pt-2 space-y-2 bg-gray-50">
          <div className="flex gap-4 flex-wrap text-xs text-gray-600">
            <span><strong>Field:</strong> {rule.field || "—"}</span>
            <span><strong>Op:</strong> {rule.op || "—"}</span>
            <span><strong>Value:</strong> {rule.value != null ? JSON.stringify(rule.value) : "—"}</span>
            <span><strong>Scope WS:</strong> {rule.scope_workspace_id}</span>
          </div>
          {rule.allowed_roles?.length > 0 && (
            <div className="text-xs text-gray-600">
              <strong>Allowed roles:</strong> {rule.allowed_roles.join(", ")}
            </div>
          )}

          {rule.evaluable && (
            <div className="flex items-center gap-2 pt-1">
              <input
                value={testValue}
                onChange={e => onTest(rule.id, e.target.value)}
                placeholder={`Test value for ${rule.field}`}
                className="border border-gray-200 rounded px-2 py-1 text-xs w-40 focus:outline-none"
              />
              {testValue !== "" && rule.value != null && (
                <span className={`flex items-center gap-1 text-xs font-medium ${
                  evalCondition(rule.op, testValue, rule.value)
                    ? "text-green-600"
                    : "text-red-600"
                }`}>
                  {evalCondition(rule.op, testValue, rule.value)
                    ? <><CheckCircle size={12} /> Pass</>
                    : <><XCircle size={12} /> Fail</>
                  }
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function evalCondition(op: string | null, actual: string, expected: any): boolean {
  if (!op || actual === "") return true;
  const a = isNaN(Number(actual)) ? actual : Number(actual);
  const e = typeof expected === "number" ? expected : (isNaN(Number(expected)) ? expected : Number(expected));
  switch (op) {
    case "==": return a == e;
    case "!=": return a != e;
    case ">":  return Number(a) > Number(e);
    case ">=": return Number(a) >= Number(e);
    case "<":  return Number(a) < Number(e);
    case "<=": return Number(a) <= Number(e);
    default:   return true;
  }
}

export default function RuntimeRuleInspector() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testValues, setTestValues] = useState<Record<number, string>>({});

  useEffect(() => {
    fetch(`/api/runtime/rules/${WORKSPACE_ID}`, {
      headers: { "X-User-Id": USER_ID, "X-Workspace-Id": WORKSPACE_ID },
    })
      .then(r => r.json())
      .then(d => setRules(d.rules || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const evaluable = rules.filter(r => r.evaluable);
  const infoOnly  = rules.filter(r => !r.evaluable);
  const locked    = rules.filter(r => r.locked);

  if (loading) return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Loading…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Rule Inspector</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Effective business rules for workspace {WORKSPACE_ID} — ordered global → branch.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Total Rules", value: rules.length, color: "text-gray-900" },
          { label: "Evaluable", value: evaluable.length, color: "text-blue-700" },
          { label: "Locked (global)", value: locked.length, color: "text-red-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white border border-gray-200 rounded-xl p-3">
            <p className="text-xs text-gray-500">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Evaluable rules */}
      {evaluable.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">
            Evaluable Rules
            <span className="ml-1.5 text-xs font-normal text-gray-400">(click to test with a value)</span>
          </h2>
          <div className="space-y-2">
            {evaluable.map(r => (
              <RuleRow
                key={r.id}
                rule={r}
                testValue={testValues[r.id] ?? ""}
                onTest={(id, val) => setTestValues(prev => ({ ...prev, [id]: val }))}
              />
            ))}
          </div>
        </div>
      )}

      {/* Info-only rules */}
      {infoOnly.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Description-only Rules</h2>
          <div className="space-y-2">
            {infoOnly.map(r => (
              <RuleRow
                key={r.id}
                rule={r}
                testValue=""
                onTest={() => {}}
              />
            ))}
          </div>
        </div>
      )}

      {rules.length === 0 && !error && (
        <div className="text-center py-16 text-gray-400">
          <Shield size={32} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No rules defined for this workspace yet.</p>
          <p className="text-xs mt-1">Run RBAC extraction from the workspace to populate rules.</p>
        </div>
      )}
    </div>
  );
}
