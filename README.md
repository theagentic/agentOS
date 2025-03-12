# AgentOS

A modular voice assistant platform with pluggable specialized agents and natural language understanding.

## Features

- 🎤 Voice and text interface with conversational AI
- 🧩 Modular agent architecture for extensibility
- 🧠 Natural language understanding to translate user requests
- 📅 Todoist integration for task management
- 📁 File management capabilities
- 🎵 Spotify integration for music control
- 🐦 Twitter automation for social media management
- ✍️ Blog post automation for content creation
- 🔌 Electron-based UI for desktop integration
### Disclaimer: 
Some of our agents and voice commands processing are yet to be implemented.

## Setup Instructions

### 1. Install Requirements

```bash
# Install main requirements
pip install -r requirements.txt

# For Electron UI (optional)
pip install -r requirements-electron.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your preferred settings
# These are system-level settings only
```

### 3. Configure Agents

Each agent has its own configuration and environment variables:

```bash
# For each agent you want to use:
cd agents/[agent_name]/
cp .env.example .env
# Edit the .env file with your API credentials
```

### 4. Run the Application

```bash
# Run the standard version
python main.py

# Or run with Electron UI (if configured)
python electron_main.py
```

## Agent Configuration

### Natural Language Agent
- **Functionality**: Translates natural language into commands for other agents
- **Requirements**: Either Ollama locally installed or Gemini API key
- Configuration: `agents/natural_language/.env`
- See `NATURAL_LANGUAGE_SETUP.md` for detailed setup instructions

### Todoist Agent
- **Functionality**: Task management, reminders, and weather information
- **Requirements**: Todoist API token
- Configuration: `agents/datetime/.env`

### Spotify Agent
- **Functionality**: Control Spotify playback, search and play tracks/playlists
- **Requirements**: Spotify API credentials (Client ID and Secret)
- Configuration: `agents/spotiauto/.env`

### Twitter Bot
- **Functionality**: Post tweets, create threads, monitor timelines
- **Requirements**: Twitter API credentials
- Configuration: `agents/twitter_bot/.env`

### Autoblog Agent
- **Functionality**: Generate blog posts automatically from repositories
- **Requirements**: None
- Configuration: `agents/autoblog/.env`

### File Management
- **Functionality**: Navigate and manipulate the file system
- **Requirements**: None
- Configuration: Configure allowed directories in the main `.env` file

## Directory Structure

```
AgentOS/
├── agents/                # Agent modules
│   ├── autoblog/          # Blog automation agent
│   ├── datetime/          # Date/time and Todoist agent
│   ├── filemanage/        # File management agent
│   ├── natural_language/  # Natural language processing agent
│   ├── spotiauto/         # Spotify automation agent
│   ├── twitter_bot/       # Twitter bot agent
│   └── agent_template/    # Template for creating new agents
├── api/                   # API endpoints for external services
├── core/                  # Core system components
│   ├── agent_base.py      # Base agent class
│   ├── agent_router.py    # Routes commands to agents
│   ├── tts_engine.py      # Text-to-speech engine
│   └── voice_processor.py # Voice input processor
├── electron/              # Electron app integration
├── scripts/               # Utility scripts
├── ui/                    # User interface components
├── utils/                 # Shared utility functions
├── .env                   # Environment variables
├── config.py              # Configuration system
├── main.py                # Application entry point
├── requirements.txt       # Project dependencies
└── setup.py               # Installation script
```

## Development

### Creating a New Agent

You can use the agent template to create a new agent:

```bash
# Copy the template
cp -r agents/agent_template agents/your_agent_name

# Edit the files to implement your agent's functionality
```

### Running Tests

```bash
# Run tests for a specific agent
python -m pytest test_agent.py -v

# Run natural language agent tests
python test_nlp_agent.py
```

## Plans
In the future, I hope to create an agentic framework so anyone can build agents for my AgentOS and use them freely or, if they want, even commit to them. Please feel free to reach out if you have ideas to share about this project of mine, I'd love to discuss and get constructive criticism and make this better with time.

## License

MIT
