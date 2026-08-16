import { forwardRef } from "react";
import { clsx } from "clsx";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => (
    <div>
      {label && <label className="block text-2xs font-medium text-gray-500 mb-1">{label}</label>}
      <input ref={ref} className={clsx("input", error && "border-danger", className)} {...props} />
      {error && <p className="text-2xs text-danger mt-1">{error}</p>}
    </div>
  )
);

Input.displayName = "Input";
