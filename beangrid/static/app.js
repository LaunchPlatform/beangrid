// React app for BeanGrid workbook viewer
const { useState, useEffect } = React;

function WorkbookViewer() {
    const [workbook, setWorkbook] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeSheet, setActiveSheet] = useState(0);
    const [selectedCell, setSelectedCell] = useState(null);
    const [formulaBar, setFormulaBar] = useState({ value: '', formula: '', showFormula: false });

    useEffect(() => {
        fetchWorkbook();
    }, []);

    const fetchWorkbook = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/v1/workbook');
            const data = await response.json();
            
            if (data.error) {
                setError(data.error);
            } else {
                setWorkbook(data);
            }
        } catch (err) {
            setError('Failed to load workbook: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCellClick = (cell, sheetName) => {
        setSelectedCell({ ...cell, sheetName });
        setFormulaBar({
            value: cell.value || '',
            formula: cell.formula || '',
            showFormula: !!(cell.formula && cell.formula.trim())
        });
    };

    const handleFormulaBarChange = (field, value) => {
        setFormulaBar({
            ...formulaBar,
            [field]: value
        });
    };

    const handleCellUpdate = async () => {
        if (!selectedCell) return;

        const requestData = {
            sheet_name: selectedCell.sheetName,
            cell_id: selectedCell.id,
            value: formulaBar.showFormula ? null : formulaBar.value,
            formula: formulaBar.showFormula ? formulaBar.formula : null
        };

        console.log('Sending request:', requestData);

        try {
            const response = await fetch('/api/v1/workbook/cell', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                // Refresh the workbook data
                await fetchWorkbook();
                // Keep the cell selected but clear the formula bar
                setFormulaBar({ value: '', formula: '', showFormula: false });
            } else {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                alert('Error updating cell: ' + errorData.detail);
            }
        } catch (err) {
            console.error('Request error:', err);
            alert('Error updating cell: ' + err.message);
        }
    };

    const handleFormulaBarKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleCellUpdate();
        }
    };

    const renderCell = (cell, sheetName) => {
        const hasFormula = cell.formula && cell.formula.trim() !== '';
        const displayValue = hasFormula ? cell.value : (cell.value || '');
        const isSelected = selectedCell && selectedCell.id === cell.id && selectedCell.sheetName === sheetName;
        
        return (
            <td 
                key={cell.id} 
                className={`cell ${hasFormula ? 'has-formula' : ''} clickable ${isSelected ? 'selected' : ''}`}
                title={hasFormula ? `Formula: ${cell.formula}` : 'Click to select'}
                onClick={() => handleCellClick(cell, sheetName)}
            >
                {displayValue}
            </td>
        );
    };

    const renderSheet = (sheet, index) => {
        // Create a grid from cells
        const grid = {};
        const maxRow = 0;
        const maxCol = 0;
        
        sheet.cells.forEach(cell => {
            const match = cell.id.match(/^([A-Z]+)(\d+)$/);
            if (match) {
                const col = match[1];
                const row = parseInt(match[2]);
                if (!grid[row]) grid[row] = {};
                grid[row][col] = cell;
            }
        });

        const rows = Object.keys(grid).sort((a, b) => parseInt(a) - parseInt(b));
        const cols = new Set();
        rows.forEach(row => {
            Object.keys(grid[row]).forEach(col => cols.add(col));
        });
        const sortedCols = Array.from(cols).sort();

        return (
            <div key={sheet.name} className={`sheet ${index === activeSheet ? 'active' : 'hidden'}`}>
                <h2>{sheet.name}</h2>
                
                {/* Formula Bar */}
                <div className="formula-bar">
                    <div className="formula-bar-cell-info">
                        {selectedCell && selectedCell.sheetName === sheet.name ? (
                            <span className="cell-reference">{selectedCell.id}</span>
                        ) : (
                            <span className="cell-reference">No cell selected</span>
                        )}
                    </div>
                    <div className="formula-bar-input-container">
                        <div className="formula-bar-tabs">
                            <button 
                                className={`tab ${!formulaBar.showFormula ? 'active' : ''}`}
                                onClick={() => setFormulaBar({...formulaBar, showFormula: false})}
                            >
                                Value
                            </button>
                            <button 
                                className={`tab ${formulaBar.showFormula ? 'active' : ''}`}
                                onClick={() => setFormulaBar({...formulaBar, showFormula: true})}
                            >
                                Formula
                            </button>
                        </div>
                        <input
                            type="text"
                            className="formula-bar-input"
                            value={formulaBar.showFormula ? formulaBar.formula : formulaBar.value}
                            onChange={(e) => handleFormulaBarChange(
                                formulaBar.showFormula ? 'formula' : 'value', 
                                e.target.value
                            )}
                            onKeyDown={handleFormulaBarKeyDown}
                            placeholder={formulaBar.showFormula ? "Enter formula..." : "Enter value..."}
                        />
                        <div className="formula-bar-actions">
                            <button onClick={handleCellUpdate} className="btn-save" disabled={!selectedCell}>
                                ✓
                            </button>
                        </div>
                    </div>
                </div>
                
                <div className="table-container">
                    <table className="workbook-table">
                        <thead>
                            <tr>
                                <th></th>
                                {sortedCols.map(col => (
                                    <th key={col} className="column-header">{col}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map(row => (
                                <tr key={row}>
                                    <td className="row-header">{row}</td>
                                    {sortedCols.map(col => (
                                        grid[row] && grid[row][col] 
                                            ? renderCell(grid[row][col], sheet.name)
                                            : <td key={col} className="cell clickable" onClick={() => handleCellClick({id: col+row, value: '', formula: ''}, sheet.name)}></td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Loading workbook...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error">
                <h3>Error Loading Workbook</h3>
                <p>{error}</p>
                <button onClick={fetchWorkbook} className="btn">Retry</button>
            </div>
        );
    }

    if (!workbook || !workbook.sheets || workbook.sheets.length === 0) {
        return (
            <div className="no-data">
                <h3>No Workbook Data</h3>
                <p>No workbook data available. Make sure WORKBOOK_FILE environment variable is set.</p>
            </div>
        );
    }

    return (
        <div className="workbook-viewer">
            <div className="header">
                <h1>BeanGrid Workbook Viewer</h1>
                <div className="header-actions">
                    {workbook.processed && (
                        <div className="status processed">
                            ✓ Formulas processed
                        </div>
                    )}
                    <button onClick={fetchWorkbook} className="btn-refresh">
                        🔄 Refresh
                    </button>
                </div>
            </div>
            
            {workbook.sheets.length > 1 && (
                <div className="sheet-tabs">
                    {workbook.sheets.map((sheet, index) => (
                        <button
                            key={sheet.name}
                            className={`tab ${index === activeSheet ? 'active' : ''}`}
                            onClick={() => setActiveSheet(index)}
                        >
                            {sheet.name}
                        </button>
                    ))}
                </div>
            )}
            
            <div className="sheets-container">
                {workbook.sheets.map((sheet, index) => renderSheet(sheet, index))}
            </div>
        </div>
    );
}

function ChatSidebar({ onAction }) {
    const [messages, setMessages] = React.useState([
        { role: 'assistant', content: 'Hi! I am your spreadsheet assistant. Ask me about your data or request updates.' }
    ]);
    const [input, setInput] = React.useState('');
    const [loading, setLoading] = React.useState(false);

    const sendMessage = async () => {
        if (!input.trim()) return;
        const newMessages = [...messages, { role: 'user', content: input }];
        setMessages(newMessages);
        setInput('');
        setLoading(true);
        try {
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: input,
                    history: newMessages.map(m => ({ role: m.role, content: m.content }))
                })
            });
            const data = await response.json();
            setMessages([...newMessages, { role: 'assistant', content: data.response }]);
            setLoading(false);
            if (data.action && data.action_args) {
                if (data.action === 'update_cell') {
                    // Ask user to confirm the action
                    if (window.confirm(data.response + '\nApply this change?')) {
                        onAction(data.action, data.action_args);
                    }
                } else if (data.action === 'update_workbook') {
                    // Ask user to confirm the workbook update
                    if (window.confirm(data.response + '\nApply this workbook update?')) {
                        onAction(data.action, data.action_args);
                    }
                }
            }
        } catch (err) {
            setMessages([...newMessages, { role: 'assistant', content: 'Error: ' + err.message }]);
            setLoading(false);
        }
    };

    return (
        <div className="chat-sidebar">
            <div className="chat-header">🤖 Spreadsheet Chat</div>
            <div className="chat-messages">
                {messages.map((msg, i) => (
                    <div key={i} className={`chat-msg ${msg.role}`}>{msg.content}</div>
                ))}
                {loading && <div className="chat-msg assistant">...</div>}
            </div>
            <div className="chat-input-bar">
                <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
                    placeholder="Ask about your spreadsheet..."
                />
                <button onClick={sendMessage} disabled={loading || !input.trim()}>Send</button>
            </div>
        </div>
    );
}

function YamlEditor({ onClose, onSaved }) {
    const [yaml, setYaml] = React.useState('');
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    const [saving, setSaving] = React.useState(false);
    React.useEffect(() => {
        fetch('/api/v1/workbook/yaml')
            .then(r => r.text())
            .then(setYaml)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, []);
    const handleSave = async () => {
        setSaving(true);
        setError(null);
        try {
            const resp = await fetch('/api/v1/workbook/yaml', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml_content: yaml })
            });
            if (!resp.ok) {
                const data = await resp.json();
                setError(data.detail || 'Failed to save YAML');
            } else {
                onSaved && onSaved();
            }
        } catch (e) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };
    return (
        <div className="yaml-editor">
            <div className="yaml-editor-header">
                <span>Raw YAML Editor</span>
                <button onClick={onClose} className="btn-cancel">Close</button>
            </div>
            {loading ? <div>Loading...</div> : (
                <>
                    <textarea
                        className="yaml-textarea"
                        value={yaml}
                        onChange={e => setYaml(e.target.value)}
                        rows={24}
                        spellCheck={false}
                    />
                    {error && <div className="yaml-error">{error}</div>}
                    <div className="yaml-editor-actions">
                        <button onClick={handleSave} className="btn-save" disabled={saving}>Save</button>
                    </div>
                </>
            )}
        </div>
    );
}

function DiffView() {
    const [diff, setDiff] = React.useState('');
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    const [commitMsg, setCommitMsg] = React.useState('');
    const [committing, setCommitting] = React.useState(false);
    const [commitResult, setCommitResult] = React.useState(null);
    const fetchDiff = React.useCallback(() => {
        setLoading(true);
        setError(null);
        fetch('/api/v1/workbook/yaml-diff')
            .then(r => r.text())
            .then(setDiff)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, []);
    React.useEffect(() => { fetchDiff(); }, [fetchDiff]);
    const handleCommit = async () => {
        setCommitting(true);
        setCommitResult(null);
        try {
            const resp = await fetch('/api/v1/workbook/commit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: commitMsg })
            });
            const data = await resp.json();
            if (!resp.ok) {
                setCommitResult(data.detail || 'Commit failed');
            } else {
                setCommitResult('Committed!');
                setCommitMsg('');
                fetchDiff();
            }
        } catch (e) {
            setCommitResult(e.message);
        } finally {
            setCommitting(false);
        }
    };
    return (
        <div className="diff-view">
            <div className="diff-header">YAML Git Diff</div>
            {loading ? <div>Loading...</div> : (
                <pre className="diff-block">
                  {diff
                    ? diff.split('\n').map((line, i) => {
                        let cls = '';
                        if (line.startsWith('+') && !line.startsWith('+++')) cls = 'diff-add';
                        else if (line.startsWith('-') && !line.startsWith('---')) cls = 'diff-del';
                        else if (line.startsWith('@@')) cls = 'diff-hunk';
                        return (
                          <span key={i} className={cls}>{line + '\n'}</span>
                        );
                      })
                    : 'No changes'}
                </pre>
            )}
            {error && <div className="diff-error">{error}</div>}
            <div className="commit-ui">
                <input
                    type="text"
                    value={commitMsg}
                    onChange={e => setCommitMsg(e.target.value)}
                    placeholder="Commit message"
                    disabled={committing}
                />
                <button onClick={handleCommit} disabled={committing || !commitMsg.trim()}>Commit Changes</button>
                {commitResult && <span className="commit-result">{commitResult}</span>}
            </div>
        </div>
    );
}

function App() {
    const [tab, setTab] = React.useState('spreadsheet');
    const workbookRef = React.useRef();
    const handleLLMAction = async (action, args) => {
        if (action === 'update_cell') {
            await fetch('/api/v1/workbook/cell', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(args)
            });
            if (workbookRef.current && workbookRef.current.fetchWorkbook) {
                workbookRef.current.fetchWorkbook();
            } else {
                window.location.reload();
            }
        } else if (action === 'update_workbook') {
            await fetch('/api/v1/workbook/update-from-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    yaml_content: args.yaml_content,
                    commit_message: args.commit_message
                })
            });
            if (workbookRef.current && workbookRef.current.fetchWorkbook) {
                workbookRef.current.fetchWorkbook();
            } else {
                window.location.reload();
            }
        }
    };
    const handleYamlSaved = () => {
        window.location.reload();
    };
    return (
        <div className="main-layout">
            <div className="main-content">
                <div className="tab-bar">
                    <button className={tab === 'spreadsheet' ? 'active' : ''} onClick={() => setTab('spreadsheet')}>Spreadsheet</button>
                    <button className={tab === 'yaml' ? 'active' : ''} onClick={() => setTab('yaml')}>YAML</button>
                    <button className={tab === 'diff' ? 'active' : ''} onClick={() => setTab('diff')}>Diff</button>
                </div>
                {tab === 'spreadsheet' && <WorkbookViewer ref={workbookRef} />}
                {tab === 'yaml' && <YamlEditor onClose={() => setTab('spreadsheet')} onSaved={handleYamlSaved} />}
                {tab === 'diff' && <DiffView />}
            </div>
            <ChatSidebar onAction={handleLLMAction} />
        </div>
    );
}

// Render the App
ReactDOM.render(<App />, document.getElementById('app')); 