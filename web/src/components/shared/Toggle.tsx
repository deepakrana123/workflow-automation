interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  className?: string;
}

export const Toggle = ({ checked, onChange, label, className }: ToggleProps) => (
  <label className={`inline-flex items-center gap-2 cursor-pointer ${className || ""}`}>
    <div
      className={checked ? "toggle-track-on" : "toggle-track-off"}
      onClick={() => onChange(!checked)}
    >
      <div className={checked ? "toggle-thumb-on" : "toggle-thumb-off"} />
    </div>
    {label && <span className="text-sm text-gray-700">{label}</span>}
  </label>
);
