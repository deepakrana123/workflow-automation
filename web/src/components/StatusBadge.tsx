import { clsx } from "clsx";

const styles: Record<string, string> = {
  completed: "bg-emerald-50 text-emerald-700",
  running: "bg-blue-50 text-blue-700",
  pending: "bg-gray-100 text-gray-600",
  failed: "bg-red-50 text-red-700",
  dlq: "bg-red-100 text-red-800",
  retry_scheduled: "bg-amber-50 text-amber-700",
  paused: "bg-purple-50 text-purple-700",
  queued: "bg-gray-100 text-gray-600",
  active: "bg-emerald-50 text-emerald-700",
};

const dots: Record<string, string> = {
  running: "bg-blue-500 animate-pulse-dot",
  active: "bg-emerald-500 animate-pulse-dot",
  dlq: "bg-red-500",
  retry_scheduled: "bg-amber-500 animate-pulse-dot",
};

const StatusBadge = ({ status }: { status: string }) => {
  const s = status.toLowerCase();
  return (
    <span className={clsx("badge", styles[s] || "bg-gray-100 text-gray-600")}>
      {dots[s] && <span className={clsx("w-1.5 h-1.5 rounded-full", dots[s])} />}
      {s.replace(/_/g, " ")}
    </span>
  );
}

export default StatusBadge;
