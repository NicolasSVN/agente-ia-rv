export function SkeletonLoader({ className = '' }) {
  return (
    <div className={`animate-pulse bg-border/50 rounded ${className}`} />
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="bg-card rounded-card border border-border p-5 shadow-card">
      <div className="flex justify-between items-start mb-3">
        <SkeletonLoader className="h-5 w-32" />
        <SkeletonLoader className="h-5 w-16 rounded-full" />
      </div>
      <SkeletonLoader className="h-4 w-24 mb-3" />
      <div className="flex gap-2 mb-4">
        <SkeletonLoader className="h-6 w-14 rounded" />
        <SkeletonLoader className="h-6 w-14 rounded" />
        <SkeletonLoader className="h-6 w-14 rounded" />
      </div>
      <div className="flex justify-between items-center pt-3 border-t border-border">
        <SkeletonLoader className="h-4 w-28" />
        <SkeletonLoader className="h-4 w-12" />
      </div>
    </div>
  );
}
