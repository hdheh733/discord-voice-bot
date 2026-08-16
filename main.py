import asyncio
import os
import sys
import aiohttp
import discord
from discord.ext import commands
import yt_dlp

# --- سيرفر الويب الخلفي المباشر عبر aiohttp ---
async def handle(request):
  return aiohttp.web.Response(text='Bot is online and active 24/7!')


async def start_web_server():
  app = aiohttp.web.Application()
  app.router.add_get('/', handle)
  runner = aiohttp.web.AppRunner(app)
  await runner.setup()
  port = int(os.environ.get('PORT', 8080))
  site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
  await site.start()
  print(f'Web server active on port {port}')


# --- إعدادات البوت والبادئة ---
TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)

# إعدادات YTDL مخصصة لمنع تراكم الاتصالات المعلقة
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
}

FFMPEG_OPTIONS = {
    'before_options': (
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    ),
    'options': '-vn',
}


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')


@bot.command()
async def play(ctx, *, query: str):
  if not ctx.author.voice:
    await ctx.send('❌ يجب أن تكون في روم صوتي أولاً!')
    return

  channel = ctx.author.voice.channel
  vc = ctx.voice_client if ctx.voice_client else await channel.connect()

  # 1. التشغيل المباشر للملفات المحلية بنفس المجلد
  if os.path.exists(query):
    if vc.is_playing():
      vc.stop()
    try:
      vc.play(discord.FFmpegPCMAudio(query))
      await ctx.send(f'🎵 جاري تشغيل الملف المحلي: **{query}**')
    except Exception as e:
      await ctx.send(f'❌ خطأ في تشغيل الملف المحلي: {e}')
    return

  # 2. التشغيل من الويب مع إغلاق الاتصال بأمان عند وجود حظر
  await ctx.send('🔍 جاري جلب المقطع...')
  loop = asyncio.get_event_loop()

  try:
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
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

      if vc.is_playing():
        vc.stop()

      vc.play(discord.FFmpegPCMAudio(source_url, **FFMPEG_OPTIONS))
      await ctx.send(f'🎵 جاري تشغيل: **{title}**')

  except Exception as e:
    print(f'Cloudflare/Fetch Error: {e}')
    await ctx.send(
        '❌ تعذر جلب الصوت بسبب حماية الموقع على الـ IP.\n'
        '💡 **جرّب:** رفع ملف MP3 إلى المشروع والتشغيل باسمه مباشرة.'
    )


@bot.command()
async def stop(ctx):
  if ctx.voice_client and ctx.voice_client.is_playing():
    ctx.voice_client.stop()
    await ctx.send('⏹️ تم الإيقاف.')


@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send('👋 تم المغادرة.')


async def main():
  await start_web_server()
  if not TOKEN:
    print('CRITICAL: DISCORD_TOKEN is missing!')
    sys.exit(1)
  await bot.start(TOKEN)


if __name__ == '__main__':
  asyncio.run(main())
