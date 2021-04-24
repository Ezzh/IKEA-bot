from discord.ext import commands
import asyncio


async def command(text):
    global bot
    await bot.wait_until_ready()
    print(text)
    channel = bot.get_channel(id=805795867125874698)
    await channel.send(text)

bot = commands.Bot(command_prefix='*')

bot.run("ODA1Nzg4MzQ1ODc5MTAxNDgw.YBf-4A.PzjxDiol8Pa_tWu_MO_t98cJURs")
bot.loop.create_task(command('lfff'))
bot.close()
bot.run("ODA1Nzg4MzQ1ODc5MTAxNDgw.YBf-4A.PzjxDiol8Pa_tWu_MO_t98cJURs")
