TRAINING = False
# dont worry about this its to prevent people from pinging me every time i do maintenance
import discord, datetime
from typing import List
from jishaku.functools import executor_function
from discord.ext import commands, tasks

if not TRAINING:
    import gpt_2_simple as gpt2
import asyncio, random

RUN_NAME = "prod"

if not TRAINING:
    sess = gpt2.start_tf_sess()
    gpt2.load_gpt2(sess, run_name=RUN_NAME)  # The name of your checkpoint
    graph = gpt2.tf.compat.v1.get_default_graph()

YOURNAME = "<@ID_OF_PERSON_YOU_WANT_THE_BOT_TO_IMITATE>"
cmdqueue = 0

if TRAINING:
    print("TRAINING MODE IS ON BAYBEEE")
    activity = discord.Activity(name="model finetuning", type=discord.ActivityType.watching)
    status = discord.Status.dnd
else:
    activity = discord.Activity(name="the game", type=discord.ActivityType.watching)
    status = discord.Status.online
bot = commands.Bot(command_prefix="jazzis", activity=activity, status=status)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.event
async def on_message(message):
    if message.guild is None:
        return
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return
    randomizer = random.randint(1, 100)  # 1% chance for an unprovoked reply
    #what will provoke the bot?
    if bot.user.mention in message.content.replace('<@!', '<@') or "jb" in message.content.lower() \
            or "jazzbot" in message.content.lower() or 1 == randomizer:

        if message.author == bot.user:
            return
        elif not TRAINING:
            global cmdqueue
            if bot.is_ready:
                print('Tasks count: ', len(asyncio.Task.all_tasks()))
                cmdqueue += 1
                uses_con = False
                async with message.channel.typing():
                    if cmdqueue > 2 and 1 != randomizer:
                        await message.channel.send(f"`processing {cmdqueue} messages atm, please slow down...`")
                    if "makeconvo" in message.content:
                        print("Gen Convo")
                        uses_con = True
                        results = gpt2.generate(sess, run_name=RUN_NAME, temperature=0.4, nsamples=1, batch_size=1,
                                                prefix=message.author.name + ":\n" + message.content + "\n\n",
                                                length=350, include_prefix=True, return_as_list=True)
                        await message.channel.send("```\n" + str('=' * 20).join(results) + "\n```")
                    else:
                        print("replying")
                        final = ''
                        prefix = ""
                        last_author = ""
                        old = await message.channel.history(limit=5).flatten()
                        old.reverse()
                        for msg in old:
                            if last_author == msg.author.id:
                                prefix = prefix + msg.content + "\n"
                            else:
                                last_author = msg.author.id
                                prefix = prefix + "\n\n" + "<@" + str(msg.author.id) + ">" + ":\n" + msg.content + "\n"

                        ok = await generateMessage(prefixArg=prefix + "\n\n" + YOURNAME + ":\n")
                        for i, msg in enumerate(ok):
                            if i == 0 and len(ok) == 1:
                                if 1 == randomizer:
                                    await message.channel.send(msg)
                                else:
                                    await message.reply(msg)
                            elif i == (len(ok) - 1):
                                await asyncio.sleep(random.randint(0, 1))
                                await message.channel.send(msg)
                            else:
                                async with message.channel.typing():
                                    await message.channel.send(msg)
                                    await asyncio.sleep(random.randint(1, 3))
                        print("replied\n")
                cmdqueue -= 1
            else:
                return
        else:
            embedVar = discord.Embed(
                title='put ur title here',
                description=f'powered by gpt-2 and tensorflow 1.15...',
                color=0xc30505,
            )
            embedVar.add_field(name="CURRENTLY TRAINING", value="leave me alone...")
            await message.channel.send(embed=embedVar)

# im not sure if this task runs at all but it's here, so..
@tasks.loop(seconds=60 * 5, count=1)
async def interject():
    print("interject condition?")
    general_channel = bot.get_channel(558031640903942145)
    current_time = datetime.datetime.now()
    old = await general_channel.history(limit=20).flatten()  # don't do less than 5 for the limit arg pls
    time_diff = []  # time difference in minutes.... stored as floats? eww
    for msg in old:
        if msg.author == bot.user:
            pass  # if the bot posted in the last 20 messages, abort
        msgDate = msg.created_at
        time_diff.append(getTimeDifference(msgDate, current_time) // 60)

    # check if the time difference between latest message in specified channel is over 10 minutes
    # AND check if chat is slow (average time difference in previous 100 messages) limit 100 :  80 average
    if sum(time_diff) / len(time_diff) > 60 and getTimeDifference(old[0].created_at, current_time) // 60 > 10:
        print("interjecting...")
        final = ''
        prefix = ""
        last_author = ""
        old = old[5:]
        old.reverse()
        for msg in old:
            if last_author == msg.author.id:
                prefix = prefix + msg.content + "\n"
            else:
                last_author = msg.author.id
                prefix = prefix + "\n\n" + "<@" + str(msg.author.id) + ">" + ":\n" + msg.content + "\n"
        ok = await generateMessage(prefixArg=prefix + "\n\n" + YOURNAME + ":\n")
        async with general_channel.typing():
            for i, msg in enumerate(ok):
                if i == 0 and len(ok) == 1:
                    await general_channel.send(msg)
                elif i == (len(ok) - 1):
                    await asyncio.sleep(random.randint(0, 1))
                    await general_channel.send(msg)
                else:
                    async with general_channel.typing():
                        await general_channel.send(msg)
                        await asyncio.sleep(random.randint(1, 3))
        return
    print("the interjection condition failed...\n")


@interject.before_loop
async def before_interjection():
    await bot.wait_until_ready()


@bot.command(name='info')
async def info(ctx):
    embedVar = discord.Embed(
        title='put ur title here',
        description=f'powered by gpt-2 and tensorflow 1.15...',
        color=0xc3b1e1,
    )
    embedVar.add_field(name="please be patient because!", value="gpt-2 text generation is slow!")
    await ctx.reply(embed=embedVar)


def isEmoji(txt):
    return txt.startswith(":") and txt.endswith(":")


def hasEmoji(txt):
    return txt.count(":") % 2 == 0


# gets the time difference between datetimes in seconds
def getTimeDifference(old_time: datetime, new_time: datetime) -> float:
    return (new_time - old_time).total_seconds()


async def generateMessage(prefixArg: str, sampleSize: int = 3, temp: float = 0.9, outputLen: int = 250,
                          truncatedText: str = "\n\n", attempts: int = 3) -> List[str]:
    ok = []
    while attempts > 0:
        print("generating")
        results = gpt2.generate(sess, run_name=RUN_NAME, temperature=temp, nsamples=sampleSize, batch_size=sampleSize,
                                prefix=prefixArg, length=outputLen,
                                return_as_list=True, include_prefix=False, truncate=truncatedText)

        # TODO: REMOVE THIS AFTER FIXING DATASET
        # NEVERMIND THIS IS PROBABLY HERE TO STAY
        for r in results:
            if "@" in r:
                results.remove(r)

        print(*results, sep=" || ")
        res_split = random.choice(results).split('\n')  # choose a random result and split it by newlines
        for r in res_split:
            if (hasEmoji(r) or not r.endswith(":")) and len(r) > 0:
                ok.append(r)
        if len(ok) > 0:
            break
        print("generation failed or garbage, retrying")
        attempts -= 1
    return ok

# unused. i hate threading
@executor_function
def gpt2GenerateAsync(sess, run_name='run1', checkpoint_dir='checkpoint', model_name=None, model_dir='models',
                      sample_dir='samples', return_as_list=False, truncate=None, destination_path=None,
                      sample_delim='=' * 20 + '\n', prefix=None, seed=None, nsamples=1, batch_size=1, length=1023,
                      temperature=0.7, top_k=0, top_p=0.0, include_prefix=True):
    with graph.as_default():
        return gpt2.generate(sess, run_name, checkpoint_dir, model_name, model_dir, sample_dir, return_as_list, truncate,
                             destination_path, sample_delim, prefix, seed, nsamples, batch_size, length, temperature,
                             top_k, top_p, include_prefix)


interject.start()
bot.run('DISCORD_TOKEN_HERE')
