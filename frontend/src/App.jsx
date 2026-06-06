import { useState } from 'react';
import './index.css';

const DEFAULT_CODE = `int main() {
    int x;
    x = 10;
    double y;
    y = 20.5;
    
    if (x < 20) {
        Print("Hello World");
    }
    
    return 0;
}`;

function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [activeTab, setActiveTab] = useState('tokens');
  const [compilerData, setCompilerData] = useState(null);
  const [isCompiling, setIsCompiling] = useState(false);

  const handleCompile = async () => {
    setIsCompiling(true);
    try {
      const response = await fetch('http://localhost:5000/api/compile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source_code: code }),
      });
      const data = await response.json();
      setCompilerData(data);
    } catch (error) {
      console.error("Compilation error:", error);
      alert("Failed to connect to the compiler backend. Is the Flask server running?");
    } finally {
      setIsCompiling(false);
    }
  };

  const renderTabContent = () => {
    if (!compilerData) {
      return <div style={{ color: 'var(--text-muted)' }}>Write some code and hit Compile to see results!</div>;
    }

    switch (activeTab) {
      case 'tokens':
        return (
          <div>
            <h3>Lexical Analysis (Tokens)</h3>
            <div style={{ marginTop: '1rem' }}>
              {compilerData.tokens.map((t, i) => (
                <span key={i} className="token-badge" title={`Line ${t.line}, Col ${t.column}`}>
                  {t.type}: {t.value || '<EOF>'}
                </span>
              ))}
            </div>
          </div>
        );
      case 'grammar':
        return (
          <div>
            <h3>Grammar (FIRST & FOLLOW sets)</h3>
            <h4>FIRST Sets:</h4>
            <div className="json-view">{JSON.stringify(compilerData.grammar.first, null, 2)}</div>
            <h4 style={{marginTop: '1rem'}}>FOLLOW Sets:</h4>
            <div className="json-view">{JSON.stringify(compilerData.grammar.follow, null, 2)}</div>
          </div>
        );
      case 'rd':
        return (
          <div>
            <h3>Recursive Descent Parse Tree</h3>
            <div className="json-view">{JSON.stringify(compilerData.parsers.rd, null, 2)}</div>
          </div>
        );
      case 'll1':
        return (
          <div>
            <h3>LL(1) Parsing Table & Trace</h3>
            <h4>Parse Trace:</h4>
            <div className="json-view">
              {compilerData.parsers.ll1.errors.length > 0 && (
                <div className="error-msg">{compilerData.parsers.ll1.errors.join('\n')}</div>
              )}
              {compilerData.parsers.ll1.trace.map((step, i) => (
                <div key={i}>
                  Step {i+1}: Stack: [{step.stack.join(', ')}] | Input: {step.input} | Action: {step.action}
                </div>
              ))}
            </div>
          </div>
        );
      case 'lr':
        return (
          <div>
            <h3>LR Parser Trace (SLR(1))</h3>
            <div className="json-view">
              {compilerData.parsers.lr.errors.length > 0 && (
                <div className="error-msg">{compilerData.parsers.lr.errors.join('\n')}</div>
              )}
              {compilerData.parsers.lr.trace.map((step, i) => (
                <div key={i}>
                  Step {i+1}: State Stack: [{step.stack.join(', ')}] | Input: {step.input} | Action: {step.action}
                </div>
              ))}
            </div>
          </div>
        );
      case 'symbol':
        return (
          <div>
            <h3>Symbol Table</h3>
            {compilerData.symbol_table.length === 0 ? (
              <p>No symbols recorded.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Kind</th>
                    <th>Type</th>
                    <th>Scope Level</th>
                    <th>Line</th>
                  </tr>
                </thead>
                <tbody>
                  {compilerData.symbol_table.map((sym, i) => (
                    <tr key={i}>
                      <td>{sym.name}</td>
                      <td>{sym.kind}</td>
                      <td>{sym.type}</td>
                      <td>{sym.scope_level}</td>
                      <td>{sym.line_number}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        );
      case 'errors':
        return (
          <div>
            <h3>Compiler Errors</h3>
            {Object.entries(compilerData.errors).map(([phase, errs]) => (
              <div key={phase}>
                <h4>{phase.charAt(0).toUpperCase() + phase.slice(1)} Errors ({errs.length}):</h4>
                {errs.length > 0 ? (
                  errs.map((e, i) => <div key={i} className="error-msg">{e}</div>)
                ) : (
                  <p style={{ color: 'var(--success)' }}>No errors.</p>
                )}
              </div>
            ))}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>Decaf Compiler</h1>
        <button className="compile-btn" onClick={handleCompile} disabled={isCompiling}>
          {isCompiling ? 'Compiling...' : '▶ Compile Run'}
        </button>
      </header>
      
      <main className="main-content">
        <div className="editor-pane">
          <textarea
            className="code-textarea"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck="false"
          />
        </div>
        
        <div className="output-pane">
          <div className="tabs-header">
            <button className={`tab-btn ${activeTab === 'tokens' ? 'active' : ''}`} onClick={() => setActiveTab('tokens')}>Lexer</button>
            <button className={`tab-btn ${activeTab === 'grammar' ? 'active' : ''}`} onClick={() => setActiveTab('grammar')}>Grammar Sets</button>
            <button className={`tab-btn ${activeTab === 'rd' ? 'active' : ''}`} onClick={() => setActiveTab('rd')}>RD Parser</button>
            <button className={`tab-btn ${activeTab === 'll1' ? 'active' : ''}`} onClick={() => setActiveTab('ll1')}>LL(1) Parser</button>
            <button className={`tab-btn ${activeTab === 'lr' ? 'active' : ''}`} onClick={() => setActiveTab('lr')}>LR Parser</button>
            <button className={`tab-btn ${activeTab === 'symbol' ? 'active' : ''}`} onClick={() => setActiveTab('symbol')}>Symbol Table</button>
            <button className={`tab-btn ${activeTab === 'errors' ? 'active' : ''}`} onClick={() => setActiveTab('errors')}>Errors</button>
          </div>
          <div className="tab-content">
            {renderTabContent()}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
