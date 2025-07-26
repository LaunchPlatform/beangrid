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

        try {
            const response = await fetch('/api/v1/workbook/cell', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sheet_name: selectedCell.sheetName,
                    cell_id: selectedCell.id,
                    value: formulaBar.showFormula ? null : formulaBar.value,
                    formula: formulaBar.showFormula ? formulaBar.formula : null
                })
            });

            if (response.ok) {
                // Refresh the workbook data
                await fetchWorkbook();
                // Keep the cell selected but clear the formula bar
                setFormulaBar({ value: '', formula: '', showFormula: false });
            } else {
                const errorData = await response.json();
                alert('Error updating cell: ' + errorData.detail);
            }
        } catch (err) {
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

// Render the React app
ReactDOM.render(<WorkbookViewer />, document.getElementById('app')); 