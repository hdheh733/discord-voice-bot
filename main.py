import asyncio
import os
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask
import yt_dlp

# --- سيرفر الويب الخلفي لإبقاء البوت متصلاً 24/7 ---
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

# --- إعدادات البوت ---
TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)

# إعدادات متقدمة لتجاوز حظر يوتيوب باستخدام iOS client
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'no_warnings': True,
    'extractor_args': {'youtube': {'player_client': ['ios', 'mweb']}},
}

FFMPEG_OPTIONS = {
    'before_options': (
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    ),
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name} ({bot.user.id})')
  print('Bot is ready and online!')


# --- أمر قائمة الأوامر ---
@bot.command(name='help', aliases=['اوامر', 'الأوامر', 'commands'])
async def help_command(ctx):
  embed = discord.Embed(
      title='🎵 قائمة أوامر بوت الصوت',
      description='استخدم الرمز **`>`** قبل كل أمر:',
      color=discord.Color.blue(),
  )
  embed.add_field(
      name='▶️ `>play <الرابط أو الاسم>`',
      value='تشغيل مقطع من اليوتيوب، الساوند كلاود، أو ملف محلي.',
      inline=False,
  )
  embed.add_field(
      name='⏸️ `>pause`', value='إيقاف التشغيل مؤقتاً.', inline=False
  )
  embed.add_field(
      name='▶️ `>resume`', value='استئناف التشغيل بعد الإيقاف المؤقت.', inline=False
  )
  embed.add_field(
      name='⏹️ `>stop`', value='إيقاف الصوت تماماً.', inline=False
  )
  embed.add_field(
      name='👋 `>leave`', value='إخراج البوت من الروم الصوتي.', inline=False
  )
  embed.add_field(
      name='📜 `>help`', value='عرض هذه القائمة من جديد.', inline=False
  )
  embed.set_footer(text='عمل البوت مستمر 24/7 بدون توقف 🚀')
  await ctx.send(embed=embed)


# --- أمر التشغيل ---
@bot.command()
async def play(ctx, *, query: str):
  if not ctx.author.voice:
    await ctx.send('❌ يجب أن تكون في روم صوتي أولاً!')
    return

  channel = ctx.author.voice.channel

  if ctx.voice_client is None:
    vc = await channel.connect()
  else:
    vc = ctx.voice_client

  # 1. إذا كان المدخل ملفاً محلياً موجوداً في مشروعك
  if os.path.exists(query):
    if vc.is_playing() or vc.is_paused():
      vc.stop()
    try:
      vc.play(discord.FFmpegPCMAudio(query))
      await ctx.send(f'🎵 جاري تشغيل الملف المحلي: **{query}**')
    except Exception as e:
      await ctx.send(f'❌ خطأ في تشغيل الملف المحلي: {e}')
    return

  # 2. إذا كان المدخل رابطاً أو بحثاً عبر الإنترنت
  await ctx.send('🔍 جاري البحث وجلب الصوت...')
  loop = asyncio.get_event_loop()
  try:
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(query, download=False)
    )
    if 'entries' in data and len(data['entries']) > 0:
      data = data['entries'][0]

    source_url = data['url']
    title = data.get('title', 'صوت من الإنترنت')
  except Exception as e:
    await ctx.send(
        f'❌ حدث خطأ أثناء جلب المقطع. جرب كتابة اسم المقطع بدلاً من الرابط، أو'
        f' استخدم ساوند كلاود.\nالتفاصيل: {e}'
    )
    return

  if vc.is_playing() or vc.is_paused():
    vc.stop()

  try:
    player = discord.FFmpegPCMAudio(source_url, **FFMPEG_OPTIONS)
    vc.play(player)
    await ctx.send(f'🎵 جاري تشغيل: **{title}**')
  except Exception as e:
    await ctx.send(f'❌ خطأ أثناء تشغيل الصوت: {e}')


# --- الأوامر الأخرى ---
@bot.command()
async def pause(ctx):
  if ctx.voice_client and ctx.voice_client.is_playing():
    ctx.voice_client.pause()
    await ctx.send('⏸️ تم الإيقاف المؤقت للصوت.')
  else:
    await ctx.send('❌ لا يوجد صوت قيد التشغيل حالياً!')


@bot.command()
async def resume(ctx):
  if ctx.voice_client and ctx.voice_client.is_paused():
    ctx.voice_client.resume()
    await ctx.send('▶️ تم استئناف التشغيل.')
  else:
    await ctx.send('❌ الصوت ليس متوقفاً مؤقتاً!')


@bot.command()
async def stop(ctx):
  if ctx.voice_client and (
      ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
  ):
    ctx.voice_client.stop()
    await ctx.send('⏹️ تم إيقاف الصوت تماماً.')
  else:
    await ctx.send('❌ لا يوجد صوت قيد التشغيل.')


@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send('👋 تم الخروج من الروم الصوتي.')
  else:
    await ctx.send('❌ البوت ليس في روم صوتي.')


if TOKEN:
  bot.run(TOKEN)
else:
  print('Error: DISCORD_TOKEN is missing!')
