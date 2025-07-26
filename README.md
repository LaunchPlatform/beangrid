[![CircleCI](https://circleci.com/gh/LaunchPlatform/beangrid.svg?style=svg)](https://circleci.com/gh/LaunchPlatform/beangrid)
# BeanGrid

A plaintext spreadsheet application with real-time collaboration and AI assistance.

## Features

- **Plaintext YAML Format**: Store spreadsheets in human-readable YAML files
- **Formula Support**: Excel-like formulas with cross-sheet references
- **Real-time Chat**: AI assistant for spreadsheet analysis and updates
- **Web Interface**: Modern React-based UI with real-time updates
- **Git Integration**: Version control for your spreadsheets

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
