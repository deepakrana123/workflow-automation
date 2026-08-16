import { forwardRef } from "react";
import { clsx } from "clsx";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, ...props }, ref) => (
    <div>
      {label && <label className="block text-2xs font-medium text-gray-500 mb-1">{label}</label>}
      <textarea ref={ref} className={clsx("textarea", error && "border-danger", className)} {...props} />
      {error && <p className="text-2xs text-danger mt-1">{error}</p>}
    </div>
  )
);

Textarea.displayName = "Textarea";
