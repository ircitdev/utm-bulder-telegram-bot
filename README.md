# UTM Builder Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A powerful Telegram bot that helps marketers and digital professionals create UTM-marked links for tracking marketing campaigns. The bot automatically shortens URLs using the YOURLS API and provides detailed analytics on link performance.

## 🌟 Features

- **Interactive UTM Parameter Collection**: Guided process for collecting all standard UTM parameters:
  - `utm_source`: Identifies which site sent traffic (e.g., google, facebook)
  - `utm_medium`: Identifies the type of link used (e.g., cpc, banner, email)
  - `utm_campaign`: Identifies a specific product promotion or strategic campaign
  - `utm_term`: Identifies paid search keywords

- **Smart URL Shortening**: Automatically shortens your UTM-marked URLs using YOURLS API
- **Predefined Options**: Quick selection of common UTM parameter values for faster link creation
- **Custom Parameters**: Option to enter custom UTM parameter values
- **Statistics Dashboard**: View top 15 most popular links by clicks with the `/stats` command
- **Multi-language Interface**: Russian interface with English documentation
- **Persistent State Management**: Maintains user session state during link creation process
- **Markdown Support**: Properly formatted responses with Markdown
- **Error Handling**: Comprehensive error handling and user feedback

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- YOURLS API endpoint (for URL shortening)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ircitdev/utm-bulder-telegram-bot.git
   cd utm-bulder-telegram-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables (see Configuration section below)

4. Run the bot:
   ```bash
   python utm_telegram_bot.py
   ```

### Docker Installation (Alternative)

1. Build the Docker image:
   ```bash
   docker build -t utm-telegram-bot .
   ```

2. Run the container:
   ```bash
   docker run --env-file .env utm-telegram-bot
   ```

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
# Telegram Bot Token
BOT_TOKEN=your_telegram_bot_token_here

# YOURLS API settings
URL_SHORTENER_API=http://your-domain.com/yourls-api.php
URL_SHORTENER_SIGNATURE=your_yourls_signature_here

# Database settings (optional)
DATABASE_URL=sqlite:///utm_bot.db

# Logging level
LOG_LEVEL=INFO

# HTTP timeout (seconds)
HTTP_TIMEOUT=10
```

### Environment Variables Explained

- `BOT_TOKEN`: Your Telegram bot token obtained from [@BotFather](https://t.me/BotFather)
- `URL_SHORTENER_API`: The endpoint for your YOURLS API (e.g., http://your-domain.com/yourls-api.php)
- `URL_SHORTENER_SIGNATURE`: Your YOURLS API signature for authentication
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `HTTP_TIMEOUT`: HTTP request timeout in seconds

## 📡 Usage

1. Start a conversation with your bot in Telegram
2. Send `/start` to begin creating a UTM link
3. Enter the URL you want to track
4. Select or enter UTM parameters through the interactive menu
5. Get both the full UTM-marked URL and a shortened version
6. Use `/stats` to view the top 15 most popular links by clicks
7. Use `/help` to see available commands and instructions

### UTM Parameters Guide

- **utm_source**: Required. Identifies which site sent traffic to your site
- **utm_medium**: Required. Identifies what type of link was used
- **utm_campaign**: Required. Identifies a specific product promotion or strategic campaign
- **utm_term**: Optional. Identifies paid search keywords

## 🛠 Technical Details

### Project Structure

```
utm-bulder-telegram-bot/
├── utm_telegram_bot.py     # Main bot implementation
├── config.py              # Configuration and constants
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
├── README.md              # This file
└── LICENSE                # MIT License
```

### Dependencies

- `pyTelegramBotAPI`: Python library for Telegram Bot API
- `requests`: HTTP library for API calls
- `python-dotenv`: Environment variable management
- `urllib3`: HTTP client library

### State Management

The bot uses an in-memory state management system to track user progress through the UTM parameter collection process:

1. `START`: Initial state
2. `COLLECTING_URL`: Waiting for URL input
3. `COLLECTING_SOURCE`: Collecting utm_source parameter
4. `COLLECTING_MEDIUM`: Collecting utm_medium parameter
5. `COLLECTING_CAMPAIGN`: Collecting utm_campaign parameter
6. `COLLECTING_TERM`: Collecting utm_term parameter
7. `READY_TO_GENERATE`: All parameters collected, ready to generate link

## 📊 Statistics Feature

The bot includes a powerful statistics feature accessible via the `/stats` command:

1. Fetches data from YOURLS API
2. Sorts links by click count in descending order
3. Displays top 15 most popular links
4. Shows full URL, shortened URL, and click count for each link
5. Provides real-time data updates

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

If you have any questions or need help with setup, please open an issue on GitHub.

## 🙏 Acknowledgments

- Thanks to the [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) team for their excellent library
- Thanks to [YOURLS](https://yourls.org/) for the URL shortening platform