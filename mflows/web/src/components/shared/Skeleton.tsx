import { clsx } from "clsx";

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
}

export const Skeleton = ({ className, width, height }: SkeletonProps) => (
  <div
    className={clsx("skeleton", className)}
    style={{ width: width || "100%", height: height || "1rem" }}
  />
);
