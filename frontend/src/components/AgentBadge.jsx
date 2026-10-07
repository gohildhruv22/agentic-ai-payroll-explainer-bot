/**
 * Pill label showing which AI agent answered (icon + colors per agent name).
 */
import { Calculator, Shield, BookOpen, AlertTriangle, Bot } from 'lucide-react';

const agentConfig = {
  'Payroll Calculator': { icon: Calculator, color: 'bg-blue-100 text-blue-700', border: 'border-blue-200' },
  'Compliance Agent': { icon: Shield, color: 'bg-emerald-100 text-emerald-700', border: 'border-emerald-200' },
  'Policy Explainer': { icon: BookOpen, color: 'bg-purple-100 text-purple-700', border: 'border-purple-200' },
  'Dispute Resolver': { icon: AlertTriangle, color: 'bg-amber-100 text-amber-700', border: 'border-amber-200' },
  'General Assistant': { icon: Bot, color: 'bg-gray-100 text-gray-700', border: 'border-gray-200' },
};

export default function AgentBadge({ agent }) {
  const config = agentConfig[agent] || agentConfig['General Assistant'];
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${config.color} ${config.border}`}>
      <Icon size={12} />
      {agent}
    </span>
  );
}
