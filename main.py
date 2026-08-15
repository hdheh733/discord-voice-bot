import asyncio
import os
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask
import imageio_ffmpeg
import yt_dlp

# جلب المسار المباشر لبرنامج ffmpeg المدمج
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

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

# --- إعدادات البوت والبادئة (Prefix) ---
TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'user_agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ),
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
  print(f'FFmpeg Path: {FFMPEG_PATH}')
  print('Bot is ready and online!')


# --- أمر عرض قائمة الأوامر ---
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

  # 1. التشغيل من ملف محلي موجود بمجلد المشروع
  if os.path.exists(query):
    if vc.is_playing() or vc.is_paused():
      vc.stop()
    try:
      player = discord.FFmpegPCMAudio(query, executable=FFMPEG_PATH)
      vc.play(player)
      await ctx.send(f'🎵 جاري تشغيل الملف المحلي: **{query}**')
    except Exception as e:
      await ctx.send(f'❌ خطأ أثناء تشغيل الملف المحلي: {e}')
    return

  # 2. التشغيل من رابط أو عبر البحث
  await ctx.send('🔍 جاري البحث وجلب الصوت...')
  loop = asyncio.get_event_loop()

  try:
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(query, download=False)
    )

    if not data:
      await ctx.send('❌ لم يتم العثور على نتائج!')
      return

    if 'entries' in data and len(data['entries']) > 0:
      data = data['entries'][0]

    source_url = data.get('url')
    title = data.get('title', 'صوت من الإنترنت')

  except Exception as e:
    await ctx.send(
        '❌ تعذر جلب المقطع بسبب حماية الموقع (Cloudflare/Bot Block).\n'
        '💡 **جرّب:** البحث باسم المقطع أو استخدام رابط SoundCloud أو ملف'
        ' محلي.'
    )
    print(f'Extraction Error: {e}')
    return

  if vc.is_playing() or vc.is_paused():
    vc.stop()

  try:
    player = discord.FFmpegPCMAudio(
        source_url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS
    )
    vc.play(player)
    await ctx.send(f'🎵 جاري تشغيل: **{title}**')
  except Exception as e:
    await ctx.send(f'❌ خطأ في تشغيل الصوت: {e}')


# --- الأوامر الأساسية الأُخرى ---
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
