import { forwardRef } from "react";
import { clsx } from "clsx";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { label: string; value: string }[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, className, ...props }, ref) => (
    <div>
      {label && <label className="block text-2xs font-medium text-gray-500 mb-1">{label}</label>}
      <select ref={ref} className={clsx("select", error && "border-danger", className)} {...props}>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && <p className="text-2xs text-danger mt-1">{error}</p>}
    </div>
  )
);

Select.displayName = "Select";
