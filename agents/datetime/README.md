# DateTime Agent for AgentOS

This agent provides date, time, weather information, and Todoist task management capabilities for the AgentOS platform.

## Features

- Get current date and time information
- Get weather forecasts for any location
- Create and manage Todoist tasks
- Support for natural language dates and recurring tasks
- Seamless integration with the AgentOS voice assistant

## Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Add your Todoist API token to the `.env` file:
   ```bash
   TODOIST_API_TOKEN=your_token_here
   WEATHER_API_KEY=your_openweather_api_key_here
   ```
   - Get your Todoist API token from Todoist settings → Integrations → API token
   - Weather API is optional, uses OpenWeatherMap if provided

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage in AgentOS

### Date and Time Commands

```
datetime time
```
Returns the current time.

```
datetime date
```
Returns the current date.

### Weather Commands

```
datetime weather
```
Gets the current weather for your default location.

```
datetime weather New York
```
Gets the weather for a specific location.

### Task Management Commands

1. **Add a new task**:
   ```
   datetime add Buy groceries tomorrow at 5pm
   ```
   This creates a new Todoist task with the specified due date.

2. **Add a recurring task**:
   ```
   datetime add Team meeting every monday at 10am
   ```
   Creates a recurring Todoist task.

3. **List tasks**:
   ```
   datetime list
   ```
   Lists all your current Todoist tasks.

4. **List tasks with filter**:
   ```
   datetime list today
   ```
   Lists tasks due today.

## Task Creation Features

When adding a new task, you can specify:

1. **Task Description**: The main task content
2. **Due Date**: 
   - Simple dates: "tomorrow", "next monday"
   - Specific times: "tomorrow at 3pm"
   - Recurring: "every day at 9am", "every monday"
3. **Additional Description**: Add more details by including text after "--" 
4. **Priority**: Specify priority with "p1", "p2", "p3", or "p4" (4 being highest)
5. **Project Assignment**: Specify project with "#ProjectName"
6. **Labels**: Add labels with "@LabelName"

## Examples

```
datetime add Finish project report by Friday at 5pm -- This is important for the client meeting #Work @Reports p3
```

```
datetime add Water plants every 3 days starting tomorrow
```

```
datetime list overdue
```

## Standalone Usage

You can also use the module directly without AgentOS:

```bash
python main.py --add "Buy groceries tomorrow"
python main.py --list
```

## Error Handling

- The agent validates the API token on startup
- Natural language processing handles various date formats
- Network and API errors are handled gracefully
