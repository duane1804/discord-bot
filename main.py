from discord.ext import commands, tasks
import discord
from datetime import datetime
from pytz import timezone
from googletrans import Translator
import requests
import json
import random, glob
from discord.utils import get
import yt_dlp as youtube_dl
import asyncio

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')
translator = Translator()
openai_api_key = os.environ.get('CHAT_GPT_APT_KEY')
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = ''

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['title'] if stream else ytdl.prepare_filename(data)

        return [filename, data['title']]


def chat_gpt(question):
    model = "text-davinci-003"

    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + openai_api_key},
        data=json.dumps({"model": model, "prompt": question, "temperature": 1, "max_tokens": 2000})
    )

    if response.status_code == 200:
        result = response.json()
        generated_text = result['choices'][0]['text']
        return generated_text
    else:
        return "Request failed with status code: {}".format(response.status_code)


@bot.event
async def on_ready():
    print('Bot logged in as: {0.user}'.format(bot))


badWords = ['đụ', 'đụ má']
speak_ill_kanna = ['ngu', 'đụ', 'chó', 'baka', 'aho']
praise_kanna = ['dễ thương', 'cute', 'kawai']


@bot.event
async def on_message(message):
    messageContent = message.content
    if any(word.lower() in messageContent.lower().replace(' ', '') for word in badWords):
        await message.delete()
        await message.channel.send(f'{message.author.mention}Yameroooo! この馬鹿')
        await message.channel.send(file=discord.File('images/kanna-yamero.png'))
    if message.author == bot.user:
        return
    if message.content.startswith('Kanna là gì của Duane'):
        await message.channel.send('屋根')
    if message.content.startswith('Kanna là người như thế nào'):
        await message.channel.send('地球上で一番かわいい')
    if message.content.startswith('Duane là gì của Kanna'):
        await message.channel.send('彼氏')
    if message.content.startswith('カンナちゃんは可愛いですか？'):
        await message.channel.send('カンナちゃんは一番可愛いです')
    if message.content.startswith('Ngủ ngon'):
        await message.channel.send(':sleeping:')
    if message.content.startswith('食べまそう'):
        await message.channel.send(file=discord.File('images/kanna_eat.gif'))
    if "kanna" in message.content.lower():
        if any(word.lower() in message.content.lower() for word in speak_ill_kanna):
            await message.delete()
            await message.channel.send(f'{message.author.mention} カンナちゃんを悪く言うなて下さい！')
            await message.channel.send(file=discord.File('images/kanna-yamero.png'))
        else:
            if any(word.lower() in message.content.lower() for word in praise_kanna):
                await message.reply(f'{message.author.mention} その通り!')
                await message.channel.send(file=discord.File('images/kawai_kanna.jpg'))
    await bot.process_commands(message)


@bot.command(name='join')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
        return
    else:
        channel = discord.utils.get(ctx.guild.voice_channels)
        await channel.connect()


@bot.command(name='play_song')
async def play_song(ctx, url):
    if ctx.voice_client is None:
        if not ctx.message.author.voice:
            await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
            return
        else:
            await ctx.author.voice.channel.connect()             
    server = ctx.message.guild
    voice_channel = server.voice_client
    if voice_channel.is_playing():
        voice_channel.stop() 
    async with ctx.typing():
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        voice_channel.play(discord.FFmpegOpusAudio(source=filename[0]))
    await ctx.send(f"**Now Listening Youtube Music** {filename[1]}")


@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client is None:
        await ctx.send("Bot not play anything!")
    else:
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await ctx.send("Bot paused play song!")
        else:
            await ctx.send("Bot not play anything!")


@bot.command(name='resume')
async def resume(ctx):
    if ctx.voice_client is None:
        await ctx.send("Bot not play anything!")
    else:
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            voice_client.resume()
            await ctx.send("Bot keep play song!")
        else:
            await ctx.send("Bot is not playing song!")


@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client is None:
        await ctx.send("Bot is not in any voice channel!")
    else:
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await  voice_client.disconnect()
            await ctx.send("Bot leave the voice room!")
        else:
            await ctx.send("Bot is not in any voice channel!")


@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client is None:
        await ctx.send("Bot not play anything!")
    else:
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.send("Bot stop playing song!")
        else:
            await ctx.send("Bot not play anything!")


@bot.command()
async def test(ctx, *, text):
    await ctx.send(f"Your text is: {text}")


@bot.command()
async def gpt(ctx, *, text):
    answer = chat_gpt(text)
    await ctx.send(f"Answer is: {answer}")


@bot.command()
async def translate(ctx, code1="help", code2="help", *, text=""):
    if (code1 == "help" or code2 == "help" or text == ""):
        await ctx.send(f"example: **!translate en ja I love You**")
    else:
        translated_text = translator.translate(text, src=code1, dest=code2)
        await ctx.send(f"{text} --> **{translated_text.text}**")


@bot.command()
async def image(ctx, *, string=""):
    if (string == ""):
        string = ctx.message.attachments[0]
        await ctx.send(f"{string}")
    else:
        if (ctx.message.attachments[0] != ""):
            await ctx.send(f"{ctx.message.attachments[0]}")
        await ctx.send(f"{string}")


@bot.command()
async def lucky_number(ctx, num1=0, num2=0):
    answer = random.randint(num1, num2)
    await ctx.send(f"Lucky number is: **_{answer}_**")


@bot.command()
async def ima(ctx):
    now_utc = datetime.now(timezone('UTC'))
    now_asia = now_utc.astimezone(timezone('Asia/Ho_Chi_Minh'))
    format = "%H:%M:%S %p"
    time = now_asia.strftime(format)
    time = time.replace("PM", "午後")
    time = time.replace("AM", "午前")
    await ctx.reply(f"今は: **_{time}_**")


@bot.command()
async def choose(ctx, *, string):
    data = string.split(",")
    await ctx.reply(f":game_die:|**<@{ctx.author.id}>** 私の選択は: **{data[random.randrange(len(data))]}**")


@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Not Duane",
        description="Duane Bot Potato",
        color=discord.Colour.random()
    )
    embed.set_thumbnail(url="https://i.pinimg.com/originals/42/96/c7/4296c7ac748548f7f3e4f593eaa238c1.jpg")
    embed.add_field(
        name="!ima",
        value="Get now time",
        inline=False
    )
    embed.add_field(
        name="!translate",
        value="Translate string",
        inline=False
    )
    embed.add_field(
        name="!lucky_number",
        value="Random number",
        inline=False
    )
    await ctx.send(embed=embed)


@bot.command()
async def translate_mes(ctx, code1="help", code2="help"):
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    if (code1 == "help" or code2 == "help"):
        await ctx.reply(f"example: reply the message and **!translate_mes ja en**")
    else:
        translated_text = translator.translate(message.content, src=code1, dest=code2)
        await ctx.reply(f"**{translated_text.text}**")


@bot.command()
async def kiss(ctx, member: discord.Member):
    embed = discord.Embed(
        title=" ",
        color=discord.Colour.random(),
    )
    output = ctx.message.author.name+" kisses "+member.name+"! とても可愛い!"
    embed.set_author(
        name=output,
        icon_url=ctx.message.author.avatar
    )

    dir_path = r'./images/kisses/'
    files = os.listdir(dir_path)
    image_files = [f for f in files if
                   os.path.isfile(os.path.join(dir_path, f)) and f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    random_image = random.choice(image_files)
    random_image = dir_path + random_image

    split_tup = os.path.splitext(random_image)
    file_name = "kiss"+split_tup[1]
    file = discord.File(random_image, filename=file_name)
    embed.set_image(url="attachment://"+file_name)
    await ctx.send(embed=embed, file=file)


@bot.command()
async def my_avatar(ctx):
    await ctx.reply(f"{ctx.message.author.avatar}")


@bot.command()
async def user_avatar(ctx, member: discord.Member):
    await ctx.reply(f"{member.avatar}")


@bot.command()
async def random_img(ctx):
    file_path_type = ["./images/kisses/*.png", "./images/kisses/*.jpeg", "./images/kisses/*.gif"]
    images = glob.glob(random.choice(file_path_type))
    random_image = random.choice(images)
    # await ctx.send(file=discord.File(random_image))
    split_tup = os.path.splitext(random_image)
    print(split_tup[1])


bot.run(BOT_TOKEN)
