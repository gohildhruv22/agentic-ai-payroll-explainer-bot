/**
 * Horizontal chips of example questions; clicking fills/sends a prompt in Chat.
 */
import { Sparkles } from 'lucide-react';

const defaultPrompts = [
  "What is my take-home salary this month?",
  "Compare old vs new tax regime for me",
  "How many leaves do I have left?",
  "Explain my latest payslip deductions",
];

export default function SuggestedPrompts({ onSelect, prompts }) {
  const items = prompts || defaultPrompts;

  return (
    <div className="flex flex-wrap gap-2 mb-3">
      {items.map((prompt, i) => (
        <button
          key={i}
          onClick={() => onSelect(prompt)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200
                     bg-white text-xs text-gray-600 hover:border-primary-300 hover:text-primary-700
                     hover:bg-primary-50 transition-all duration-200"
        >
          <Sparkles size={12} className="text-primary-400" />
          {prompt}
        </button>
      ))}
    </div>
  );
}
