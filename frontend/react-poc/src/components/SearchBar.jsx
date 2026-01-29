import { useState } from 'react';

export function SearchBar({ value, onChange, placeholder = 'Buscar produtos...' }) {
  return (
    <div className="relative">
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-4 py-2.5 bg-card border border-border rounded-input
                   text-foreground placeholder:text-muted
                   focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
                   transition-colors"
      />
    </div>
  );
}
