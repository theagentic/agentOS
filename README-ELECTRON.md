# AgentOS - Electron + Python Edition

A voice-activated assistant platform with modular agents, featuring an Electron frontend and Python backend.

## Features

- 🎤 Voice and text interface
- 🧩 Modular agent architecture
- 📅 Todoist integration
- 📁 File management
- 🎵 Spotify integration
- 🐦 Twitter automation
- ✍️ Blog post automation
- 🖥️ Modern Electron UI

## Installation

### Prerequisites

- [Node.js](https://nodejs.org/) (v16+)
- [Python](https://www.python.org/) (3.8+)
- npm (comes with Node.js)

### Automatic Installation

Run the installation script:

```sh
# Windows
install.bat

# macOS/Linux
./install.sh
```

### Manual Installation

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   pip install -r requirements-electron.txt
   ```

2. Install Node.js dependencies:
   ```
   npm install
   ```

## Configuration

1. Copy environment examples for the main application:
   ```
   cp .env.example .env
   ```

2. Set up agent-specific configurations:
   ```
   # For each agent you want to use
   cp agents/[agent_name]/.env.example agents/[agent_name]/.env
   ```

3. Edit each `.env` file with your API credentials and preferences.

## Running the Application

```sh
# Windows
start.bat

# macOS/Linux
./start.sh

# Or with npm
npm start
```

## Development

Run in development mode to enable dev tools:

```sh
npm run dev
```

## Building a Distribution

```sh
npm run build
```

Distribution files will be in the `dist` directory.

## Architecture

AgentOS uses a hybrid architecture:

1. **Electron Frontend**: Modern web-based UI built with HTML/CSS/JS
2. **Python Backend**: Handles agents, NLP, and API integrations
3. **Flask Bridge**: Connects the two layers via HTTP and WebSockets

## Troubleshooting

- **Missing dependencies**: Run `pip install -r requirements.txt -r requirements-electron.txt`
- **Port conflicts**: Make sure port 5000 is available for the Python bridge
- **Voice recognition issues**: Check your microphone settings and PyAudio installation
