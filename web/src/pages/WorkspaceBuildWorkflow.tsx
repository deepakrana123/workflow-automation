import { useState, useRef, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import {
  useGetWorkspaceQuery,
  useGetWorkspaceOverviewQuery,
  useGetActionsQuery,
} from "@/store/api";
import {
  Sparkles, ArrowLeft, Plus, X, Search, Check,
  Loader2, AlertTriangle, GitBranch, ChevronRight,
} from "lucide-react";
import { clsx } from "clsx";

// ── SSE event types ────────────────────────────────────────────────────────────
interface StreamEvent {
  event: string;
  seq: number;
  ts: number;
  data: any;
}

// ── Chat message types ─────────────────────────────────────────────────────────
type MsgKind =
  | "user"
  | "thinking"
  | "progress"
  | "step"
  | "explanation"
  | "done"
  | "error";

interface ChatMsg {
  id: number;
  kind: MsgKind;
  text?: string;
  data?: any;
}

let _msgId = 0;
const nextId = () => ++_msgId;

const WorkspaceBuildWorkflow = () => {
  const { id } = useParams();
  const wsId = Number(id);

  const { data: workspace } = useGetWorkspaceQuery(wsId);
  const { data: overview }  = useGetWorkspaceOverviewQuery(wsId);

  const [name,        setName]        = useState("");
  const [instruction, setInstruction] = useState("");
  const [selected,    setSelected]    = useState<any[]>([]);
  const [messages,    setMessages]    = useState<ChatMsg[]>([]);
  const [streaming,   setStreaming]   = useState(false);
  const [doneWfId,    setDoneWfId]    = useState<number | null>(null);

  const bottomRef  = useRef<HTMLDivElement>(null);
  const readerRef  = useRef<ReadableStreamDefaultReader | null>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function addMsg(msg: ChatMsg) {
    setMessages((prev) => {
      // Replace thinking spinner with actual progress if same event type
      if (msg.kind === "progress") {
        const last = prev[prev.length - 1];
        if (last?.kind === "thinking") return [...prev.slice(0, -1), msg];
      }
      return [...prev, msg];
    });
  }

  async function handleGenerate() {
    if (!name.trim() || !instruction.trim() || streaming) return;
    setMessages([]);
    setDoneWfId(null);
    setStreaming(true);

    addMsg({ id: nextId(), kind: "user", text: instruction });
    addMsg({ id: nextId(), kind: "thinking" });

    try {
      const res = await fetch(`/api/workspaces/${wsId}/generate/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          user_request: instruction,
          domain: "finance",
          selected_action_ids: selected.map((a) => a.id),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Request failed" }));
        addMsg({ id: nextId(), kind: "error", text: err.detail || "Request failed" });
        setStreaming(false);
        return;
      }

      const reader = res.body!.getReader();
      readerRef.current = reader;
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE lines: "data: {...}\n\n"
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.startsWith("data:")) continue;
          const raw = part.replace(/^data:\s*/, "").trim();
          if (!raw) continue;
          try {
            const evt: StreamEvent = JSON.parse(raw);
            handleEvent(evt);
          } catch {
            // malformed chunk — skip
          }
        }
      }
    } catch (err: any) {
      addMsg({ id: nextId(), kind: "error", text: err?.message || "Connection failed" });
    } finally {
      readerRef.current = null;
      setStreaming(false);
    }
  }

  function handleEvent(evt: StreamEvent) {
    const { event, data } = evt;

    switch (event) {
      case "started":
        addMsg({ id: nextId(), kind: "progress", text: "Starting generation…" });
        break;

      case "catalog_matched":
        addMsg({
          id: nextId(), kind: "progress",
          text: `Matched ${data.action_count} actions, ${data.trigger_count} triggers from workspace`,
        });
        break;

      case "context_built":
        addMsg({ id: nextId(), kind: "progress", text: "Workspace context built — rules and actors loaded" });
        break;

      case "llm_started":
        addMsg({
          id: nextId(), kind: "progress",
          text: data.is_fallback
            ? `Trying fallback provider (${data.provider})… ${data.budget_remaining_s}s remaining`
            : `Generating (attempt ${data.attempt})… ${data.budget_remaining_s}s budget remaining`,
        });
        break;

      case "llm_attempt_failed":
        addMsg({
          id: nextId(), kind: "progress",
          text: `Attempt ${data.attempt} failed — ${(data.errors || []).join(", ")}. Retrying…`,
        });
        break;

      case "llm_success":
        addMsg({ id: nextId(), kind: "progress", text: `Generated on attempt ${data.attempt} (${data.elapsed_ms}ms)` });
        break;

      case "compiled":
        addMsg({
          id: nextId(), kind: "progress",
          text: `Compiled — ${data.step_count} step${data.step_count !== 1 ? "s" : ""} · trigger: ${data.trigger}`,
        });
        break;

      case "step":
        addMsg({ id: nextId(), kind: "step", data });
        break;

      case "explanation":
        addMsg({ id: nextId(), kind: "explanation", data });
        break;

      case "saved":
        setDoneWfId(data.workflow_id);
        addMsg({ id: nextId(), kind: "done", data });
        break;

      case "chains_detected":
        if ((data.chains || []).length > 0) {
          addMsg({
            id: nextId(), kind: "progress",
            text: `💡 ${data.chains.length} chain connection${data.chains.length > 1 ? "s" : ""} detected`,
          });
        }
        break;

      case "heartbeat":
        // silently ignore
        break;

      case "error":
        addMsg({ id: nextId(), kind: "error", text: data.message || "Generation failed" });
        break;

      case "stream_closed":
        // stream is done — handled by the reader loop ending
        break;
    }
  }

  if (!workspace) return <div className="h-8 w-40 rounded skeleton mt-8" />;

  const canGenerate = name.trim().length > 0 && instruction.trim().length > 0 && !streaming;

  return (
    <div className="animate-in max-w-2xl space-y-5">
      {/* Back */}
      <div>
        <Link to={`/workspaces/${wsId}`}
          className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-2 transition-colors">
          <ArrowLeft size={12} /> {workspace.display_name}
        </Link>
        <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <Sparkles size={17} className="text-gray-700" /> Build with AI
        </h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Uses this workspace's actions and rules — not the global catalog.
        </p>
      </div>

      {/* Workspace context strip */}
      {overview && (
        <div className="flex items-center gap-4 px-4 py-3 rounded-xl bg-gray-50 border border-gray-100 text-sm">
          <CtxStat label="Actions"  value={overview.action_count} />
          <div className="w-px h-4 bg-gray-200" />
          <CtxStat label="Triggers" value={overview.trigger_count} />
          <div className="w-px h-4 bg-gray-200" />
          <CtxStat label="Rules"    value={overview.business_rule_count} />
          <div className="w-px h-4 bg-gray-200" />
          <CtxStat label="BRDs"     value={overview.brd_count} />
        </div>
      )}

      {/* Input form — hidden while streaming, shown again after done */}
      {!streaming && doneWfId === null && (
        <div className="card p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500">Workflow name</label>
              <input className="input mt-0.5" value={name} onChange={(e) => setName(e.target.value)}
                placeholder="loan_approval_flow" />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-500">What should this workflow do?</label>
              <textarea className="input mt-0.5" rows={4} value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="Generate a workflow for processing a personal loan application starting from KYC verification through to disbursement." />
            </div>
          </div>

          <ActionPicker selected={selected} setSelected={setSelected} />

          <button onClick={handleGenerate} disabled={!canGenerate}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-medium disabled:opacity-40 hover:bg-gray-700 transition-colors">
            <Sparkles size={14} /> Generate workflow
          </button>
        </div>
      )}

      {/* Chat stream */}
      {messages.length > 0 && (
        <div className="space-y-2">
          {messages.map((msg) => <ChatBubble key={msg.id} msg={msg} />)}
          <div ref={bottomRef} />
        </div>
      )}

      {/* Done actions */}
      {doneWfId !== null && !streaming && (
        <div className="flex items-center gap-3">
          <Link to={`/workflows/${doneWfId}`}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 transition-colors">
            <GitBranch size={13} /> View workflow #{doneWfId}
          </Link>
          <button onClick={() => { setMessages([]); setDoneWfId(null); setName(""); setInstruction(""); }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 transition-colors">
            <Plus size={13} /> Generate another
          </button>
          <Link to={`/workspaces/${wsId}`}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors">
            ← Back to workspace
          </Link>
        </div>
      )}
    </div>
  );
};

// ── Chat bubble renderer ──────────────────────────────────────────────────────
const ChatBubble = ({ msg }: { msg: ChatMsg }) => {
  if (msg.kind === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-br-md bg-gray-900 text-white text-sm">
          {msg.text}
        </div>
      </div>
    );
  }

  if (msg.kind === "thinking") {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-gray-400 text-sm">
        <Loader2 size={13} className="animate-spin shrink-0" />
        <span>Thinking…</span>
      </div>
    );
  }

  if (msg.kind === "progress") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-gray-500 text-xs">
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300 shrink-0" />
        {msg.text}
      </div>
    );
  }

  if (msg.kind === "step") {
    const { id, action, display_name, depends_on, rules, actors } = msg.data;
    return (
      <div className="flex items-start gap-3 pl-3">
        <div className="w-6 h-6 rounded-lg bg-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-500 shrink-0 mt-0.5">
          {id}
        </div>
        <div className="flex-1 min-w-0 py-0.5">
          <p className="text-sm font-medium text-gray-800">{display_name || action}</p>
          {depends_on?.length > 0 && (
            <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
              <ChevronRight size={10} /> after {depends_on.join(", ")}
            </p>
          )}
          {rules?.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {rules.map((r: string, i: number) => (
                <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">{r}</span>
              ))}
            </div>
          )}
          {actors?.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {actors.map((a: string, i: number) => (
                <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">{a}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (msg.kind === "explanation") {
    const { summary } = msg.data;
    return (
      <div className="mx-3 px-4 py-3 rounded-xl bg-gray-50 border border-gray-100 text-sm text-gray-600">
        {summary}
      </div>
    );
  }

  if (msg.kind === "done") {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-emerald-600 text-sm font-medium">
        <Check size={14} className="shrink-0" />
        Workflow #{msg.data?.workflow_id} saved
      </div>
    );
  }

  if (msg.kind === "error") {
    return (
      <div className="flex items-start gap-2 px-3 py-2.5 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600 mx-0">
        <AlertTriangle size={14} className="shrink-0 mt-0.5" />
        {msg.text}
      </div>
    );
  }

  return null;
};

// ── Action picker ─────────────────────────────────────────────────────────────
const ActionPicker = ({ selected, setSelected }: { selected: any[]; setSelected: (a: any[]) => void }) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { data } = useGetActionsQuery({ page_size: 20, search }, { skip: !open || search.length < 2 });
  const results = data?.data || [];

  const add    = (a: any) => { if (!selected.find((s) => s.id === a.id)) setSelected([...selected, a]); };
  const remove = (id: number) => setSelected(selected.filter((s) => s.id !== id));

  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="text-xs text-gray-500">Extra global actions (optional)</label>
        <button type="button" onClick={() => setOpen((o) => !o)}
          className="text-xs text-gray-500 hover:text-gray-800 inline-flex items-center gap-1 transition-colors">
          <Plus size={11} /> Add
        </button>
      </div>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {selected.map((a) => (
            <span key={a.id}
              className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 inline-flex items-center gap-1">
              {a.display_name || a.name}
              <button type="button" onClick={() => remove(a.id)} className="hover:text-gray-900">
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}

      {open && (
        <div className="mt-2 border border-gray-200 rounded-xl p-2">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="input pl-8 text-sm" value={search} autoFocus
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search catalog (2+ chars)…" />
          </div>
          <div className="mt-1.5 max-h-48 overflow-y-auto space-y-0.5">
            {search.length < 2 && <p className="text-xs text-gray-400 px-1 py-1">Type to search</p>}
            {results.map((a: any) => {
              const already = !!selected.find((s) => s.id === a.id);
              return (
                <button key={a.id} type="button" disabled={already} onClick={() => add(a)}
                  className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-gray-50 disabled:opacity-40 flex items-center gap-2 text-sm">
                  <span className="font-medium text-gray-800 flex-1">{a.display_name}</span>
                  <code className="text-xs text-gray-400">{a.name}</code>
                </button>
              );
            })}
            {search.length >= 2 && results.length === 0 && (
              <p className="text-xs text-gray-400 px-1 py-1">No matches.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const CtxStat = ({ label, value }: { label: string; value: any }) => (
  <div className="text-center">
    <p className="text-sm font-semibold text-gray-800">{value ?? 0}</p>
    <p className="text-xs text-gray-400">{label}</p>
  </div>
);

export default WorkspaceBuildWorkflow;
