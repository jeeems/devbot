# DevBot
A Discord bot designed to assist developers with code quality, project analysis, and AI-powered code reviews. DevBot helps identify potential issues, suggest enhancements, and understand project structures, making your development workflow smoother and more efficient.

## ✨ Features
- **Repository Analysis** (`!analyze`): Scan a GitHub repository to get insights into its code quality, potential issues, unused imports/functions, and general suggestions.

- **AI Code Review** (`!ai-review`): Get an in-depth, AI-powered code review for a specific file within a GitHub repository, covering bugs, code quality, performance, security, and best practices.

- **Project Structure Analysis** (`!structure`): Visualize the directory and file structure of a GitHub repository, along with framework detection and structural recommendations.

- **File Upload Analysis** (`!upload`): Upload a local code file directly to the bot for quick analysis and suggestions.

- **AI Chat** (`!chat`): Engage in a conversation with an AI assistant for general development help, debugging tips, and coding advice.

- **File Search** (`!search`): Quickly locate specific files within a GitHub repository.

- **Bot Status** (`!status`): Check the operational status of the bot and its API connections.

## 🚀 Getting Started
Follow these steps to set up and run your DevBot.

### Prerequisites
- Python 3.8+
- pip (Python package installer)
- A Discord Bot Token
- A GitHub Personal Access Token (PAT)
- A Groq API Key (for AI features)
- (Optional) An OpenAI API Key (if you plan to use OpenAI models, though Groq is currently configured)

### 1. Clone the Repository
```bash
git clone https://github.com/jeeems/devbot.git
cd devbot
```

### 2. Set up a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.

```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, you'll need to create it. Based on the provided code, you'll need at least:
- discord.py
- PyGithub
- python-dotenv
- requests

You can generate it by running `pip freeze > requirements.txt` after installing the necessary libraries.

### 4. Configure Environment Variables
Create a `.env` file in the root directory of your project and add the following:

```env
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
GITHUB_TOKEN=YOUR_GITHUB_PERSONAL_ACCESS_TOKEN
GROQ_API_KEY=YOUR_GROQ_API_KEY
# OPENAI_API_KEY=YOUR_OPENAI_API_KEY # Uncomment and set if you plan to use OpenAI
```

- **DISCORD_TOKEN**: Get this from the Discord Developer Portal. Make sure your bot has the necessary intents enabled (especially Message Content Intent).
- **GITHUB_TOKEN**: Generate a Personal Access Token from your GitHub settings (Settings -> Developer settings -> Personal access tokens -> Tokens (classic)). It needs repo scope for full repository access.
- **GROQ_API_KEY**: Obtain this from the Groq Console.

### 5. Run the Bot
```bash
python bot.py
```

The bot should now be online and ready to receive commands in your Discord server.

## 🤖 Usage
Invite your bot to your Discord server and use the `!` prefix for commands.

`!help-dev`: Displays a list of all available commands and their usage.

### Examples:

**Analyze a GitHub Repository:**
```
!analyze https://github.com/octocat/Spoon-Knife main
```

**Get AI Code Review for a File:**
```
!ai-review https://github.com/your-username/your-repo main.py
```

**Show Project Structure:**
```
!structure https://github.com/octocat/Spoon-Knife
```

**Chat with the AI Assistant:**
```
!chat What's the best way to handle asynchronous operations in Python?
```

**Upload a File for Analysis:**
(Attach a file to your Discord message and type `!upload` in the comment)

## 📁 Project Structure
```
devbot/
├── cogs/
│   ├── __pycache__/
│   ├── analysis_cog.py          # Commands for code analysis, AI review, and structure
│   └── general_cog.py           # General commands like chat, help, and status
├── core/
│   ├── __pycache__/
│   ├── analyzers.py             # Core logic for code analysis, structure detection, and AI integration
│   └── github_client.py         # Handles GitHub API interactions and repository access
├── venv/                        # Python virtual environment
├── .env                         # Environment variables (Discord token, GitHub token, API keys)
├── bot.log                      # Bot's log file
├── bot.py                       # Main bot entry point and setup
├── requirements.txt             # Project dependencies
└── README.md                    # This file
```

## 🤝 Contributing
Contributions are welcome! If you have suggestions for improvements or new features, please feel free to:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add new feature'`).
5. Push to the branch (`git push origin feature/your-feature`).
6. Open a Pull Request.