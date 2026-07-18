import discord
import os
import aiohttp
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

FORECAST = ["clear sky", "few clouds", "scattered clouds", "broken clouds", "shower rain", "rain", "thunderstorm", "snow", "mist"]
FORECAST_ICONS = {"clear sky": "☀️", "few clouds": "⛅", "scattered clouds": "☁️", "broken clouds": "☁️",
                  "shower rain": "🌦", "rain": "🌧", "thunderstorm": "⛈", "snow": "❄️", "mist": "🌫"}

class Weather(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def cog_unload(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _fetch(self, url: str, params: dict) -> dict | None:
        session = await self._get_session()
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 401:
                    return None
                if resp.status == 404:
                    return None
                if resp.status != 200:
                    return None
                return await resp.json()
        except (aiohttp.ClientError, ValueError, TypeError):
            return None

    @commands.hybrid_command(name="weather", aliases=["w", "forecast"], description="get current weather or 5-day forecast", help="Get current weather or 5-day forecast for any city. Usage: !weather london, !weather tokyo, !forecast paris. Uses OpenWeatherMap. Shows temp (°C/°F), humidity, wind, and conditions.")
    @cooldown(1, 5, BucketType.user)
    async def weather(self, ctx, *, city: str):
        api_key = os.getenv("OPENWEATHER_KEY")
        if not api_key:
            return await ctx.send(embed=discord.Embed(description="✖ OPENWEATHER_KEY not set in .env.", color=0xff4500))

        is_forecast = city.lower().startswith("forecast ")
        search = city[9:].strip() if is_forecast else city
        if not search:
            return await ctx.send(embed=discord.Embed(description="✖ specify a city name.", color=0xff4500))

        if is_forecast:
            url = "https://api.openweathermap.org/data/2.5/forecast"
        else:
            url = "https://api.openweathermap.org/data/2.5/weather"

        try:
            data = await self._fetch(url, {"q": search, "appid": api_key, "units": "metric"})
        except aiohttp.ClientError:
            return await ctx.send(embed=discord.Embed(
                description="✖ could not reach the weather service.",
                color=0xff4500
            ))
        if data is None:
            return await ctx.send(embed=discord.Embed(
                description="✖ city not found or api error.",
                color=0xff4500
            ))

        if is_forecast:
            embed = discord.Embed(
                title=f"◈ 5-day forecast · {search.title()}",
                color=0x2b2d31
            )
            seen = set()
            for entry in data.get("list", []):
                day = entry["dt_txt"][:10]
                if day in seen:
                    continue
                seen.add(day)
                if len(seen) > 5:
                    break
                temp = round(entry["main"]["temp"])
                desc = entry["weather"][0]["description"]
                icon = FORECAST_ICONS.get(desc, "🌡")
                embed.add_field(name=day, value=f"{icon} {temp}°C · {desc}", inline=False)
            embed.set_footer(text="m4-core · powered by openweathermap")
            return await ctx.send(embed=embed)

        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        desc = data["weather"][0]["description"]
        city_name = data["name"]
        country = data["sys"]["country"]
        temp_f = round(temp * 9/5 + 32, 1)
        icon = FORECAST_ICONS.get(desc, "🌡")

        embed = discord.Embed(
            title=f"{icon} {city_name}, {country}",
            description=f"**{desc}**",
            color=0x2b2d31
        )
        embed.add_field(name="🌡 temp", value=f"`{temp}°C / {temp_f}°F`", inline=True)
        embed.add_field(name="🤔 feels like", value=f"`{feels}°C`", inline=True)
        embed.add_field(name="💧 humidity", value=f"`{humidity}%`", inline=True)
        embed.add_field(name="💨 wind", value=f"`{wind} m/s`", inline=True)
        embed.set_footer(text="use !forecast <city> for 5-day · powered by openweathermap")
        await ctx.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Weather(bot))