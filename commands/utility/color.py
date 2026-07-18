import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
from PIL import Image
import io
import colorsys

NAMED_COLORS = {
    "red": 0xff0000, "green": 0x00ff00, "blue": 0x0000ff,
    "yellow": 0xffff00, "cyan": 0x00ffff, "magenta": 0xff00ff,
    "white": 0xffffff, "black": 0x000000, "gray": 0x808080,
    "orange": 0xffa500, "purple": 0x800080, "pink": 0xffc0cb,
    "brown": 0xa52a2a, "navy": 0x000080, "teal": 0x008080,
    "maroon": 0x800000, "lime": 0x00ff00, "gold": 0xffd700,
    "indigo": 0x4b0082, "violet": 0xee82ee, "coral": 0xff7f50,
    "salmon": 0xfa8072, "tomato": 0xff6347, "wheat": 0xf5deb3,
}

class Color(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="color", aliases=["colour"], description="show info and swatch for a hex color or name", help="Show color information for a hex code or named color. Displays RGB, HSV, HSL, complementary color, and a side-by-side swatch image. Examples: !color #ff4500, !color red, !color navy")
    @cooldown(1, 3, BucketType.user)
    async def color(self, ctx, *, query: str):
        query = query.strip().lower()

        if query in NAMED_COLORS:
            hex_code = format(NAMED_COLORS[query], "06x")
        else:
            hex_code = query.lstrip("#")
            if len(hex_code) not in (3, 6) or not all(c in "0123456789abcdef" for c in hex_code):
                return await ctx.send(embed=discord.Embed(
                    description="⊘ provide a valid hex code (e.g. `!color #ff4500`) or color name (e.g. `!color red`)",
                    color=0xff4500
                ))

        if len(hex_code) == 3:
            hex_code = "".join(c * 2 for c in hex_code)

        r, g, b = int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        hls_h, hls_l, hls_s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

        # complementary
        comp_h = (h + 0.5) % 1.0
        comp_r, comp_g, comp_b = colorsys.hsv_to_rgb(comp_h, s, v)
        comp_hex = f"{int(comp_r * 255):02x}{int(comp_g * 255):02x}{int(comp_b * 255):02x}"

        img = Image.new("RGB", (200, 200), (r, g, b))
        comp_img = Image.new("RGB", (200, 200), (int(comp_r * 255), int(comp_g * 255), int(comp_b * 255)))

        # combine swatches
        combined = Image.new("RGB", (420, 200), (30, 30, 30))
        combined.paste(img, (10, 0))
        combined.paste(comp_img, (220, 0))

        buf = io.BytesIO()
        combined.save(buf, format="PNG")
        buf.seek(0)

        embed = discord.Embed(
            title=f"#{hex_code.upper()}",
            description=f"↔ complementary: **#{comp_hex.upper()}**",
            color=int(hex_code, 16)
        )
        embed.add_field(name="◈ rgb", value=f"`{r}, {g}, {b}`", inline=True)
        embed.add_field(name="◈ hsv", value=f"`{round(h * 360)}°, {round(s * 100)}%, {round(v * 100)}%`", inline=True)
        embed.add_field(name="◈ hsl", value=f"`{round(hls_h * 360)}°, {round(hls_s * 100)}%, {round(hls_l * 100)}%`", inline=True)
        embed.set_image(url="attachment://swatch.png")

        await ctx.send(embed=embed, file=discord.File(buf, filename="swatch.png"))

async def setup(bot) -> None:
    await bot.add_cog(Color(bot))