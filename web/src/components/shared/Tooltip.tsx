import { useState } from "react";

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  className?: string;
}

export const Tooltip = ({ content, children, className }: TooltipProps) => {
  const [show, setShow] = useState(false);

  return (
    <div
      className={`relative inline-block ${className || ""}`}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1.5 text-2xs font-medium text-white bg-gray-900 rounded-lg shadow-elevated whitespace-nowrap animate-fade pointer-events-none">
          {content}
        </div>
      )}
    </div>
  );
};
