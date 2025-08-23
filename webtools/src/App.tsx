import { useState, useEffect } from 'react'
import './App.css'
import traceData from './assets/trace.json'

interface TraceItem {
  func: string
  impl: string
  rules: string[]
  args: string[]
  kwargs: Record<string, any>
  choice_kwargs: Record<string, any>
  items: TraceItem[]
}

interface RegistryEntry {
  interface: string
  funcs: string[]
  rules: string[]
}

interface TraceData {
  items: TraceItem[]
  registry: Record<string, RegistryEntry>
}

function App() {
  const [data] = useState<TraceData>(traceData)

  const renderTraceItem = (item: TraceItem, depth: number = 0) => {
    const indent = depth * 20
    return (
      <div key={`${item.func}-${depth}`} style={{ marginLeft: `${indent}px`, marginBottom: '10px' }}>
        <div className="trace-item">
          <h4>Function: {item.func}</h4>
          <p><strong>Implementation:</strong> {item.impl}</p>
          <p><strong>Args:</strong> [{item.args.join(', ')}]</p>
          {item.rules.length > 0 && (
            <p><strong>Rules:</strong> [{item.rules.join(', ')}]</p>
          )}
          {Object.keys(item.kwargs).length > 0 && (
            <p><strong>Kwargs:</strong> {JSON.stringify(item.kwargs)}</p>
          )}
          {Object.keys(item.choice_kwargs).length > 0 && (
            <p><strong>Choice Kwargs:</strong> {JSON.stringify(item.choice_kwargs)}</p>
          )}
          {item.items.length > 0 && (
            <div>
              <strong>Nested Items:</strong>
              {item.items.map((nestedItem, index) => 
                renderTraceItem(nestedItem, depth + 1)
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>PyChoice Trace Viewer</h1>
      </header>
      
      <main style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <section>
          <h2>Trace Items</h2>
          <div className="trace-items">
            {data.items.length > 0 ? (
              data.items.map((item, index) => renderTraceItem(item))
            ) : (
              <p>No trace items found.</p>
            )}
          </div>
        </section>

        <section style={{ marginTop: '40px' }}>
          <h2>Registry</h2>
          <div className="registry">
            {Object.entries(data.registry).map(([key, entry]) => (
              <div key={key} className="registry-entry">
                <h3>{key}</h3>
                <p><strong>Interface:</strong> {entry.interface}</p>
                <p><strong>Functions:</strong> [{entry.funcs.join(', ')}]</p>
                <div>
                  <strong>Rules:</strong>
                  <ul>
                    {entry.rules.map((rule, index) => (
                      <li key={index}>{rule}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
