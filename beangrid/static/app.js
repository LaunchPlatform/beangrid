// React app for BeanGrid workbook viewer
const { useState, useEffect } = React;

function WorkbookViewer() {
    const [workbook, setWorkbook] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeSheet, setActiveSheet] = useState(0);

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

    const renderCell = (cell) => {
        const hasFormula = cell.formula && cell.formula.trim() !== '';
        const displayValue = hasFormula ? cell.value : (cell.value || '');
        
        return (
            <td 
                key={cell.id} 
                className={`cell ${hasFormula ? 'has-formula' : ''}`}
                title={hasFormula ? `Formula: ${cell.formula}` : ''}
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
                                            ? renderCell(grid[row][col])
                                            : <td key={col}></td>
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
                {workbook.processed && (
                    <div className="status processed">
                        ✓ Formulas processed
                    </div>
                )}
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