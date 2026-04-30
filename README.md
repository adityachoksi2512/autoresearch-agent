# AutoResearch Agent

An autonomous multi-step research agent powered by Claude and DuckDuckGo. Give it any question - it plans, searches the live web, reads sources, and writes a full cited report with clickable URLs.

## Demo

[Watch the demo video](https://drive.google.com/file/d/1x8JQYDNOs4RMiKj4yk5ax6OJd0cmjARo/view?usp=sharing)

## How it works

Your question is broken into N sub-questions based on your depth setting. For each sub-question, the agent runs a live DuckDuckGo search, Claude summarizes the results and extracts URLs, and finally everything is synthesized into a cited markdown report.

## Features

- Live web search via DuckDuckGo - free, no extra API key required
- Agentic planning - Claude breaks your question into focused sub-questions
- Depth slider 1-10 - control how many angles are researched
- Markdown and PDF export with clickable citation links
- Streamlit dark UI
- CLI support

## Setup

### 1. Clone the repo
```
git clone https://github.com/adityachoksi2512/autoresearch-agent
cd autoresearch-agent
```

### 2. Create a virtual environment
```
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Set your Anthropic API key

Get your key at https://console.anthropic.com

Windows:
```
set ANTHROPIC_API_KEY=your_api_key_here
```

Mac/Linux:
```
export ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### Streamlit UI
```
streamlit run app.py
```

### Command Line
```
python agent.py "Your research question here" --depth 3
```

## Depth Flag

| Depth | Sub-questions | Best for |
|-------|--------------|----------|
| 1-2 | 1-2 | Quick answers |
| 3-5 | 3-5 | Balanced research |
| 6-10 | 6-10 | Thorough deep dives |

## Tech Stack

| Layer | Tool |
|-------|------|
| LLM | Claude Haiku via Anthropic API |
| Web Search | DuckDuckGo (free) |
| UI | Streamlit |
| PDF Export | ReportLab |
| CLI | Typer + Rich |

## Project Structure

```
autoresearch-agent/
├── app.py
├── agent.py
├── utils.py
├── pdf_export.py
├── requirements.txt
├── .env.example
├── .gitignore
└── .streamlit/
    └── config.toml
```

## Notes

- Never commit your API key - always use set or export to set it in your session
- Keep depth at 3-5 to avoid hitting rate limits
- Reports are saved locally to the outputs/ folder
