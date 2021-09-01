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

# define application
app = Quart(__name__)

# config 
app.secret_key = os.environ.get("session")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"
app.config["DISCORD_CLIENT_ID"] = os.getenv("CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = os.getenv("RI")
app.config["DISCORD_BOT_TOKEN"] = os.getenv("token")
discordd = DiscordOAuth2Session(app)

@app.route("/")
async def home():
    logged = ""
    if await discordd.authorized:
        logged = True
        user = await discordd.fetch_user()

    return await render_template("index.html", logged=logged)

@app.route("/login/")
async def login():
    return await discordd.create_session(scope=["identify", "guilds"])

@app.route("/logout/")
async def logout():
    discordd.revoke()
    return redirect(url_for(".home"))

@app.route("/me/")
@requires_authorization
async def me():
    user = await discordd.fetch_user()
    return redirect(url_for(".home"))

@app.route("/callback/")
async def callback():
    await discordd.callback()
    try:
        return redirect(bot.url)
    except:
        return redirect(url_for(".me"))

@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    bot.url = request.url
    return redirect(url_for(".login"))

# bot confiuguration
navigation = DefaultMenu("◀️", "▶️", "❌")
bot = commands.Bot(command_prefix=">", description="A discord bot designed for generating profile-themed banners for Beat Saber!")
bot.help_command = PrettyHelp(navigation=navigation, color=discord.Colour.grey())
token = os.environ.get("token")


@bot.event
async def on_ready():
    print("I'm in")


class Commands(commands.Cog):
    """ All bot commands """
    @commands.command(
        name="banner",
        brief="get a banner from your discord pfp",
        help="Use this command to generate a cool banner from your pfp"
    )
    async def _banner(self, ctx):
        filename = 'pfp.png'
        await ctx.author.avatar.save(filename)
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
        user = await bot.fetch_user(ctx.author.id)
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
        await ctx.channel.send('Here\'s your banner, ' + ctx.author.name + '!', file=file)

        #deleting
        os.remove('./pfp.png')
        os.remove('./nocolor.png')
        os.remove('./banner.png')
  
def run():
    bot.loop.create_task(app.run_task('0.0.0.0'))
    bot.add_cog(Economy(bot))
    bot.run(token)

if __name__ == "__main__":
    run()