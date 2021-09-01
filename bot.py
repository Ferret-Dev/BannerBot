import discord
from discord.ext import commands
import subprocess
import sys
from asyncio import sleep
import os
import random
from quart import Quart, redirect, url_for, render_template, request
from dotenv import load_dotenv
import time
from PIL import Image, ImageOps, ImageDraw, ImageFont
from colorthief import ColorThief
from discord import Embed, Member
from pretty_help import DefaultMenu, PrettyHelp
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

load_dotenv()

app = Quart(__name__)

app.config["SECRET_KEY"] = "key"
app.config["DISCORD_CLIENT_ID"] = os.getenv("discord_client_id")  # Discord client ID.
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("discord_client_secret")  # Discord client secret.
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"   

Discord = DiscordOAuth2Session(app)

@app.route("/")
async def home():
	return await render_template("index.html", authorized = await Discord.authorized)

@app.route("/login")
async def login():
	return await Discord.create_session()

@app.route("/callback")
async def callback():
	try:
		await Discord.callback()
	except Exception:
		pass

	return redirect(url_for("logged_in"))

# bot confiuguration
navigation = DefaultMenu("◀️", "▶️", "❌")
bot = commands.Bot(command_prefix=">", description="A discord bot designed for generating profile-themed banners for Beat Saber!")
bot.remove_command("help")
token = os.getenv("token")

@bot.event
async def on_ready():
    print("I'm in")

class Commands(commands.Cog):
    """ All bot commands """
    @commands.command(
        name="banner",
        brief="get a banner from your discord pfp",
        help="Use this command to generate a cool banner from your pfp",
        aliases=["bnr", "b"]
    )
    async def _banner(self, ctx, target: discord.Member=None):
        target = target or ctx.author
        filename = 'pfp.png'
        await target.avatar_url.save(filename)
        pfp = Image.open('./pfp.png')
        mask = Image.open('./mask.png').convert('L')
        base = Image.open('./base.png')
        status = Image.open('./status.png')

        #crop
        crop = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
        crop.putalpha(mask)
        
        #resize
        time.sleep(1)
        new_size = (123, 124)
        resize = crop.resize(new_size)

        #pasting
        base.paste(resize,(201,323),resize)
        base.paste(status,(285,405),status)

        #text
        font = ImageFont.truetype(r'./unisans.ttf', 25)
        draw = ImageDraw.Draw(base)
        user = await bot.fetch_user(target.id)
        draw.text((262,472),str(user),(255,255,255),font=font,anchor='mm')
        base.save('nocolor.png')

        import cv2
        import numpy as np

        #coloring
        image = cv2.imread('./nocolor.png')
        ct = ColorThief('./pfp.png')
        value = ct.get_color(quality=1)
        xy = 268,232
        cv2.floodFill(image, None, xy, value)

        tmp = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _,alpha = cv2.threshold(tmp,0,255,cv2.THRESH_BINARY)
        b, g, r = cv2.split(image)
        rgba = [b,g,r, alpha]
        dst = cv2.merge(rgba,4)
        cv2.imwrite("banner.png", dst)
        
        #sending
        file = discord.File('./banner.png')
        await ctx.channel.send('Here\'s your banner, ' + target.name + '!', file=file)

        #deleting
        os.remove('./pfp.png')
        os.remove('./nocolor.png')
        os.remove('./banner.png')

    @commands.command(
        name="help",
        brief="get's bot help",
        help="Simple way to get command help!",
        aliases=["hlp", "h"]
    )
    async def _help(self, ctx):
        page_1 = discord.Embed(
                title="Index",
                description="The home page of the help command!", 
                colour=discord.Colour.green()
            )
        fields = [("`Index`", "Home page of the help command.", False),
                    ("`Commands`", "View all commands.", False)]

        page_1.set_footer(
            text="To scroll through pages, react to the arrows below."
        )

        for name, value, inline in fields:
            page_1.add_field(name=name, value=value, inline=inline)

        page_2 = discord.Embed(
            title="Commands", 
            description="View all commands", 
            colour=discord.Colour.green()
        )
        fields = [("`help`", "Your looking at this command.\n**aliases:** `hlp`, `h`", False),
                ("`userinfo`", "Generates a banner from your discord pfp!\n**aliases:** `bnr`, `b`", False)]

        page_2.set_footer(
            text=f"Handy tip! Put a handy tip here lol."
        )

        for name, value, inline in fields:
            page_2.add_field(name=name, value=value, inline=inline)

        message = await ctx.send(embed=page_1)
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        await message.add_reaction("❌")
        pages = 2
        current_page = 1

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️", "❌"]

        while True:
            try:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=60, check=check)

                if str(reaction.emoji) == "▶️" and current_page != pages:
                    current_page += 1

                    if current_page == 2:
                        await message.edit(embed=page_2)
                        await message.remove_reaction(reaction, user)

                if str(reaction.emoji) == "◀️" and current_page > 1:
                    current_page -= 1
                    
                    if current_page == 1:
                        await message.edit(embed=page_1)
                        await message.remove_reaction(reaction, user)

                    elif current_page == 2:
                        await message.edit(embed=page_2)
                        await message.remove_reaction(reaction, user)

                if str(reaction.emoji) == "❌":
                    await message.delete()
                    break

                else:
                    await message.remove_reaction(reaction, user)
                    
            except asyncio.TimeoutError:
                await message.delete()
                break
  
def run():
    bot.loop.create_task(app.run_task('0.0.0.0'))
    bot.add_cog(Commands(bot))
    bot.run(token)

if __name__ == "__main__":
	run()