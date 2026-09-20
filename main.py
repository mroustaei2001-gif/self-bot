import asyncio
import os
import re
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
STRING_SESSION = os.getenv('STRING_SESSION', '')

GHOST_MODE = False
CLOCK_ON = False
GAME_MODE = False
GAME_BUSY = False
BASE_LAST = ''

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# ═══════════ ساعت زنده ═══════════
SMALL = str.maketrans('0123456789:', '⁰¹²³⁴⁵⁷⁸⁹')
CLOCK_RE = re.compile(r'[\s⁰¹²³⁴⁵⁶⁷⁸⁹ː]+$')

def small_time():
    tz = timezone(timedelta(hours=3, minutes=30))
    return datetime.now(tz).strftime('%H:%M').translate(SMALL)

async def clock_loop():
    last = ''
    while True:
        try:
            if CLOCK_ON:
                t = small_time()
                if t != last:
                    await client(UpdateProfileRequest(last_name=(BASE_LAST + ' ' + t).strip()))
                    last = t
        except Exception:
            pass
        await asyncio.sleep(10)

# ═══════════ مود بازی ═══════════
GAME_TARGETS = {'🎲': 6, '🎯': 6, '🏀': 5, '⚽': 5, '🎳': 6}

@client.on(events.NewMessage(pattern=r'^/game\s+(on|off)$', chats='me'))
async def game_cmd(event):
    global GAME_MODE
    GAME_MODE = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🎮 مود بازی: {"روشن ✅" if GAME_MODE else "خاموش ❌"}')

@client.on(events.NewMessage(outgoing=True))
async def game_fix(event):
    global GAME_BUSY
    if not GAME_MODE or GAME_BUSY:
        return
    msg = event.message
    if not msg.dice:
        return
    target = GAME_TARGETS.get(msg.dice.emoji)
    if target is None:
        return
    GAME_BUSY = True
    try:
        for _ in range(20):
            if msg.dice and msg.dice.value == target:
                break
            try:
                await msg.delete()
            except Exception:
                break
            await asyncio.sleep(0.15)
            msg = await client.send_message(event.chat_id, msg.dice.emoji)
            await asyncio.sleep(0.15)
    finally:
        GAME_BUSY = False

# ═══════════ ساعت ═══════════
@client.on(events.NewMessage(pattern=r'^/clock\s+(on|off)$', chats='me'))
async def clock_cmd(event):
    global CLOCK_ON, BASE_LAST
    if event.pattern_match.group(1) == 'on':
        me = await client.get_me()
        BASE_LAST = CLOCK_RE.sub('', me.last_name or '').strip()
        CLOCK_ON = True
        await client(UpdateProfileRequest(last_name=(BASE_LAST + ' ' + small_time()).strip()))
        await event.edit('🕐 ساعت زنده روشن شد!')
    else:
        CLOCK_ON = False
        await client(UpdateProfileRequest(last_name=BASE_LAST))
        await event.edit('🕐 ساعت خاموش شد و اسم برگشت.')

# ═══════════ دستورات پایه ═══════════
@client.on(events.NewMessage(pattern=r'^/ping$', chats='me'))
async def ping(event):
    await event.edit('🏓 پونگ! سلف‌بات زنده است.')

@client.on(events.NewMessage(pattern=r'^/save$', chats='me'))
async def save(event):
    if event.is_reply:
        await event.get_reply_message().forward_to('me')
        await event.edit('✅ ذخیره شد.')

@client.on(events.NewMessage(pattern=r'^/del$', chats='me'))
async def delete(event):
    if event.is_reply:
        await event.get_reply_message().delete()
    await event.delete()

@client.on(events.NewMessage(pattern=r'^/ghost\s+(on|off)$', chats='me'))
async def ghost(event):
    global GHOST_MODE
    GHOST_MODE = (event.pattern_match.group(1) == 'on')
    await event.edit(f'👻 حالت روح: {"روشن ✅" if GHOST_MODE else "خاموش ❌"}')

@client.on(events.NewMessage())
async def ghost_reader(event):
    if GHOST_MODE and not event.out:
        try:
            await client.send_read_acknowledge(event.chat_id, max_id=event.id)
        except Exception:
            pass

@client.on(events.NewMessage(pattern=r'^/help$', chats='me'))
async def help_cmd(event):
    await event.edit('🤖 /ping | /save | /del | /ghost on|off | /clock on|off | /game on|off')

async def main():
    global BASE_LAST
    await client.start()
    me = await client.get_me()
    BASE_LAST = CLOCK_RE.sub('', me.last_name or '').strip()
    asyncio.create_task(clock_loop())
    print('🚀 سلف‌بات فعال شد!', flush=True)
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
