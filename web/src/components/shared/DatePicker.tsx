import { forwardRef } from "react";
import { clsx } from "clsx";

interface DatePickerProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  error?: string;
}

export const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(
  ({ label, error, className, ...props }, ref) => (
    <div>
      {label && <label className="block text-2xs font-medium text-gray-500 mb-1">{label}</label>}
      <input ref={ref} type="date" className={clsx("input", error && "border-danger", className)} {...props} />
      {error && <p className="text-2xs text-danger mt-1">{error}</p>}
    </div>
  )
);

DatePicker.displayName = "DatePicker";
