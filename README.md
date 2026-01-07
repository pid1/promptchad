# Promptchad

Test prompts across multiple AI providers (OpenAI, Anthropic, Google) and compare results side-by-side.

![Promptchad](promptchad.png)

## Quick Start

```bash
# Enter the development environment
devenv shell

# Start the web UI
dev
```

Open http://localhost:5000 in your browser.

## Configuration

On first run, `config.toml` is created from the example. Add your API keys:

```toml
[providers.openai]
enabled = true
api_key = "sk-..."
model = "gpt-4"

[providers.anthropic]
enabled = true
api_key = "sk-ant-..."
model = "claude-3-5-sonnet-20241022"

[providers.google]
enabled = false
api_key = ""
model = "gemini-pro"
```

Each provider supports: `enabled`, `api_key`, `model`, `temperature`, `max_tokens`.

## Usage

### Web UI

```bash
dev
```

- **A/B Testing**: Enter two different prompts (A and B) to compare responses across providers
- **Shared Input**: Add a shared input (e.g., customer query) that gets appended to both prompts—useful for testing different system prompts against the same user input
- **Save/Load**: Save and load prompts by name using the dropdowns
- **Provider Config**: Enable/disable providers and configure models in the sidebar
- Click "Run A/B Test" to execute across all enabled providers

### Shared Input

The shared input field is useful for workflows like:
- Testing different customer support prompt templates against the same customer query
- Comparing system prompts with identical user messages
- A/B testing prompt variations with consistent test cases

The shared input is appended to each prompt with a `---` separator.

### CLI

```bash
# Basic usage
cli prompts/sample.txt

# JSON output
cli prompts/sample.txt --output json

# Custom config file
cli prompts/sample.txt --config /path/to/config.toml

# Inline prompt
cli prompts/sample.txt --prompt-text "Explain quantum computing"
```

## Logging

All A/B test runs are automatically logged to the `logs/` directory as JSON Lines files (one file per day).

### Log Format

Each log entry contains:
- **timestamp**: ISO 8601 UTC timestamp
- **inputs**: Original prompts (A, B) and shared input
- **config**: Provider configuration used (API keys are redacted)
- **outputs**: Full results from each provider

### Viewing Logs

```bash
# View today's logs
cat logs/$(date +%Y-%m-%d).jsonl

# Pretty-print a log file
cat logs/2024-01-15.jsonl | jq .

# View just the prompts and timestamps
cat logs/*.jsonl | jq '{timestamp, prompts: .inputs}'

# Filter by provider results
cat logs/*.jsonl | jq '.outputs.results_a.openai'
```

Logs are gitignored by default.

## Development

### Prerequisites

- [devenv](https://devenv.sh/getting-started/)

### Environment

The devenv provides:

- **Python 3.13** with uv for fast dependency management
- **Auto-sync** - dependencies install automatically on shell entry
- **Hot reloading** - Flask runs in debug mode; edit Python files and the server reloads

### Commands

| Command | Description |
|---------|-------------|
| `dev` | Start web UI server with hot reload |
| `cli <file>` | Run CLI with a prompt file |
| `test-prompt` | Quick test with `prompts/sample.txt` |

### Adding Providers

To add a new provider, edit `promptchad.py`:

1. Create an async function `call_<provider>(prompt, config) -> dict`
2. Add it to the `PROVIDERS` registry
3. Add default config in `config.toml.example`

### Project Structure

```
├── promptchad.py        # CLI tool and provider implementations
├── web_ui.py            # Flask server
├── templates/index.html # Web UI (vanilla HTML/JS)
├── prompts/             # Saved prompts
├── logs/                # Test run logs (gitignored)
├── config.toml          # Your configuration (gitignored)
├── config.toml.example  # Configuration template
├── pyproject.toml       # Python dependencies
├── devenv.nix           # Development environment
└── devenv.yaml          # Devenv inputs
```
