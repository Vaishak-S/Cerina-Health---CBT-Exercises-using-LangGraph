import { useState, useEffect, useRef } from 'react'
import './App.css'

interface ScratchpadEntry {
  agent: string
  content: string
  iteration: number
  timestamp: string
}

interface SafetyAssessment {
  level: string
  concerns: string[]
  recommendations: string[]
}

interface ClinicalAssessment {
  empathy_score: number
  structure_score: number
  clinical_appropriateness: number
  feedback: string
}

interface ProtocolState {
  protocol_id: string
  current_draft: string
  iteration_count: number
  safety_assessment?: SafetyAssessment
  clinical_assessment?: ClinicalAssessment
  scratchpad: ScratchpadEntry[]
  requires_human_approval: boolean
  completed: boolean
}

function App() {
  const [userIntent, setUserIntent] = useState('')
  const [userContext, setUserContext] = useState('')
  const [protocolId, setProtocolId] = useState<string | null>(null)
  const [state, setState] = useState<ProtocolState | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editedDraft, setEditedDraft] = useState('')
  const [humanFeedback, setHumanFeedback] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // WebSocket connection
  useEffect(() => {
    if (!protocolId) return

    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/${protocolId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'state_update') {
        fetchState()
      } else if (data.type === 'human_approval_required') {
        fetchState()
      } else if (data.type === 'error') {
        setError(data.message)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return () => {
      ws.close()
    }
  }, [protocolId])

  const fetchState = async () => {
    if (!protocolId) return

    try {
      const response = await fetch(`${API_BASE}/api/protocols/${protocolId}/state`)
      if (!response.ok) throw new Error('Failed to fetch state')
      
      const data = await response.json()
      setState(data)
      setEditedDraft(data.current_draft)
      
      // Stop loading when we have state
      if (data) {
        setLoading(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }

  // Polling effect - continuously fetch state while workflow is active
  useEffect(() => {
    if (!protocolId || state?.completed) return

    const pollInterval = setInterval(fetchState, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [protocolId, state?.completed])

  const handleCreateProtocol = async () => {
    if (!userIntent.trim()) {
      setError('Please enter a user intent')
      return
    }

    setLoading(true)
    setError(null)
    setState(null)

    try {
      const response = await fetch(`${API_BASE}/api/protocols`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_intent: userIntent,
          user_context: userContext || undefined
        })
      })

      if (!response.ok) throw new Error('Failed to create protocol')

      const data = await response.json()
      setProtocolId(data.protocol_id)
      
      // Poll for state updates
      setTimeout(fetchState, 1000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitFeedback = async (approved: boolean) => {
    if (!protocolId) {
      console.error('No protocol ID available')
      return
    }

    console.log(`Submitting feedback: approved=${approved}, protocolId=${protocolId}`)
    setLoading(true)
    setError(null)

    try {
      const payload = {
        approved,
        feedback: humanFeedback || undefined,
        edits: approved && editedDraft !== state?.current_draft ? editedDraft : undefined
      }
      
      console.log('Feedback payload:', payload)
      
      const response = await fetch(`${API_BASE}/api/protocols/${protocolId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Feedback submission failed:', response.status, errorText)
        throw new Error(`Failed to submit feedback: ${response.status}`)
      }

      const result = await response.json()
      console.log('Feedback submitted successfully:', result)

      // Clear feedback textarea after submission
      setHumanFeedback('')
      
      // Fetch updated state immediately
      await fetchState()
      
      // Continue polling if not completed
      if (!approved) {
        setTimeout(fetchState, 2000)
      }
    } catch (err) {
      console.error('Error submitting feedback:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getAgentColor = (agent: string) => {
    const colors: Record<string, string> = {
      drafter: '#4A90E2',
      safety_guardian: '#E24A4A',
      clinical_critic: '#9B59B6',
      supervisor: '#F39C12'
    }
    return colors[agent] || '#95A5A6'
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🏥 Cerina Protocol Foundry</h1>
        <p>Multi-Agent CBT Exercise Generator</p>
      </header>

      <div className="container">
        {!protocolId ? (
          <div className="input-section">
            <h2>Create New Protocol</h2>
            <div className="form-group">
              <label htmlFor="intent">User Intent *</label>
              <input
                id="intent"
                type="text"
                placeholder="e.g., Create an exposure hierarchy for agoraphobia"
                value={userIntent}
                onChange={(e) => setUserIntent(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="context">Additional Context (Optional)</label>
              <textarea
                id="context"
                placeholder="e.g., Patient is a 35-year-old experiencing moderate anxiety..."
                value={userContext}
                onChange={(e) => setUserContext(e.target.value)}
                disabled={loading}
                rows={4}
              />
            </div>
            <button 
              onClick={handleCreateProtocol} 
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? 'Starting Workflow...' : 'Generate Protocol'}
            </button>
          </div>
        ) : (
          <div className="workflow-section">
            <div className="workflow-header">
              <h2>
                {state?.completed 
                  ? '✅ Protocol Complete' 
                  : state?.requires_human_approval 
                    ? '⏸️ Awaiting Human Review' 
                    : '🔄 Protocol Generation in Progress'}
              </h2>
              <span className="protocol-id">ID: {protocolId}</span>
            </div>

            {error && (
              <div className="alert alert-error">
                <strong>Error:</strong> {error}
              </div>
            )}

            {!state && loading && (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>Initializing workflow and waiting for agents...</p>
              </div>
            )}

            {state && (
              <>
                {/* Agent Activity Log */}
                <div className="agents-panel">
                  <h3>🤖 Agent Deliberation</h3>
                  <div className="scratchpad">
                    {state.scratchpad.map((entry, idx) => (
                      <div 
                        key={idx} 
                        className="scratchpad-entry"
                        style={{ borderLeftColor: getAgentColor(entry.agent) }}
                      >
                        <div className="entry-header">
                          <strong style={{ color: getAgentColor(entry.agent) }}>
                            {entry.agent.replace('_', ' ').toUpperCase()}
                          </strong>
                          <span className="iteration">Iteration {entry.iteration}</span>
                        </div>
                        <p>{entry.content}</p>
                        <span className="timestamp">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Assessments */}
                <div className="assessments-panel">
                  {state.safety_assessment && (
                    <div className="assessment safety">
                      <h4>🛡️ Safety Assessment</h4>
                      <div className={`level level-${state.safety_assessment.level}`}>
                        {state.safety_assessment.level.toUpperCase()}
                      </div>
                      {state.safety_assessment.concerns.length > 0 && (
                        <div>
                          <strong>Concerns:</strong>
                          <ul>
                            {state.safety_assessment.concerns.map((c, i) => (
                              <li key={i}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {state.clinical_assessment && (
                    <div className="assessment clinical">
                      <h4>📊 Clinical Quality</h4>
                      <div className="scores">
                        <div className="score">
                          <span>Empathy:</span>
                          <strong>{state.clinical_assessment.empathy_score}/10</strong>
                        </div>
                        <div className="score">
                          <span>Structure:</span>
                          <strong>{state.clinical_assessment.structure_score}/10</strong>
                        </div>
                        <div className="score">
                          <span>Clinical:</span>
                          <strong>{state.clinical_assessment.clinical_appropriateness}/10</strong>
                        </div>
                      </div>
                      <p><em>{state.clinical_assessment.feedback}</em></p>
                    </div>
                  )}
                </div>

                {/* Current Draft */}
                {state.current_draft && (
                  <div className="draft-panel">
                    <h3>📝 Current Draft (Iteration {state.iteration_count})</h3>
                    <textarea
                      value={editedDraft}
                      onChange={(e) => setEditedDraft(e.target.value)}
                      rows={15}
                      className="draft-editor"
                      disabled={!state.requires_human_approval || state.completed}
                    />
                  </div>
                )}

                {/* Human Approval Interface */}
                {state.requires_human_approval && !state.completed && (
                  <div className="approval-panel">
                    <h3>⏸️ Human Review Required</h3>
                    <p>The agents have completed their deliberation. Please review the draft and provide feedback.</p>
                    
                    <div className="form-group">
                      <label>Feedback (Optional)</label>
                      <textarea
                        value={humanFeedback}
                        onChange={(e) => setHumanFeedback(e.target.value)}
                        placeholder="Provide any feedback or reasons for changes..."
                        rows={3}
                      />
                    </div>

                    <div className="button-group">
                      <button 
                        onClick={() => {
                          console.log('Request Revision button clicked')
                          handleSubmitFeedback(false)
                        }}
                        className="btn btn-secondary"
                        disabled={loading}
                      >
                        {loading ? 'Submitting...' : 'Request Revision'}
                      </button>
                      <button 
                        onClick={() => {
                          console.log('Approve Protocol button clicked')
                          handleSubmitFeedback(true)
                        }}
                        className="btn btn-success"
                        disabled={loading}
                      >
                        {loading ? 'Submitting...' : '✓ Approve Protocol'}
                      </button>
                    </div>
                  </div>
                )}

                {state.completed && (
                  <div className="alert alert-success">
                    <strong>✓ Workflow Complete!</strong> The protocol has been approved and saved.
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {protocolId && !state?.completed && (
          <button 
            onClick={() => {
              setProtocolId(null)
              setState(null)
              setUserIntent('')
              setUserContext('')
              setEditedDraft('')
              setHumanFeedback('')
            }}
            className="btn btn-secondary"
          >
            Start New Protocol
          </button>
        )}
      </div>
    </div>
  )
}

export default App
