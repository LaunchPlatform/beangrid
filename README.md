# BeanGrid

> **🚧 Prototype Alert**: This is a prototype created by vibe coding. It's an experimental plaintext-based spreadsheet application that demonstrates the potential of plaintext-based spreadsheets in the AI era.

A plaintext spreadsheet application with real-time collaboration and AI assistance, built for the modern AI-powered workflow.

## Why Plaintext-Based Spreadsheets?

### 1. **Open Source & Vendor Independence**
Excel and other traditional spreadsheets are closed-source and vendor-locked. We need open-source solutions that give users full control over their data and workflows.

### 2. **AI-Native Design**
In the AI era, plaintext-based spreadsheets are infinitely more accessible for LLMs to read, understand, and update. No more complex binary formats or proprietary APIs - just clean, human-readable YAML that AI can easily parse and modify.

### 3. **Git Integration & Version Control**
Keeping your spreadsheets in Git is now seamless. Track every change, see the complete history of modifications, and collaborate with confidence. Never lose your work again.

### 4. **Open Source Collaboration**
Share and discover spreadsheets like never before. Common workbooks like tax calculations, financial models, and business templates should be available as open-source sheets that anyone can reference, modify, and contribute to.

## Features

- **📝 Plaintext YAML Format**: Store spreadsheets in human-readable YAML files
- **🧮 Excel-like Formulas**: Full formula support with cross-sheet references
- **🤖 AI Assistant**: Real-time chat with Grok for spreadsheet analysis and updates
- **🌐 Modern Web Interface**: React-based UI with real-time updates
- **📊 Multi-sheet Support**: Organize data across multiple sheets
- **🔗 Git Integration**: Version control for your spreadsheets
- **💬 Real-time Chat**: AI-powered assistance for complex calculations

## YAML-Based Spreadsheet Example

Here's what a spreadsheet looks like in YAML format:

```yaml
sheets:
  - name: Sales
    cells:
      - id: A1
        value: Product
      - id: B1
        value: Price
      - id: C1
        value: Quantity
      - id: D1
        value: Total
      - id: A2
        value: Widget A
      - id: B2
        value: "10.50"
      - id: C2
        value: "4"
      - id: D2
        formula: "=B2*C2"
      - id: A3
        value: Widget B
      - id: B3
        value: "15.75"
      - id: C3
        value: "6"
      - id: D3
        formula: "=B3*C3"
      - id: A4
        value: Total
      - id: B4
        value: ""
      - id: C4
        value: ""
      - id: D4
        formula: "=SUM(D2:D3)"
  - name: Summary
    cells:
      - id: A1
        value: Summary Report
      - id: A2
        value: Total Sales
      - id: B2
        formula: "=Sales!D4"
      - id: A3
        value: Average Price
      - id: B3
        formula: "=AVERAGE(Sales!B2:B3)"
```

### Formula Examples

```yaml
# Basic arithmetic
- id: C1
  formula: "=A1+B1"

# Cross-sheet references
- id: B2
  formula: "=Sales!D4"

# Functions
- id: D4
  formula: "=SUM(D2:D3)"

# Complex calculations
- id: E1
  formula: "=(A1+B1)*C1/100"
```

## Configuration

### LLM Settings

The application uses Grok for AI assistance. You can configure the LLM settings using environment variables:

```bash
# Set the LLM model (Grok)
export LLM_MODEL="xai/grok-3"

# Set the LLM API base URL (X.AI API)
export LLM_API_BASE="https://api.x.ai/v1"

# Set your X.AI API key
export LLM_API_KEY="your-xai-api-key-here"
```

Or you can set these in a `.env` file:

```env
LLM_MODEL=xai/grok-beta
LLM_API_BASE=https://api.x.ai/v1
LLM_API_KEY=your-xai-api-key-here
```

**Note**: You'll need to obtain an API key from [X.AI](https://x.ai) to use Grok.

## Installation

### Prerequisites

- Python 3.8+
- Git (for version control features)
- X.AI API key (for AI features)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/LaunchPlatform/beangrid.git
   cd beangrid
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up your API key**
   ```bash
   export LLM_API_KEY="your-xai-api-key-here"
   ```

4. **Run the server**
   ```bash
   uv run python run_server.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8000`

## Usage

### Creating a New Session
Click the "🆕 New Session" button in the top toolbar to create a fresh workspace with a new YAML file.

### Editing Cells
1. Click on any cell to select it
2. Use the formula bar at the bottom to edit values or formulas
3. Press Enter to save changes

### AI Assistance
1. Open the chat sidebar on the right
2. Ask questions about your data or request updates
3. The AI can suggest cell updates or entire workbook modifications

### Version Control
- All changes are automatically tracked in Git
- Use the "Diff" tab to see what's changed
- Commit changes with meaningful messages

## Development

This is a prototype built with:
- **Backend**: FastAPI + Python
- **Frontend**: React + JavaScript
- **AI**: Grok via X.AI API
- **Storage**: YAML files with Git version control

## Contributing

Since this is a prototype, we're exploring the concept of plaintext-based spreadsheets. Ideas and feedback are welcome!

## License

MIT License - feel free to use this as inspiration for your own plaintext spreadsheet projects.

---

*Exploring the future of spreadsheets in the AI era*
