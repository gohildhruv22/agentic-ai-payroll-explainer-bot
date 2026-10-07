/**
 * AI chat UI: message list, suggested prompts, POST /api/chat, optional session id for history.
 */
import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import MessageBubble from '../components/MessageBubble';
import SuggestedPrompts from '../components/SuggestedPrompts';

export default function Chat({ sessionId, setSessionId, refreshSessions }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (sessionId) loadHistory(sessionId);
    else setMessages([]);
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async (sid) => {
    try {
      const res = await api.get(`/chat/history/${sid}`);
      setMessages(res.data.messages || []);
    } catch { /* fresh session */ }
  };

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    const userMsg = { role: 'user', message: msg, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/chat', { message: msg, session_id: sessionId || null });
      const { response, session_id, agent, intent } = res.data;

      if (!sessionId) setSessionId(session_id);

      const assistantMsg = {
        role: 'assistant',
        message: response,
        agent,
        intent,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);
      if (refreshSessions) refreshSessions();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to get response');
      setMessages(prev => [...prev, {
        role: 'assistant',
        message: 'I apologize, but I encountered an error processing your request. Please try again.',
        agent: 'System',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {isEmpty ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <div className="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mb-6">
              <Bot size={36} className="text-primary-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Hello, {user?.name?.split(' ')[0]}!</h2>
            <p className="text-sm text-gray-500 max-w-md mb-8">
              I'm your AI payroll assistant. Ask me about your salary, tax deductions,
              leave balance, company policies, or file a dispute.
            </p>
            <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
              {[
                { text: "What's my take-home salary this month?", emoji: "💰" },
                { text: "Compare old vs new tax regime", emoji: "📊" },
                { text: "How many leaves do I have?", emoji: "📅" },
                { text: "My HRA deduction seems incorrect", emoji: "⚠️" },
                { text: "Explain the leave encashment policy", emoji: "📋" },
                { text: "What is my PF contribution?", emoji: "🏦" },
              ].map((p, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(p.text)}
                  className="text-left p-3 rounded-xl border border-gray-200 hover:border-primary-300
                             hover:bg-primary-50 transition-all text-sm text-gray-600 hover:text-primary-700"
                >
                  <span className="mr-2">{p.emoji}</span>{p.text}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            {loading && (
              <div className="flex gap-3 items-start">
                <div className="w-8 h-8 rounded-full bg-primary-800 flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="max-w-3xl mx-auto">
          {!isEmpty && !loading && (
            <SuggestedPrompts onSelect={(p) => sendMessage(p)} />
          )}
          <div className="flex items-end gap-2">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your salary, taxes, leaves, policies..."
                rows={1}
                className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm
                           focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none
                           transition max-h-32 overflow-y-auto"
                style={{ minHeight: '44px' }}
              />
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="p-3 rounded-xl bg-primary-800 text-white hover:bg-primary-900
                         disabled:opacity-40 disabled:cursor-not-allowed transition-all flex-shrink-0"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
          <p className="text-[10px] text-gray-400 text-center mt-2">
            AI responses are generated using your payroll data. Always verify critical information with HR.
          </p>
        </div>
      </div>
    </div>
  );
}
