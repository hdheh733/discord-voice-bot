import os
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask

# --- تشغيل سيرفر الويب الخلفي لإبقاء البوت متصلاً في Render ---
app = Flask('')


@app.route('/')
def home():
  return 'Bot is online and active 24/7!'


def run():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = Thread(target=run)
  t.daemon = True
  t.start()


keep_alive()

# --- كود بوت الديسكورد الأساسي ---
TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name} ({bot.user.id})')
  print('Ready and connected to Discord Gateway!')


@bot.command()
async def play(ctx, file_name: str):
  if not ctx.author.voice:
    await ctx.send('يجب أن تكون في روم صوتي أولاً!')
    return

  channel = ctx.author.voice.channel

  if ctx.voice_client is None:
    vc = await channel.connect(cls=discord.FFmpegPCMAudio)
  else:
    vc = ctx.voice_client

  if not os.path.exists(file_name):
    await ctx.send(f'الملف `{file_name}` غير موجود!')
    return

  if vc.is_playing():
    vc.stop()

  def after_playing(error):
    if error:
      print(f'Error: {error}')

  vc.play(discord.FFmpegPCMAudio(file_name), after=after_playing)
  await ctx.send(f'جاري تشغيل: `{file_name}`')


@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send('تم الخروج من الروم الصوتي.')
  else:
    await ctx.send('البوت ليس في روم صوتي حالياً.')


if TOKEN:
  bot.run(TOKEN)
else:
  print('Error: DISCORD_TOKEN is not set in Environment Variables!')
