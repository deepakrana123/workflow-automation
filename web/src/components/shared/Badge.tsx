import { clsx } from "clsx";

type BadgeVariant = "default" | "success" | "danger" | "warning" | "info";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-gray-100 text-gray-600",
  success: "bg-emerald-50 text-emerald-700",
  danger: "bg-red-50 text-red-700",
  warning: "bg-amber-50 text-amber-700",
  info: "bg-blue-50 text-blue-700",
};

const dotStyles: Record<BadgeVariant, string> = {
  default: "bg-gray-400",
  success: "bg-emerald-500",
  danger: "bg-red-500",
  warning: "bg-amber-500",
  info: "bg-blue-500",
};

export const Badge = ({ children, variant = "default", dot, className }: BadgeProps) => (
  <span className={clsx("badge", variantStyles[variant], className)}>
    {dot && <span className={clsx("w-1.5 h-1.5 rounded-full", dotStyles[variant])} />}
    {children}
  </span>
);
