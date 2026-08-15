import asyncio
import os
import sys
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask

# --- سيرفر الويب الخلفي للمحافظة على الاتصال ---
app = Flask(__name__)


@app.route('/')
def home():
  return 'Bot is online and active 24/7!'


def run_web_server():
  port = int(os.environ.get('PORT', 8080))
  # استخدام 0.0.0.0 أساسي للاستجابة لفحص الصحة من Render
  app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# تشغيل سيرفر الويب في Thread منفصل تماماً
server_thread = Thread(target=run_web_server)
server_thread.daemon = True
server_thread.start()

# --- إعدادات البوت ---
TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
  print('Ready and listening for commands!')


@bot.command(name='help', aliases=['اوامر', 'الأوامر'])
async def help_command(ctx):
  embed = discord.Embed(
      title='🎵 قائمة أوامر بوت الصوت',
      description='استخدم الرمز **`>`** قبل كل أمر:',
      color=discord.Color.blue(),
  )
  embed.add_field(
      name='▶️ `>play <الاسم أو الرابط>`',
      value='تشغيل صوت من يوتيوب/ساوند كلاود أو ملف محلي.',
      inline=False,
  )
  embed.add_field(
      name='⏹️ `>stop`', value='إيقاف التشغيل تماماً.', inline=False
  )
  embed.add_field(
      name='👋 `>leave`', value='إخراج البوت من الروم.', inline=False
  )
  await ctx.send(embed=embed)


@bot.command()
async def play(ctx, *, query: str):
  if not ctx.author.voice:
    await ctx.send('❌ يجب أن تكون في روم صوتي أولاً!')
    return

  channel = ctx.author.voice.channel
  vc = ctx.voice_client if ctx.voice_client else await channel.connect()

  # تشغيل الملفات المحلية المرفوعة للمشروع
  if os.path.exists(query):
    if vc.is_playing():
      vc.stop()
    try:
      vc.play(discord.FFmpegPCMAudio(query))
      await ctx.send(f'🎵 جاري تشغيل الملف: **{query}**')
    except Exception as e:
      await ctx.send(f'❌ خطأ في التشغيل: {e}')
    return

  await ctx.send(
      '💡 لتشغيل الأغاني بدقة وبدون حظر الـ IP، ارفع ملف `.mp3` إلى GitHub واستخدم'
      ' اسمه.'
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


# التشغيل المباشر مع التحقق من التوكن
if __name__ == '__main__':
  if not TOKEN:
    print('CRITICAL ERROR: DISCORD_TOKEN Environment Variable is missing!')
    sys.exit(1)
  bot.run(TOKEN)
