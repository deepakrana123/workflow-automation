import { clsx } from "clsx";

const colors: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-800",
  running: "bg-blue-100 text-blue-800",
  pending: "bg-gray-100 text-gray-800",
  failed: "bg-red-100 text-red-800",
  dlq: "bg-red-200 text-red-900",
  retry_scheduled: "bg-amber-100 text-amber-800",
  paused: "bg-purple-100 text-purple-800",
  queued: "bg-gray-100 text-gray-600",
  active: "bg-emerald-100 text-emerald-800",
};

export default function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize",
        colors[s] || "bg-gray-100 text-gray-700"
      )}
    >
      {s.replace(/_/g, " ")}
    </span>
  );
}
