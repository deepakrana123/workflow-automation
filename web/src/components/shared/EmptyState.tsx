import { type LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState = ({ icon: Icon, title, description, action, className }: EmptyStateProps) => (
  <div className={`flex flex-col items-center justify-center py-16 text-center ${className || ""}`}>
    {Icon && (
      <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center mb-3">
        <Icon size={18} className="text-gray-400" />
      </div>
    )}
    <p className="text-sm font-medium text-gray-600">{title}</p>
    {description && <p className="text-2xs text-gray-400 mt-1">{description}</p>}
    {action && <div className="mt-3">{action}</div>}
  </div>
);
