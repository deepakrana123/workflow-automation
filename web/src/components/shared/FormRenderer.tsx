import { clsx } from "clsx";
import { Input } from "./Input";
import { Select } from "./Select";
import { Textarea } from "./Textarea";
import { DatePicker } from "./DatePicker";
import { Toggle } from "./Toggle";
import type { FormField } from "@/types/form";

interface FormRendererProps {
  fields: FormField[];
  values: Record<string, unknown>;
  onChange: (values: Record<string, unknown>) => void;
  onSubmit: (e: React.FormEvent) => void;
  submitLabel?: string;
  onCancel?: () => void;
  cancelLabel?: string;
  columns?: 1 | 2;
  className?: string;
}

export const FormRenderer = ({
  fields,
  values,
  onChange,
  onSubmit,
  submitLabel = "Submit",
  onCancel,
  cancelLabel = "Cancel",
  columns = 2,
  className,
}: FormRendererProps) => {
  const handleChange = (name: string, value: unknown) => {
    onChange({ ...values, [name]: value });
  };

  return (
    <form onSubmit={onSubmit} className={clsx("space-y-4", className)}>
      <div className={clsx("grid gap-3", columns === 2 ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1")}>
        {fields.map((field) => {
          const colClass = field.colSpan === 2 ? "sm:col-span-2" : "";
          const value = values[field.name];

          switch (field.type) {
            case "select":
              return (
                <div key={field.name} className={colClass}>
                  <Select
                    label={field.label}
                    value={(value as string) || ""}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    options={field.options || []}
                    required={field.required}
                  />
                </div>
              );

            case "textarea":
              return (
                <div key={field.name} className={colClass}>
                  <Textarea
                    label={field.label}
                    value={(value as string) || ""}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    rows={field.rows || 3}
                    placeholder={field.placeholder}
                    required={field.required}
                  />
                </div>
              );

            case "date":
              return (
                <div key={field.name} className={colClass}>
                  <DatePicker
                    label={field.label}
                    value={(value as string) || ""}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    required={field.required}
                  />
                </div>
              );

            case "toggle":
              return (
                <div key={field.name} className={clsx(colClass, "flex items-center pt-5")}>
                  <Toggle
                    label={field.label}
                    checked={!!value}
                    onChange={(checked) => handleChange(field.name, checked)}
                  />
                </div>
              );

            default:
              return (
                <div key={field.name} className={colClass}>
                  <Input
                    label={field.label}
                    type={field.type}
                    value={(value as string) || ""}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                    required={field.required}
                  />
                </div>
              );
          }
        })}
      </div>

      <div className="flex items-center gap-2 pt-1">
        <button type="submit" className="btn-primary">{submitLabel}</button>
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">{cancelLabel}</button>
        )}
      </div>
    </form>
  );
};
