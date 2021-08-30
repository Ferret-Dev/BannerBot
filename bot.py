import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import time
from PIL import Image, ImageOps, ImageDraw, ImageFont
from colorthief import ColorThief
from discord import Embed, Member

bot = commands.Bot(command_prefix='>')
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.command()
async def banner(ctx):
  #files
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
bot.run(TOKEN)
