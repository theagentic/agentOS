# File Management Agent for AgentOS

This agent provides file and directory management capabilities for the AgentOS platform, allowing you to interact with your file system through voice or text commands.

## Features

- Browse directories and list files
- Open files with associated applications
- Search for files by name or content
- Copy, move, rename, and delete files
- Create and manage folders
- Get file information and statistics
- Security-oriented design with configurable allowed directories

## Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure allowed directories in the `.env` file:
   ```
   ALLOWED_DIRECTORIES=/home/user/Documents,/home/user/Downloads
   DEFAULT_DIRECTORY=/home/user/Documents
   OPEN_WITH_DEFAULT_APP=true
   ```

   This restricts file operations to only the specified directories for security.

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage in AgentOS

### Basic File Operations

1. **List files in a directory**:
   ```
   filemanage list
   ```
   Lists files in the default directory.

   ```
   filemanage list ~/Documents
   ```
   Lists files in a specific directory.

2. **Open a file**:
   ```
   filemanage open document.pdf
   ```
   Opens the file with the default application.

3. **Get file information**:
   ```
   filemanage info document.pdf
   ```
   Shows file size, creation date, and other information.

### File Management

1. **Search for files**:
   ```
   filemanage search budget
   ```
   Searches for files containing "budget" in the name.

2. **Create a new directory**:
   ```
   filemanage mkdir new_folder
   ```
   Creates a new directory.

3. **Copy a file**:
   ```
   filemanage copy source.txt destination.txt
   ```
   Copies a file from source to destination.

4. **Move a file**:
   ```
   filemanage move file.txt ~/Documents/
   ```
   Moves a file to another location.

5. **Rename a file**:
   ```
   filemanage rename old_name.txt new_name.txt
   ```
   Renames a file.

6. **Delete a file**:
   ```
   filemanage delete file.txt
   ```
   Deletes a file (with confirmation).

### Advanced Features

1. **File content search**:
   ```
   filemanage find-text "search phrase" ~/Documents
   ```
   Searches for text content within files.

2. **Get directory statistics**:
   ```
   filemanage stats ~/Documents
   ```
   Shows statistics about the directory (size, file counts, etc.).

## Security Considerations

- The agent only allows operations in directories specified in the `.env` file
- File operations that could be dangerous require explicit confirmation
- The agent validates all paths against the allowed list
- All file operations are logged for auditing purposes

## Configuration Options

In the `.env` file, you can configure:

- `ALLOWED_DIRECTORIES`: Comma-separated list of directories the agent can access
- `DEFAULT_DIRECTORY`: The default directory for operations without a specified path
- `OPEN_WITH_DEFAULT_APP`: Whether to allow opening files with default applications
- `ENABLE_DELETE`: Whether to allow file deletion operations
- `LOG_LEVEL`: Level of detail for logging (INFO, DEBUG, WARNING, etc.)

## Help and Documentation

For additional help and a list of all available commands, use:
```
filemanage help
```
