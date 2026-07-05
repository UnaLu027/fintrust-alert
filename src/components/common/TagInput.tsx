import { useState, type KeyboardEvent } from "react";

interface TagInputProps {
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  suggestions?: string[];
}

export function TagInput({ values, onChange, placeholder, suggestions }: TagInputProps) {
  const [draft, setDraft] = useState("");

  function commitDraft() {
    const trimmed = draft.trim();
    if (trimmed && !values.includes(trimmed)) {
      onChange([...values, trimmed]);
    }
    setDraft("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commitDraft();
    }
  }

  function removeTag(tag: string) {
    onChange(values.filter((v) => v !== tag));
  }

  function addSuggestion(tag: string) {
    if (!values.includes(tag)) onChange([...values, tag]);
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 rounded-md border border-brand-border bg-white p-2">
        {values.map((tag) => (
          <span
            key={tag}
            className="flex items-center gap-1 rounded-full bg-brand-sky px-2.5 py-1 text-xs font-medium text-brand-blue"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              className="text-brand-blue/60 hover:text-brand-blue"
              aria-label={`移除 ${tag}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={commitDraft}
          placeholder={placeholder}
          className="min-w-[120px] flex-1 border-none text-sm outline-none"
        />
      </div>
      {suggestions && suggestions.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {suggestions
            .filter((s) => !values.includes(s))
            .map((s) => (
              <button
                type="button"
                key={s}
                onClick={() => addSuggestion(s)}
                className="rounded-full border border-brand-border px-2 py-0.5 text-xs text-brand-muted hover:border-brand-blue hover:text-brand-blue"
              >
                + {s}
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
