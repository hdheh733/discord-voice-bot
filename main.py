import discord
from discord.ext import commands
import os

# إعداد الصلاحيات
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='--', intents=intents)
@bot.event
async def on_ready():
    print(f'تم تسجيل الدخول بنجاح باسم: {bot.user}')

@bot.command()
async def play(ctx):
    # التأكد من أن المستخدم داخل روم صوتي
    if not ctx.author.voice:
        await ctx.send("لازم تكون داخل روم صوتي أولاً!")
        return

    # التأكد من وجود ملف MP3 مرفق مع الرسالة
    if not ctx.message.attachments:
        await ctx.send("يرجى إرفاق ملف MP3 مع الأمر! (مثال: ارسل الملف واكتب في الوصف !play)")
        return

    attachment = ctx.message.attachments[0]
    
    # التأكد من أن الملف بصيغة mp3
    if not attachment.filename.endswith('.mp3'):
        await ctx.send("الملف يجب أن يكون بصيغة .mp3 فقط!")
        return

    # حفظ الملف مؤقتاً
    file_path = f"./{attachment.filename}"
    await attachment.save(file_path)

    # الاتصال بالروم الصوتي
    voice_channel = ctx.author.voice.channel
    vc = ctx.voice_client

    if not vc:
        vc = await voice_channel.connect()
    elif vc.channel != voice_channel:
        await vc.move_to(voice_channel)

    # تشغيل الصوت
    def after_playing(error):
        if os.path.exists(file_path):
            os.remove(file_path) # حذف الملف بعد الانتهاء للحفاظ على المساحة

    audio_source = discord.FFmpegPCMAudio(file_path)
    
    if not vc.is_playing():
        vc.play(audio_source, after=after_playing)
        await ctx.send(f"جاري تشغيل: **{attachment.filename}** 🎶")
    else:
        await ctx.send("البوت يشغل صوت حالياً، انتظر لين يخلص أو اكتب أمر الخروج.")

# أمر إخراج البوت من الروم
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("تم الخروج من الروم الصوتي 👋")
    else:
        await ctx.send("أنا مو موجود في أي روم صوتي أساساً!")

# ضع التوكن الخاص بك هنا
import os

bot.run(os.getenv("DISCORD_TOKEN"))