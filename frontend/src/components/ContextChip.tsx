"use client";

import { XMarkIcon } from "@heroicons/react/24/outline";
import { ReactNode } from "react";

interface ContextChipProps {
  icon: string | ReactNode;
  label: string;
  onRemove: () => void;
  onEdit?: () => void;
}

export default function ContextChip({
  icon,
  label,
  onRemove,
  onEdit,
}: ContextChipProps) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-teal-100 text-teal-800 rounded-lg text-sm font-medium transition-colors hover:bg-teal-200">
      {typeof icon === "string" ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : (
        <div className="flex-shrink-0">{icon}</div>
      )}

      {onEdit ? (
        <button
          onClick={onEdit}
          className="hover:underline max-w-[200px] truncate"
          title={label}
        >
          {label}
        </button>
      ) : (
        <span className="max-w-[200px] truncate" title={label}>
          {label}
        </span>
      )}

      <button
        onClick={onRemove}
        className="ml-1 hover:text-teal-900 flex-shrink-0 w-4 h-4 flex items-center justify-center"
        aria-label="Supprimer"
        title="Supprimer"
      >
        <XMarkIcon className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
