# Natural Language Processing Agent

This agent translates natural language queries to specific commands that can be
routed to the appropriate agent in the AgentOS system.

## Features

- Translates natural language to specific commands for other agents
- Supports multiple LLM backends:
  - Google's Gemini models (requires API key)
  - Local Ollama models (requires Ollama running)
- Handles voice input with conversational responses
- Runtime configuration of model providers and specific models
- Fallback translation for when LLM services are unavailable

## Setup

### Ollama Setup (Default)

1. Install and run [Ollama](https://ollama.com/) on your local machine.
2. Pull the llama3.2:1b model:
   ```
   ollama pull llama3.2:1b
   ```
3. Make sure Ollama is running and accessible at http://localhost:11434.
4. Configure your `.env` file:
   ```
   NLP_MODEL_PROVIDER=ollama
   OLLAMA_API_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:1b
   ```

### Gemini Setup (Alternative)

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/)
2. Configure your `.env` file:
   ```
   NLP_MODEL_PROVIDER=gemini
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-lite
   ```
3. Install Google's generative AI package:
   ```
   pip install google-generativeai
   ```

## Usage

The Natural Language Processing agent works as a translation layer between natural language queries and specific agent commands:

1. User submits a query through voice or text
2. The agent sends the query to the configured LLM (Gemini or Ollama)
3. The LLM identifies the intent and translates it to a specific agent command
4. The translated command is routed to the appropriate agent
5. If no appropriate agent is found, it returns an "Unsupported query" message

## Example Queries

- "What's the weather like today?" → `datetime weather`
- "Create a task to buy groceries tomorrow" → `datetime add buy groceries tomorrow`
- "Open the document called budget report" → `filemanage open budget report`
- "Play music by Coldplay" → `spotiauto play Coldplay`
- "Tweet about the new AI features" → `twitter_bot tweet about the new AI features`
- "Generate a blog post" → `autoblog generate`

## API Endpoints

The agent provides several API endpoints for configuration:

- `/get_model_info`: Get current model configuration
- `/set_model_provider`: Change the model provider
- `/set_model`: Change the specific model for the current provider
- `/health_check`: Get the health status of the agent

## Configuration Options

The following configuration options are available in the `.env` file:

- `NLP_MODEL_PROVIDER`: Model provider ("gemini" or "ollama")
- `GEMINI_API_KEY`: API key for Google's Gemini models
- `GEMINI_MODEL`: Specific Gemini model to use
- `OLLAMA_API_URL`: URL for local Ollama API
- `OLLAMA_MODEL`: Specific Ollama model to use
- `NLP_DEBUG`: Enable debug logging (true/false) 