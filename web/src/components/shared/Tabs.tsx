import { clsx } from "clsx";

interface TabsProps<T extends string> {
  value: T;
  onChange: (tab: T) => void;
  tabs: { label: string; value: T }[];
  className?: string;
}

export const Tabs = <T extends string>({ value, onChange, tabs, className }: TabsProps<T>) => (
  <div className={clsx("tabs-pill", className)}>
    {tabs.map((tab) => (
      <button
        key={tab.value}
        onClick={() => onChange(tab.value)}
        className={value === tab.value ? "tab-pill-active" : "tab-pill-inactive"}
      >
        {tab.label}
      </button>
    ))}
  </div>
);
