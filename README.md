# M4 Core

Discord bot for the Immie server, built with discord.py and cogs.

## Features

- **Economy system** (cores currency, gambling, transfers, rob, crime, daily, work, begging)
- **Shop system** (`!shop` / `!buy` / `!inventory` / `!open`) — buy special items that modify command behavior:
  - *Donut* (⌬ 5,000) — bribe the cops, halve fines
  - *Pet Rock* (⌬ 500) — does nothing, collector item
  - *Lucky Socks* (⌬ 6,000) — +5% gambling win rate
  - *Fake License* (⌬ 8,000) — -1 min crime/rob cooldown
  - *Mystery Box* (⌬ 15,000) — random prize up to ⌬ 100k
  - *Alarm System* (⌬ 25,000) — 30% chance robber pays double
  - *Extra Luck* (⌬ 30,000) — +15% success on crime/rob, +10% earnings
  - *Stealthy Shoes* (⌬ 45,000) — +15% steal, delayed victim notification
  - *Invisibility Potion* (⌬ 60,000) — +5% success, no trace in logs
- **Transaction history** (`!history`) — track earnings, losses, transfers, purchases
- **Moderation** (ban, kick, timeout, warn, purge, slowmode, lock, lockdown, nick, move)
- **Fun commands** (8ball, ship, roast, impostor, dice, password generator, etc.)
- **Utility** (weather with 5-day forecast, translate, reminders, QR codes, polls, timer with DM notification, AFK, userinfo, serverinfo, snipe/editsnipe, text tools)
- **AI chat** via Slug (Groq API)
- **Anonymous confessions**, Hall of Fame, welcome messages, leveling, reaction roles
- **Remote eval console**, hot-reload, GitHub pull
- **Web-based terminal** to manage bot, pull, restart, and remotely execute code (after PIN login)

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
pyfiglet
```

Install with:

```bash
pip install -r requirements.txt
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
pip install -r requirements.txt
```

**3. Set environment variables**

You'll need to set environment variables for the bot to work.

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✓ | your bot token |
| `PANEL_PORT` | - | port for the web panel |
| `PANEL_HOSTNAME` | - | fake hostname to show in web panel |
| `PANEL_USER` | - | user name to show in web panel |
| `SESSION_SECRET` | - | signing session cookies for web panel|
| `PANEL_PIN` | ✓ | password to enter web panel |
| `EMERGENCY_PASSPHRASE` | - | phrase to DM bot to regain emergency admin access |
| `GROQ_KEY` | ✓ | groq API key for slug AI chat |
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

You can also set channels at runtime using set commands (e.g. `!setwelcome #channel`).

**5. Add yourself as admin**

Edit `admins.yaml`:

```yaml
admins:
  - YOUR_DISCORD_USER_ID
```

**6. Run the bot**

```bash
python main.py
```

## Branches

- **canary** — active development and testing

## Hot Reload

Use `!reload` to reload all cogs without restarting, or `!pull [branch]` to sync from GitHub and auto-reload.

## Data

All data such as economy, shop inventory, transaction history, and statistics are stored in `.msgpack` format inside the `data/` folder.
