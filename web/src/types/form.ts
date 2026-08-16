export interface FormField {
  name: string;
  label: string;
  type: "text" | "number" | "email" | "password" | "select" | "textarea" | "date" | "toggle";
  placeholder?: string;
  required?: boolean;
  options?: { label: string; value: string }[];
  rows?: number;
  colSpan?: 1 | 2;
  validation?: (value: unknown) => string | undefined;
}

export interface DropdownItem {
  label: string;
  onClick: () => void;
  danger?: boolean;
  icon?: React.ReactNode;
}
