import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'
import './AgentMode.css'

// --- GENERATIVE UI COMPONENTS ---
const ActionList = ({ data, onActionClick }) => (
  <div className="generative-action-list">
    <div className="action-list-header">
      <span className="badge">Next steps</span>
      <h3>{data.title || "What to do right now"}</h3>
    </div>
    <div className="action-items">
      {data.items.map((item, idx) => (
        <button key={idx} className="action-item-btn" onClick={() => onActionClick(item.label)}>
          <span className="action-icon">{item.icon || ">_"}</span>
          <span className="action-label">{item.label}</span>
          <span className="action-arrow">↗</span>
        </button>
      ))}
    </div>
  </div>
);

const PhaseGrid = ({ data }) => (
  <div className="generative-phase-grid">
    <div className="phase-grid-header">
      <span className="badge">Build phases</span>
      <h3>{data.title || "How to build it step by step"}</h3>
    </div>
    <div className="phase-cards">
      {data.cards.map((card, idx) => (
        <div key={idx} className="phase-card">
          <div className="phase-card-subtitle">{card.subtitle}</div>
          <h4 className="phase-card-title">{card.title}</h4>
          <p className="phase-card-desc">{card.description}</p>
          {card.badge && <span className={`phase-card-badge ${card.badgeColor || 'green'}`}>{card.badge}</span>}
        </div>
      ))}
    </div>
  </div>
);

const TerminalCommand = ({ data, onRunCommand }) => {
  const [status, setStatus] = useState('idle');

  return (
    <div className="generative-terminal">
      <div className="terminal-header">
        <span className="badge yellow">Requires Approval</span>
        <span className="terminal-desc">{data.description}</span>
      </div>
      <div className="terminal-code">
        <code>{data.command}</code>
      </div>
      <button 
        className={`terminal-run-btn ${status}`} 
        onClick={async () => {
          setStatus('running');
          await onRunCommand(data.command);
          setStatus('done');
        }}
        disabled={status !== 'idle'}
      >
        {status === 'idle' ? "Approve & Run >_" : status === 'running' ? "Executing..." : "Executed ✓"}
      </button>
    </div>
  );
};

const BrowserAutomation = ({ data, onRunScript }) => {
  const [status, setStatus] = useState('idle');

  return (
    <div className="generative-terminal">
      <div className="terminal-header">
        <span className="badge blue">Browser Subagent</span>
        <span className="terminal-desc">{data.description}</span>
      </div>
      <div className="terminal-code" style={{color: '#00ccff'}}>
        <code>{data.script}</code>
      </div>
      <button 
        className={`terminal-run-btn ${status}`} 
        style={status === 'idle' ? {background: 'linear-gradient(135deg, #0096ff, #0055ff)', color: '#fff'} : {}}
        onClick={async () => {
          setStatus('running');
          await onRunScript(data.script);
          setStatus('done');
        }}
        disabled={status !== 'idle'}
      >
        {status === 'idle' ? "Launch Subagent 🌐" : status === 'running' ? "Browsing..." : "Finished ✓"}
      </button>
    </div>
  );
};
// --------------------------------


function App() {
  const [messages, setMessages] = useState([])
  const [keyStatus, setKeyStatus] = useState(null)
  const [localStatus, setLocalStatus] = useState(null)
  const [conversations, setConversations] = useState([])
  const [activeConvId, setActiveConvId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)

  // Agent Mode States
  const [isAgentMode, setIsAgentMode] = useState(false)
  const [agentFeed, setAgentFeed] = useState([])
  const [pendingApproval, setPendingApproval] = useState(null)

  // Metrics Dashboard States
  const [metricsOpen, setMetricsOpen] = useState(false)
  const [metrics, setMetrics] = useState({
    local_requests: 0,
    cloud_requests: 0,
    local_tokens: 0,
    cloud_tokens: 0,
    estimated_savings: 0.0
  })

  // Load all conversations on mount
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/conversations');
        const data = await res.json();
        const convs = data.conversations || [];
        setConversations(convs);
        // Load the most recent conversation
        if (convs.length > 0) {
          loadConversation(convs[0].id);
        } else {
          // First ever launch — show welcome message
          setMessages([{ id: 1, sender: 'leif', text: "Hey Harry! I've been upgraded with conversation memory. Each chat is now saved separately, just like ChatGPT. What are we building today?" }]);
        }
      } catch (err) {
        console.error("Could not fetch conversations:", err);
      }
    };
    fetchConversations();
  }, []);

  const loadConversation = async (convId) => {
    setActiveConvId(convId);
    try {
      const res = await fetch(`http://localhost:8000/api/conversations/${convId}/messages`);
      const data = await res.json();
      setMessages(data.history && data.history.length > 0 ? data.history : []);
    } catch (err) {
      console.error("Could not load conversation:", err);
    }
  };

  const startNewChat = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/conversations', { method: 'POST' });
      const data = await res.json();
      setActiveConvId(data.id);
      setMessages([]);
      setConversations(prev => [{ id: data.id, title: 'New Chat', message_count: 0 }, ...prev]);
    } catch (err) {
      console.error("Could not create conversation:", err);
    }
  };

  const deleteConversation = async (e, convId) => {
    e.stopPropagation();
    try {
      await fetch(`http://localhost:8000/api/conversations/${convId}`, { method: 'DELETE' });
      const remaining = conversations.filter(c => c.id !== convId);
      setConversations(remaining);
      if (activeConvId === convId) {
        if (remaining.length > 0) loadConversation(remaining[0].id);
        else { setActiveConvId(null); setMessages([]); }
      }
    } catch (err) {
      console.error("Could not delete conversation:", err);
    }
  };

  const copyConversationToClipboard = async () => {
    if (!messages || messages.length === 0) return;
    const textToCopy = messages.map(m => {
      const role = m.sender === 'user' ? 'User' : 'Leif';
      return `${role}:\n${m.text}`;
    }).join('\n\n----------------------------------------\n\n');
    
    try {
      await navigator.clipboard.writeText(textToCopy);
      alert('Conversation copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy conversation:', err);
      alert('Failed to copy conversation. Check console for details.');
    }
  };

  // Poll status every 30 seconds
  useEffect(() => {
    const fetchKeyStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/key-status');
        const data = await res.json();
        setKeyStatus(data);
      } catch (_) { /* silent fail */ }
    };
    
    const fetchLocalStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/local-status');
        const data = await res.json();
        setLocalStatus(data);
      } catch (_) { /* silent fail */ }
    };

    const fetchMetrics = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/metrics');
        const data = await res.json();
        setMetrics(data);
      } catch (_) { /* silent fail */ }
    };

    fetchKeyStatus();
    fetchLocalStatus();
    fetchMetrics();
    const interval = setInterval(() => {
      fetchKeyStatus();
      fetchLocalStatus();
      fetchMetrics();
    }, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const [inputText, setInputText] = useState('')
  
  // Reference to auto-scroll to the bottom of the chat
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const [attachedFile, setAttachedFile] = useState(null)

  // Auto-scroll function
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Trigger scroll whenever messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Reusable send function (for text input OR button clicks)
  const sendMessage = async (text, fileOverride = null) => {
    if (!text.trim() && !attachedFile && !fileOverride) return
    if (isProcessing) return

    setIsProcessing(true)
    const file = fileOverride || attachedFile;
    const displayText = file ? `${text}\n\n📎 *${file.name}*` : text;

    // Ensure we have an active conversation
    let convId = activeConvId;
    if (!convId) {
      const res = await fetch('http://localhost:8000/api/conversations', { method: 'POST' });
      const data = await res.json();
      convId = data.id;
      setActiveConvId(convId);
      setConversations(prev => [{ id: convId, title: 'New Chat', message_count: 0 }, ...prev]);
    }

    const newMessages = [...messages, { id: Date.now(), sender: 'user', text: displayText }];
    setMessages(newMessages)
    setInputText('')
    setAttachedFile(null)

    const typingId = Date.now() + 1;
    setMessages(prev => [...prev, { id: typingId, sender: 'leif', text: "..." }]);

    try {
      let response;
      const formData = new FormData();
      formData.append('message', text);
      formData.append('conversation_id', convId);
      if (file) formData.append('file', file);

      response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "API Server Error");
      }
      
      const data = await response.json();

      // Update the conversation title in sidebar (backend auto-generates it)
      setConversations(prev => prev.map(c =>
        c.id === convId ? { ...c, title: text.slice(0, 50) } : c
      ));
      
      setMessages(prev => prev.map(msg => 
        msg.id === typingId ? { ...msg, text: data.response } : msg
      ));

    } catch (error) {
      console.error(error);
      setMessages(prev => prev.map(msg => 
        msg.id === typingId ? { ...msg, text: `⚠️ Leif API Error: ${error.message}` } : msg
      ));
    } finally {
      setIsProcessing(false)
    }
  }

  // Handle Agent Loop SSE Stream
  // Handle Agent Loop SSE Stream
  const startAgentLoop = async (task) => {
    if (!task.trim()) return;
    if (isProcessing) return;

    setIsProcessing(true);
    setAgentFeed([{ type: 'status', message: `🚀 Starting task: ${task}` }]);
    setInputText('');
    setAttachedFile(null);

    try {
      const response = await fetch('http://localhost:8000/api/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task })
      });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        
        // Process all complete chunks
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              setAgentFeed(prev => [...prev, data]);
              if (data.type === 'requires_approval') {
                setPendingApproval(data);
              }
            } catch (e) {
              console.error("SSE Parse Error", e);
            }
          }
        }
        // Keep the incomplete chunk in the buffer
        buffer = lines[lines.length - 1];
      }
    } catch (err) {
      setAgentFeed(prev => [...prev, { type: 'error', message: err.message }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApproval = async (approved) => {
    if (!pendingApproval) return;
    const currentId = pendingApproval.approval_id;
    setPendingApproval(null); // Optimistically close modal
    
    try {
      await fetch('http://localhost:8000/api/agent/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approval_id: currentId, approved })
      });
    } catch (err) {
      console.error(err);
    }
  };

  // Handle Terminal Execution
  const executeCommand = async (command) => {
    try {
      const response = await fetch('http://localhost:8000/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      });
      const data = await response.json();
      
      // Feed the output back into Leif's brain!
      await sendMessage(`[Terminal Output for \`${command}\`]\n\n\`\`\`\n${data.output}\n\`\`\`\n\nWhat should we do next?`);
    } catch (error) {
      await sendMessage(`[Terminal Error]\n\n${error.message}`);
    }
  };

  // Handle Browser Subagent Execution
  const executeBrowse = async (script) => {
    try {
      const response = await fetch('http://localhost:8000/api/browse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script })
      });
      const data = await response.json();
      
      await sendMessage(`[Browser Output]\n\n\`\`\`\n${data.output}\n\`\`\`\n\nWhat should we do next?`);
    } catch (error) {
      await sendMessage(`[Browser Error]\n\n${error.message}`);
    }
  };

  // Handle Enter key form submission
  const handleSend = async (e) => {
    e.preventDefault()
    if (isAgentMode) {
      await startAgentLoop(inputText);
    } else {
      await sendMessage(inputText);
    }
  }

  // Handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) setAttachedFile(file);
    e.target.value = ''; // reset so same file can be re-selected
  }

  return (
    <div className="app-container">

      {/* SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={startNewChat}>
            <span>✏️</span> New Chat
          </button>
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(o => !o)} title="Toggle sidebar">
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>
        <div className="sidebar-conversations">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`conv-item ${activeConvId === conv.id ? 'active' : ''}`}
              onClick={() => loadConversation(conv.id)}
            >
              <span className="conv-icon">💬</span>
              <span className="conv-title">{conv.title || 'New Chat'}</span>
              <button
                className="conv-delete"
                onClick={(e) => deleteConversation(e, conv.id)}
                title="Delete"
              >🗑</button>
            </div>
          ))}
        </div>
      </aside>

      {/* MAIN CHAT WINDOW */}
      <div className="chat-window">
        
        {/* Header */}
        <header className="chat-header">
          <button className="sidebar-toggle-mobile" onClick={() => setSidebarOpen(o => !o)}>☰</button>
          <div className="avatar-container">
            <img src="/leif-avatar.png" alt="Leif Avatar" className="leif-avatar" />
            <div className="status-dot"></div>
          </div>
          <div className="header-info">
            <h1>Leif</h1>
            <p>Your Personal AI Assistant</p>
          </div>
          
          <div className="mode-toggle">
            <span className={!isAgentMode ? 'active' : ''}>Chat</span>
            <label className="switch">
              <input type="checkbox" checked={isAgentMode} onChange={() => setIsAgentMode(!isAgentMode)} />
              <span className="slider round"></span>
            </label>
            <span className={isAgentMode ? 'active-agent' : ''} style={isAgentMode ? {color: '#eab308', fontWeight: 'bold'} : {}}>Agent</span>
          </div>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
            <button 
              className={`metrics-toggle-btn ${metricsOpen ? 'active' : ''}`} 
              onClick={() => setMetricsOpen(!metricsOpen)}
              title="Toggle Metrics Dashboard"
              style={{ padding: '0.5rem', background: metricsOpen ? 'var(--primary)' : 'var(--bg-card)', color: metricsOpen ? '#fff' : 'var(--text-secondary)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', cursor: 'pointer' }}
            >
              📊 Metrics
            </button>
            <button 
              className="copy-conv-btn" 
              onClick={copyConversationToClipboard}
              title="Copy Entire Conversation"
              style={{ padding: '0.5rem', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', cursor: 'pointer', color: 'var(--text-secondary)' }}
            >
              📋 Copy
            </button>
          </div>
        </header>

        {/* Metrics Dashboard Panel */}
        {metricsOpen && (
          <div className="metrics-dashboard-panel" style={{ padding: '1rem', background: 'var(--bg-panel)', borderBottom: '1px solid var(--border)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div className="metric-card" style={{ background: 'var(--bg-card)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Model Usage Ratio</h4>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                {metrics.local_requests + metrics.cloud_requests > 0 
                  ? Math.round((metrics.local_requests / (metrics.local_requests + metrics.cloud_requests)) * 100) 
                  : 0}% Local
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {metrics.local_requests} Local / {metrics.cloud_requests} Cloud
              </div>
            </div>
            
            <div className="metric-card" style={{ background: 'var(--bg-card)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Tokens Processed</h4>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>
                {metrics.local_tokens.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Local Tokens Saved
              </div>
            </div>

            <div className="metric-card" style={{ background: 'var(--bg-card)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Cloud Tokens Spent</h4>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f59e0b' }}>
                {metrics.cloud_tokens.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Escalated Tokens
              </div>
            </div>

            <div className="metric-card" style={{ background: 'var(--bg-card)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Estimated Savings</h4>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#0ea5e9' }}>
                ${metrics.estimated_savings.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                vs Gemini API Cost
              </div>
            </div>
          </div>
        )}

        {/* Key Status Panel */}
        {keyStatus && (
          <div className="key-status-panel">
            <div className="key-status-title">
              <span>API Key Pool</span>
              <span className="key-status-model">{keyStatus.primary_model}</span>
            </div>
            <div className="key-status-grid">
              {keyStatus.keys.map((k) => (
                <div key={k.index} className={`key-pill ${k.status}`}>
                  <span className="key-pill-dot" />
                  <span className="key-pill-label">Key {k.index} <span className="key-hint">{k.key_hint}</span></span>
                  {k.status === 'exhausted' && (
                    <span className="key-pill-reset">resets in {k.resets_in}</span>
                  )}
                  {k.status === 'active' && (
                    <span className="key-pill-active">ACTIVE</span>
                  )}
                </div>
              ))}
            </div>
            
            {localStatus && localStatus.enabled && (
              <div className="local-status-panel">
                <span className="key-status-title">Tier 0 Brain</span>
                <div className={`key-pill ${localStatus.online ? 'active' : 'exhausted'}`}>
                  <span className="key-pill-dot" />
                  <span className="key-pill-label">Local LLM <span className="key-hint">{localStatus.model}</span></span>
                  <span className={localStatus.online ? 'key-pill-active' : 'key-pill-reset'}>
                    {localStatus.online ? 'ONLINE' : 'OFFLINE'}
                  </span>
                </div>
              </div>
            )}

            {keyStatus && keyStatus.has_groq_fallback && keyStatus.keys.every(k => k.status === 'exhausted') && (
              <div className="local-status-panel" style={{ marginTop: '0.5rem' }}>
                <span className="key-status-title" style={{ color: '#0ea5e9' }}>Tier 3 Fallback Brain</span>
                <div className="key-pill active" style={{ borderColor: '#0ea5e9', background: 'rgba(14, 165, 233, 0.1)' }}>
                  <span className="key-pill-dot" style={{ backgroundColor: '#0ea5e9' }} />
                  <span className="key-pill-label" style={{ color: '#fff' }}>Groq <span className="key-hint" style={{ color: '#bae6fd' }}>{keyStatus.groq_model}</span></span>
                  <span className="key-pill-active" style={{ color: '#0ea5e9' }}>ACTIVE</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Messages / Agent Feed */}
        <main className="messages-container">
          {!isAgentMode ? (
            <>
              {messages.length === 0 && (
                <div className="empty-state">
                  <span>💬</span>
                  <p>Start a new conversation</p>
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={`message-wrapper ${msg.sender}`}>
                  <div className="message-sender-label">
                    {msg.sender === 'user' ? 'You' : 'Leif'}
                  </div>
                  <div className="message-bubble">
                    <ReactMarkdown
                      components={{
                        code(props) {
                          const {children, className, ...rest} = props
                          const match = /language-(\w+)/.exec(className || '')
                          if (match && match[1] === 'json') {
                             try {
                               const data = JSON.parse(String(children).replace(/\n$/, ''));
                               if (data.ui_type === 'action_list') return <ActionList data={data} onActionClick={sendMessage} />;
                               if (data.ui_type === 'phase_grid') return <PhaseGrid data={data} />;
                               if (data.ui_type === 'terminal_command') return <TerminalCommand data={data} onRunCommand={executeCommand} />;
                               if (data.ui_type === 'browser_automation') return <BrowserAutomation data={data} onRunScript={executeBrowse} />;
                             } catch(_) {}
                          }
                          return <code {...rest} className={className}>{children}</code>
                        }
                      }}
                    >
                      {msg.text}
                    </ReactMarkdown>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className="agent-feed">
              {agentFeed.length === 0 && (
                <div className="empty-state">
                  <span>🤖</span>
                  <p>Agent Mode is active. Give Leif a task!</p>
                </div>
              )}
              {agentFeed.map((event, idx) => (
                <div key={idx} className={`agent-event ${event.type}`}>
                  {event.type === 'status' && <div className="event-status">{event.message}</div>}
                  {event.type === 'thought' && <div className="event-thought">🧠 {event.message}</div>}
                  {event.type === 'action_result' && (
                    <div className="event-result">
                      <strong>Result of {event.tool}:</strong>
                      <pre>{event.result}</pre>
                    </div>
                  )}
                  {event.type === 'done' && <div className="event-done">✅ {event.message}</div>}
                  {event.type === 'error' && <div className="event-error">❌ {event.message}</div>}
                  {event.type === 'requires_approval' && <div className="event-wait">⏳ Waiting for your approval...</div>}
                </div>
              ))}
            </div>
          )}
          <div ref={messagesEndRef} />
        </main>

        {/* Approval Modal */}
        {pendingApproval && (
          <div className="approval-modal-overlay">
            <div className="approval-modal">
              <h2>⚠️ Action Requires Approval</h2>
              <p>Leif wants to execute the following <strong>{pendingApproval.tool}</strong> action:</p>
              
              <div className="approval-details">
                {pendingApproval.tool === 'terminal_run' && (
                  <pre><code>{pendingApproval.args.command}</code></pre>
                )}
                {pendingApproval.tool === 'file_write' && (
                  <>
                    <p><strong>File:</strong> {pendingApproval.args.path}</p>
                    <pre><code>{pendingApproval.args.content.substring(0, 500)}{pendingApproval.args.content.length > 500 ? '...\n[Content Truncated]' : ''}</code></pre>
                  </>
                )}
              </div>
              
              <div className="approval-actions">
                <button className="reject-btn" onClick={() => handleApproval(false)}>Reject</button>
                <button className="approve-btn" onClick={() => handleApproval(true)}>Approve</button>
              </div>
            </div>
          </div>
        )}

        {/* Input */}
        <form className="input-area" onSubmit={handleSend}>
          <input ref={fileInputRef} type="file" style={{ display: 'none' }}
            accept="image/*,.pdf,.txt,.py,.js,.jsx,.ts,.tsx,.json,.md,.csv"
            onChange={handleFileChange}
          />
          {attachedFile && (
            <div className="attachment-chip">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                {attachedFile.name}
              </span>
              <button type="button" className="attachment-remove" onClick={() => setAttachedFile(null)}>✕</button>
            </div>
          )}
          <div className="input-row">
            <button type="button" className="attach-button" onClick={() => fileInputRef.current?.click()} title="Attach file" disabled={isProcessing}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
            </button>
            <input type="text" className="chat-input" placeholder={isProcessing ? "Leif is thinking..." : "Talk to Leif..."}
              value={inputText} onChange={(e) => setInputText(e.target.value)} autoComplete="off" disabled={isProcessing}
            />
            <button type="submit" className="send-button" disabled={isProcessing || (!inputText.trim() && !attachedFile)}>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default App
