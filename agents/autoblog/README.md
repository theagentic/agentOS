# AutoBlog Agent for AgentOS

This agent automatically generates blog posts from your GitHub repositories and publishes them to your blog.

## Setup

1. Copy `.env-example` to `.env` and set your credentials:
   ```
   cp .env-example .env
   ```

2. Edit the `.env` file with your information:
   ```
   # GitHub Configuration
   GITHUB_TOKEN=your_github_token_here
   GITHUB_USERNAME=your_github_username_here

   # Blog Configuration
   OBSIDIAN_VAULT_PATH=C:/path/to/your/obsidian/vault
   BLOG_POSTS_FOLDER=blog_posts
   BLOG_REPO_PATH=C:/path/to/your/blog/repo

   # OpenRouter API Key (optional - for enhanced blog post generation)
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## Using with AgentOS Frontend

The AutoBlog agent is fully integrated with the AgentOS frontend. You can interact with it using these commands:

1. **Help**: Get a list of available commands
   ```
   autoblog help
   ```

2. **Generate**: Create blog posts from your GitHub repositories
   ```
   autoblog generate
   ```

3. **Status**: Check the current status of the autoblog agent
   ```
   autoblog status
   ```

4. **Set Date**: Set a reference date for repository filtering
   ```
   autoblog setdate 2024-01-01
   ```

5. **Process Specific Repository**: Process a specific repository by name
   ```
   autoblog blog-repo REPOSITORY_NAME
   ```
   This command will process the specified repository even if it has been processed before. This is useful for testing or updating existing blog posts.

The frontend will display real-time progress updates during the blog generation process, showing you each step as it happens.

## Using from Command Line

You can also use the autoblog agent directly from the command line using the provided script:

```bash
# Show help
python run_autoblog.py help

# Generate blog posts
python run_autoblog.py generate

# Check status
python run_autoblog.py status

# Set reference date
python run_autoblog.py setdate 2024-01-01

# Process specific repository
python run_autoblog.py blog-repo REPOSITORY_NAME
```

The command line script will show real-time progress updates when running the `generate` and `blog-repo` commands.

## How It Works

The AutoBlog agent performs these steps during blog generation:

1. Scans your GitHub repositories for ones that haven't been processed
2. Analyzes each repository's README.md and other files
3. Generates a structured blog post with:
   - Title and description
   - Technologies used
   - Key features
   - Implementation details
   - GitHub repository link
4. Saves the blog post to your Obsidian vault
5. Commits and pushes the changes to your blog repository

## Troubleshooting

If you encounter issues:

1. Check your `.env` file to ensure all paths and credentials are correct
2. Verify that your GitHub token has the necessary permissions
3. Make sure your Obsidian vault and blog repository paths exist
4. Check the logs for detailed error messages
5. If a repository doesn't have a README.md file, it will be skipped
6. Try the `blog-repo` command if the automatic discovery isn't finding your repository

## Further Help

For more detailed information about any command, use the help command or refer to the source code in this directory. 