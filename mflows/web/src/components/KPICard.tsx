import { type LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: "up" | "down";
  trendValue?: string;
}

const KPICard = ({ title, value, subtitle, icon: Icon, trend, trendValue }: Props) => {
  return (
    <div className="card p-4 flex flex-col gap-2 hover:shadow-card transition-shadow duration-200">
      <div className="flex items-center justify-between">
        <span className="text-2xs font-semibold text-gray-500 uppercase tracking-wide">{title}</span>
        {Icon && (
          <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center">
            <Icon size={14} className="text-gray-500" />
          </div>
        )}
      </div>
      <span className="text-2xl font-semibold text-gray-900 tracking-tight">{value}</span>
      {(trend || subtitle) && (
        <div className="flex items-center gap-1.5 text-2xs">
          {trend && (
            <span className={trend === "up" ? "text-success font-semibold" : "text-danger font-semibold"}>
              {trend === "up" ? "↑" : "↓"} {trendValue}
            </span>
          )}
          {subtitle && <span className="text-gray-400">{subtitle}</span>}
        </div>
      )}
    </div>
  );
}

export default KPICard;
