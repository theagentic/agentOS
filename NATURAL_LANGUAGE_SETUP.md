# Natural Language Processing Setup for AgentOS

This guide explains how to set up and use the natural language processing feature in AgentOS, which allows you to use conversational language instead of specific commands.

## Prerequisites

1. **Ollama**: The natural language processing feature uses Ollama with the llama3.2:1b model to translate natural language to specific agent commands.

## Installation Steps

### 1. Install Ollama

Download and install Ollama from the official website:
- Windows/macOS/Linux: [https://ollama.com/download](https://ollama.com/download)

### 2. Pull the Required Model

After installing Ollama, open a terminal or command prompt and run:

```
ollama pull llama3.2:1b
```

This will download the 1B parameter version of Llama 3.2, which is small enough to run on most computers but powerful enough for command translation.

### 3. Start Ollama

Make sure Ollama is running before using the natural language features:

- On Windows: Ollama should start automatically after installation and run in the background
- On macOS/Linux: Run `ollama serve` if it's not already running

Verify Ollama is running by opening a browser and navigating to: http://localhost:11434

## Using Natural Language

Once Ollama is set up and running, you can use natural language queries with AgentOS instead of specific commands. For example:

Instead of typing: `datetime weather`
You can say: "What's the weather like today?"

Instead of typing: `twitter_bot create post about AI`
You can say: "Create a Twitter post about artificial intelligence"

### Example Queries

Here are some examples of natural language queries and how they get translated:

| Natural Language Query | Translated Command |
|------------------------|-------------------|
| "What's the weather like today?" | `datetime weather` |
| "Create a post for Twitter about AI" | `twitter_bot create post about AI` |
| "Open the document called budget report" | `filemanage open budget report` |
| "Play my favorite playlist" | `spotiauto play favorite playlist` |
| "What time is it?" | `datetime time` |

## Troubleshooting

If natural language processing isn't working:

1. **Check if Ollama is running**:
   - Open a browser and go to http://localhost:11434
   - If you can't access this URL, Ollama is not running

2. **Verify the model is installed**:
   - Run `ollama list` to see installed models
   - Make sure `llama3.2:1b` is in the list

3. **Check the logs**:
   - Look for any errors related to the natural language agent in the AgentOS logs

4. **Test the NLP agent directly**:
   - Run `python test_nlp_agent.py` to test the natural language agent

## Configuration

You can configure the natural language processing agent by editing the `.env` file in the `agents/natural_language` directory:

- `OLLAMA_API_URL`: The URL of the Ollama API (default: http://localhost:11434)
- `OLLAMA_MODEL`: The model to use (default: llama3.2:1b)
- `NLP_DEBUG`: Set to `true` to enable debug logging

## Disabling Natural Language Processing

If you prefer to use only direct commands, you can disable natural language processing by setting:

```python
router.use_natural_language = False
```

in your code, or by modifying the AgentRouter class to disable it by default. 