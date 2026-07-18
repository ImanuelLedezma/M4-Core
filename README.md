# M4 Core

Discord bot for the Immie server, built with discord.py and cogs.

## Features

- Economy system (cores currency, gambling, transfers)
- Moderation (ban, kick, timeout, warn, purge)
- Fun commands (8ball, ship, roast, impostor, etc.)
- Utility (weather, translate, reminders, QR, polls)
- AI chat via Slug (Groq API)
- Anonymous confessions, Hall of Fame, welcome messages
- Remote eval console, hot-reload, GitHub pull
- Web-based terminal to manage bot, pull, restart and remotely execute code (After login)

## Dependencies

```
discord.py>=2.3.0
aiohttp
groq
pyyaml
qrcode[pil]
Pillow
deep-translator
requests
msgpack
```

Install with:

```bash
pip install -r requirements
```

If you want to expose your web panel to the Internet, you may also need a reverse proxy such as Nginx or cloudflared.

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/ImanuelLedezma/M4-Core.git
cd M4-Core
```

**2. Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements
```

**3. Set environment variables**

You'll need to set enviroment variables for the bot to work.

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✓ | your bot token |
| `PANEL_PORT` | - | port for the web panel |
| `PANEL_HOSTNAME` | - | fake hostname to show in web panel |
| `PANEL_USER` | - | user name to show in web pabel |
| `SESSION_SECRET` | - | signing session cookies for web panel|
| `PANEL_PIN` | ✓ | password to enter web panel |
| `EMERGENCY_PASSPHRASE` | - | phrase to DM bot for to regain emergency admin access |
| `GROQ_KEY` | ✓ | groq api key for slug ai chat |
| `OPENWEATHER_KEY` | ✓ | openweathermap key for `!weather` |

**4. Configure `config.yaml`**

Edit `config.yaml` at the root with your server's channel and guild IDs:

```yaml
guild_id: YOUR_GUILD_ID

channels:
  log: 0
  console: 0
  ai_chat: 0
  dictionary: 0
  confession: 0
  hall_of_fame: 0
  welcome: 0
```

You can also set channels at runtime using the set commands (e.g. `!setwelcome #channel`).

**5. Add yourself as admin**

Edit `admins.yaml`:

```yaml
- YOUR_DISCORD_USER_ID
```

**6. Run the bot**

```bash
python main.py
```

## Branches

- **main** — stable, production-ready
- **canary** — active development and testing

## Hot Reload

Use `!reload` to reload all cogs without restarting, or `!pull [branch]` to sync from GitHub and auto-reload.

## Data

All data such as Economy or statistics are stored in .msgpack format inside the data/ folder.