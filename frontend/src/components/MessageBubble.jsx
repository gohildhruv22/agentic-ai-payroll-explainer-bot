/**
 * Single chat message: user vs assistant styling, markdown rendering, optional agent badge.
 */
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import AgentBadge from './AgentBadge';
import { User, Bot } from 'lucide-react';

function cleanMessage(text) {
  if (!text) return '';
  return text.replace(/<\w+>[\s\S]*?<\/\w+>/g, '').trim();
}

const markdownComponents = {
  table: ({ children }) => (
    <div className="overflow-x-auto my-3 rounded-lg border border-gray-200 shadow-sm">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-gray-900 text-white">{children}</thead>
  ),
  th: ({ children }) => (
    <th className="px-4 py-2.5 text-left font-semibold text-xs uppercase tracking-wider whitespace-nowrap text-white">{children}</th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2.5 border-t border-gray-100 whitespace-nowrap">{children}</td>
  ),
  tr: ({ children, ...props }) => (
    <tr className="even:bg-gray-50 hover:bg-purple-50/50 transition-colors">{children}</tr>
  ),
};

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-violet-500 flex items-center justify-center mt-1 shadow-sm">
          <Bot size={16} className="text-white" />
        </div>
      )}
      <div className={`max-w-[75%] ${isUser ? 'order-first' : ''}`}>
        {!isUser && message.agent && (
          <div className="mb-1.5">
            <AgentBadge agent={message.agent} />
          </div>
        )}
        <div className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-gradient-to-r from-purple-600 to-violet-500 text-white rounded-tr-md shadow-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-md shadow-sm'
        }`}>
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.message}</p>
          ) : (
            <div className="prose text-sm leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {cleanMessage(message.message)}
              </ReactMarkdown>
            </div>
          )}
        </div>
        <p className={`text-xs mt-1 ${isUser ? 'text-right' : 'text-left'} text-gray-400`}>
          {message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
        </p>
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-violet-400 flex items-center justify-center mt-1 shadow-sm">
          <User size={16} className="text-white" />
        </div>
      )}
    </div>
  );
}
