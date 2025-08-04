<h1 align="center">✨ Contributors Guide ✨</h1>
<h3 align="center">Welcome to AgentOS! 🤖<br> We appreciate your interest in contributing to our modular AI assistant platform.😊 <br>This guide will help you get started with the project and make your first contribution.</h3>

![Line](https://user-images.githubusercontent.com/85225156/171937799-8fc9e255-9889-4642-9c92-6df85fb86e82.gif)

## What you can Contribute?

**🐞 Bug Fixing:**
Contributors can help by reviewing and confirming reported issues. This includes verifying bugs, providing additional details, and prioritizing tasks for the development team. Common areas include:
- Agent communication issues
- Voice processing bugs
- Natural language understanding errors
- UI/UX problems in the Electron app

**✨ Enhancements:**
Contributors can enhance the project by implementing new features or improvements. This involves understanding requirements, designing solutions, and extending the functionality of AgentOS:
- Improving existing agent capabilities
- Enhancing the natural language processing
- Adding new voice commands
- Improving the Electron UI
- Performance optimizations

**🤖 New Agent Development:**
Create entirely new agents for different use cases:
- Weather agents
- News aggregation agents
- Smart home control agents
- Productivity agents
- Entertainment agents
- And any creative agent ideas you have!

**📚 Documentation:**
Help improve our documentation:
- API documentation
- Agent development guides
- Setup and configuration tutorials
- Code comments and inline documentation
- README improvements

**🧪 Testing:**
Write tests to ensure code quality and reliability:
- Unit tests for individual agents
- Integration tests for agent communication
- End-to-end tests for the complete system
- Voice processing tests

![Line](https://user-images.githubusercontent.com/85225156/171937799-8fc9e255-9889-4642-9c92-6df85fb86e82.gif)

## Development Environment Setup

### Prerequisites
- Python 3.8 or higher
- Node.js (for Electron UI)
- Git
- Code editor (VS Code recommended)

### Initial Setup
1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/<your-username>/agentOS.git
   cd agentOS
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   # For Electron UI (optional)
   pip install -r requirements-electron.txt
   ```

3. **Install Node Dependencies (for Electron UI)**
   ```bash
   cd electron
   npm install
   cd ..
   ```

4. **Set Up Environment Variables**
   ```bash
   # Copy the main environment file
   cp .env.example .env
   
   # For each agent you want to work with:
   cd agents/[agent_name]/
   cp .env.example .env
   # Edit with your API credentials
   ```

5. **Test the Setup**
   ```bash
   # Test basic functionality
   python test_agent.py
   
   # Test natural language agent
   python test_nlp_agent.py
   ```

![Line](https://user-images.githubusercontent.com/85225156/171937799-8fc9e255-9889-4642-9c92-6df85fb86e82.gif)

## How to Contribute?

### Step 1: Preparation
- ⭐ Drop a Star in this repo
- 🍴 Fork the repository
- 📋 Take a look at the existing [Issues](https://github.com/theagentic/agentOS/issues)
- 💡 For new features, first raise an issue to discuss the idea

### Step 2: Development Process
1. **Create an Issue First**
   - Describe the bug, feature, or improvement you want to work on
   - Wait for issue assignment before starting work
   - **REMINDER: Don't raise more than 2 `Issues` at a time**

2. **Work on Assigned Issues Only**
   - **IMPORTANT: Don't make any `Pull Request` until you get assigned to an `Issue`**
   - Create a branch for your work: `git checkout -b feature/your-feature-name`

3. **Development Guidelines**
   - Follow the existing code style and structure
   - Add proper documentation and comments
   - Test your changes thoroughly
   - Follow the agent template for new agents

4. **Commit and Push**
   - Make meaningful commit messages
   - Push your branch to your forked repository

### Step 3: Pull Request
- Create a [**Pull Request**](https://github.com/theagentic/agentOS/pulls) from your branch
- Add detailed description of your changes
- Include screenshots or demos for UI changes
- Add testing instructions
- Reference the issue number in your PR description

### Step 4: Review Process
- Your PR will be reviewed by maintainers
- Address any feedback or requested changes
- Once approved, your contribution will be merged!

![Line](https://user-images.githubusercontent.com/85225156/171937799-8fc9e255-9889-4642-9c92-6df85fb86e82.gif)

## Agent Development Guidelines

### Creating a New Agent

1. **Use the Template**
   ```bash
   cp -r agents/agent_template agents/your_agent_name
   ```

2. **Agent Structure**
   ```
   agents/your_agent_name/
   ├── __init__.py
   ├── agent.py          # Main agent class
   ├── config.py         # Agent configuration
   ├── .env.example      # Environment variables template
   ├── requirements.txt  # Agent-specific dependencies
   └── README.md         # Agent documentation
   ```

3. **Agent Requirements**
   - Inherit from `AgentBase` class
   - Implement required methods: `handle_request()`, `get_capabilities()`
   - Add proper error handling and logging
   - Include comprehensive docstrings
   - Add configuration options

4. **Testing Your Agent**
   - Write unit tests for your agent
   - Test integration with the main system
   - Test voice commands if applicable
   - Verify configuration handling

### Code Quality Standards
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add type hints where appropriate
- Include proper exception handling
- Write comprehensive docstrings
- Keep functions focused and single-purpose

![Line](https://user-images.githubusercontent.com/85225156/171937799-8fc9e255-9889-4642-9c92-6df85fb86e82.gif)

## Project Structure Overview

```
AgentOS/
├── agents/                # All agent modules
│   ├── agent_template/    # Template for new agents
│   ├── natural_language/  # NLP processing agent
│   ├── datetime/          # Task management agent
│   ├── filemanage/        # File operations agent
│   ├── spotiauto/         # Spotify control agent
│   ├── twitter_bot/       # Social media agent
│   └── autoblog/          # Content creation agent
├── core/                  # Core system components
│   ├── agent_base.py      # Base agent class
│   ├── agent_router.py    # Command routing
│   ├── voice_processor.py # Voice input handling
│   └── tts_engine.py      # Text-to-speech
├── electron/              # Desktop UI application
├── api/                   # REST API endpoints
├── utils/                 # Shared utilities
└── scripts/               # Helper scripts
```

![Line](https://user-images.githubusercontent.com/85225156/171937799-8fc9e255-9889-4642-9c92-6df85fb86e82.gif)

<h2 align="center">Need more help? 🤔</h1>
<p align="center">
  You can refer to the following articles on basics of Git and Github and also contact the Project Maintainers, in case you are stuck: <br>
  <a href="https://help.github.com/en/desktop/contributing-to-projects/creating-an-issue-or-pull-request">How to create an Issue</a> <br>
  <a href="https://help.github.com/en/github/getting-started-with-github/fork-a-repo">Forking a Repo</a> <br>
  <a href="https://docs.github.com/en/get-started/quickstart/fork-a-repo#cloning-your-forked-repository">Cloning a Repo</a> <br>
  <a href="https://opensource.com/article/19/7/create-pull-request-github">How to create a Pull Request</a> <br>
  <a href="https://docs.github.com/get-started">Getting started with Git and GitHub</a> <br>
  <a href="https://code.visualstudio.com/docs/python/python-tutorial">Python Development in VS Code</a> <br>
  <a href="https://www.electronjs.org/docs/latest/">Electron Documentation</a> <br>
</p>

## Community Guidelines

- 🤝 Be respectful and inclusive to all contributors
- 💬 Use clear and constructive communication
- 🚫 No spam or low-quality contributions
- 📝 Follow the issue and PR templates
- ⏱️ Be patient with the review process
- 🎯 Focus on quality over quantity

<h2 align="center">Special Thanks 🙏</h1>
<p align="center">We appreciate every contribution, no matter how small. Whether it's fixing a typo, reporting a bug, or adding a new feature, every contribution helps make AgentOS better!</p>

<h2 align="center">Tip from us 😇</h1>
<p align="center">It always takes time to understand and learn. So, don't worry at all. We know <b>you have got this</b>! 💪</p>
<h3 align="center">Show some &nbsp;❤️&nbsp; by &nbsp;🌟&nbsp; this repository!</h3>
