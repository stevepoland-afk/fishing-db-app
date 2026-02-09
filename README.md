# Fishing Organizations Database

A web-based application for managing fishing organizations with AI-powered research capabilities using Claude.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Claude](https://img.shields.io/badge/AI-Claude%20API-orange)

## Features

- **Browse & Search**: Filter organizations by state, type, or keyword
- **CRUD Operations**: Add, edit, and delete organization entries
- **AI Research**: Use Claude to research and discover new organizations via web search
- **Bulk Import**: Import existing data from Excel files
- **Export**: Download your database as JSON

## Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- An Anthropic API key ([Get one here](https://console.anthropic.com))

### 2. Installation

```bash
# Clone or download the project
cd fishing-db-app

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Your API Key

```bash
# Linux/Mac
export ANTHROPIC_API_KEY="your-api-key-here"

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=your-api-key-here

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

### 4. Run the Application

```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open your browser to: **http://localhost:8000**

## Importing Existing Data

If you have an existing Excel database:

```bash
python import_excel.py path/to/your/fishing_organizations_database.xlsx
```

The importer will:
- Read all sheets from your Excel file
- Map columns automatically (Name, Type, State, Website, etc.)
- Skip duplicates
- Assign organization types based on sheet names

## Project Structure

```
fishing-db-app/
├── app.py              # FastAPI backend with Claude integration
├── import_excel.py     # Excel import utility
├── requirements.txt    # Python dependencies
├── fishing_organizations.db  # SQLite database (created on first run)
└── static/
    └── index.html      # Web interface
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organizations` | List organizations (with filters) |
| GET | `/api/organizations/{id}` | Get single organization |
| POST | `/api/organizations` | Create organization |
| PUT | `/api/organizations/{id}` | Update organization |
| DELETE | `/api/organizations/{id}` | Delete organization |
| POST | `/api/research` | AI-powered research |
| POST | `/api/research/add` | Bulk add research results |
| GET | `/api/stats` | Database statistics |
| GET | `/api/export` | Export all data as JSON |

## Using AI Research

The AI Research panel lets you ask Claude to find fishing organizations:

**Example queries:**
- "Find bass fishing clubs in Texas"
- "Research fly fishing organizations in Colorado"
- "What conservation groups focus on redfish in the Gulf Coast?"
- "Find kayak fishing clubs in Florida"

Claude will search the web and return structured data you can review and add to your database.

### Research Tips

1. **Be specific**: "Bass fishing clubs in East Texas" works better than "fishing clubs"
2. **Use filters**: Select a state or organization type to narrow results
3. **Review results**: Claude may occasionally find outdated information
4. **Add selectively**: Use "Add" for individual results or "Add All" for bulk import

## Configuration

### Changing the AI Model

In `app.py`, modify the `ANTHROPIC_MODEL` constant:

```python
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"  # Default: cost-effective
# ANTHROPIC_MODEL = "claude-opus-4-5-20251101"  # More capable, higher cost
```

### Database Location

Change `DATABASE_PATH` in `app.py` to use a different SQLite file:

```python
DATABASE_PATH = "/path/to/your/database.db"
```

## Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud Platforms

The app works well on:
- **Railway** / **Render** / **Fly.io**: Set `ANTHROPIC_API_KEY` as environment variable
- **AWS/GCP/Azure**: Deploy as containerized service
- **Heroku**: Add `Procfile` with `web: uvicorn app:app --host 0.0.0.0 --port $PORT`

## Costs

- **Claude API**: Research queries use Claude Sonnet with web search. Typical cost is $0.01-0.05 per research query depending on complexity.
- **Storage**: SQLite is free and local. For production, consider PostgreSQL.

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
Make sure you've exported the environment variable in your current terminal session.

### "Research failed"
- Check your API key is valid
- Ensure you have API credits
- Try a simpler, more specific query

### Import not finding columns
The importer looks for common column names. Rename your Excel columns to: Name, Type, State, Website, Contact, Description, Notes.

## License

MIT License - Use freely for personal or commercial projects.

## Contributing

Pull requests welcome! Areas for improvement:
- PostgreSQL support
- User authentication
- Batch research operations
- More export formats (CSV, Excel)
