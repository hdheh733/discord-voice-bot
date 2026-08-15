import asyncio
import os
import sys
import discord
from discord.ext import commands
from aiohttp import web

# --- سيرفر خفيف لـ Port Binding الخاص بـ Render ---
async def handle(request):
    return web.Response(text="Bot is running 24/7!")

async def start_background_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server successfully bound to port {port}")

# --- إعدادات البوت ---
TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')

@bot.command()
async def play(ctx, *, query: str):
    if not ctx.author.voice:
        await ctx.send("❌ يجب أن تكون في روم صوتي أولاً!")
        return

    channel = ctx.author.voice.channel
    vc = ctx.voice_client if ctx.voice_client else await channel.connect()

    # تشغيل من ملف محلي موجود في المشروع لتفادي Cloudflare
    if os.path.exists(query):
        if vc.is_playing():
            vc.stop()
        try:
            vc.play(discord.FFmpegPCMAudio(query))
            await ctx.send(f"🎵 جاري تشغيل: **{query}**")
        except Exception as e:
            await ctx.send(f"❌ خطأ تشغيل: {e}")
        return

    await ctx.send("⚠️ روابط يوتيوب المباشرة محظورة من السيرفر. قم برفع ملف MP3 إلى GitHub واستخدم اسمه.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹️ تم الإيقاف.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 تم المغادرة.")

async def main():
    await start_background_web_server()
    if not TOKEN:
        print("CRITICAL: DISCORD_TOKEN is missing!")
        sys.exit(1)
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
