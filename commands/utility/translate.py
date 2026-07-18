import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from deep_translator import GoogleTranslator, exceptions

LANG_MAP = {
    "en": "english", "es": "spanish", "fr": "french", "de": "german",
    "it": "italian", "pt": "portuguese", "ru": "russian", "ja": "japanese",
    "ko": "korean", "zh": "chinese", "ar": "arabic", "hi": "hindi",
    "nl": "dutch", "pl": "polish", "sv": "swedish", "da": "danish",
    "fi": "finnish", "el": "greek", "he": "hebrew", "tr": "turkish",
    "th": "thai", "vi": "vietnamese", "id": "indonesian", "ms": "malay",
    "cs": "czech", "hu": "hungarian", "ro": "romanian", "uk": "ukrainian",
    "no": "norwegian",
}

class Translate(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="translate", aliases=["tr"], description="translate text", help="Translate text to a target language (default: English). Auto-detects source language. Usage: !tr hello, !tr es hello, !tr fr bonjour. Supported: en, es, fr, de, it, pt, ru, ja, ko, zh, ar, hi, and more.")
    @cooldown(1, 3, BucketType.user)
    async def translate(self, ctx, target_or_text: str, *, text: str = None):
        target = "en"
        source_text = target_or_text

        if text is not None:
            if target_or_text.lower() in LANG_MAP or len(target_or_text) == 2:
                target = target_or_text.lower()
                source_text = text
            else:
                source_text = f"{target_or_text} {text}"

        try:
            translator = GoogleTranslator(source="auto", target=target)
            result = await asyncio.to_thread(translator.translate, source_text)

            embed = discord.Embed(color=0x2b2d31)
            embed.add_field(name="◈ input", value=source_text[:1024], inline=False)
            embed.add_field(name=f"◈ {LANG_MAP.get(target, target)}", value=result[:1024], inline=False)
            embed.set_footer(text="m4-core · auto-detected source language")
            await ctx.send(embed=embed)

        except exceptions.LanguageNotSupportedException:
            await ctx.send(embed=discord.Embed(
                description=f"⊘ language `{target}` not supported. try `en`, `es`, `fr`, `de`, etc.",
                color=0xff4500
            ))
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                description=f"⊘ translation failed: {e}",
                color=0xff4500
            ))

async def setup(bot) -> None:
    await bot.add_cog(Translate(bot))