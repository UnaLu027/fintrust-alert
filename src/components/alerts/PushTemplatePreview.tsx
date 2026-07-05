import { useState } from "react";

export function PushTemplatePreview({ message }: { message: string }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="text-xs font-medium text-brand-blue hover:underline"
      >
        {isOpen ? "隱藏推播內容" : "查看完整推播內容"}
      </button>
      {isOpen && (
        <p className="mt-2 whitespace-pre-line rounded-md bg-brand-surface p-3 text-xs leading-relaxed text-brand-navy">
          {message}
        </p>
      )}
    </div>
  );
}
