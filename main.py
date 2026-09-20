import asyncio
import os
import re
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import InputMediaDice

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
STRING_SESSION = os.getenv('STRING_SESSION', '')

GHOST_MODE = False
CLOCK_ON = False
GAME_MODE = os.getenv('GAME_MODE', 'on') == 'on'
GAME_BUSY = False
BASE_LAST = ''

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# ═══════════ ساعت زنده با فونت ریز ═══════════
SMALL = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹',':':'ː'}
CLOCK_RE = re.compile(r'[⁰¹²³⁴۵۶۸۹\s]+$')

def small_time():
    tz = timezone(timedelta(hours=3, minutes=30))
    return ''.join(SMALL.get(c, c) for c in datetime.now(tz).strftime('%H:%M'))

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

@client.on(events.NewMessage(pattern=r'^/status$', chats='me'))
async def status_cmd(event):
    await event.edit(f'📊 game={GAME_MODE} | ghost={GHOST_MODE} | clock={CLOCK_ON}')

@client.on(events.NewMessage(outgoing=True))
async def game_fix(event):
    global GAME_BUSY
    if not GAME_MODE or GAME_BUSY:
        return
    if not event.message.dice:
        return
    emoji = event.message.dice.emoticon or ''
    target = GAME_TARGETS.get(emoji)
    if target is None:
        return
    print(f'[GAME] dice {emoji} in chat {event.chat_id}', flush=True)
    GAME_BUSY = True
    try:
        msg = event.message
        val = msg.dice.value
        for i in range(12):
            if val == target:
                print(f'[GAME] got {val} - stop', flush=True)
                break
            try:
                await msg.delete()
                print(f'[GAME] deleted value={val}', flush=True)
            except errors.FloodWaitError as e:
                print(f'[GAME] floodwait {e.seconds}s', flush=True)
                await asyncio.sleep(e.seconds + 1)
                continue
            except Exception as e:
                print(f'[GAME] delete failed: {e}', flush=True)
                break
            await asyncio.sleep(0.1)
            try:
                msg = await client.send_file(event.chat_id, InputMediaDice(emoticon=emoji))
            except errors.FloodWaitError as e:
                print(f'[GAME] floodwait on send {e.seconds}s', flush=True)
                await asyncio.sleep(e.seconds + 1)
                continue
            await asyncio.sleep(0.25)
            cur = await client.get_messages(event.chat_id, ids=msg.id)
            val = cur.dice.value if (cur and cur.dice) else None
            print(f'[GAME] try {i}: value={val}', flush=True)
    except Exception as e:
        print(f'[GAME] error: {e}', flush=True)
    finally:
        GAME_BUSY = False

# ═══════════ دستور ساعت ═══════════
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
    await event.edit('🤖 /ping | /save | /del | /status | /ghost on|off | /clock on|off | /game on|off')

async def main():
    global BASE_LAST
    await client.start()
    me = await client.get_me()
    BASE_LAST = CLOCK_RE.sub('', me.last_name or '').strip()
    asyncio.create_task(clock_loop())
    print('🚀 سلف‌بات فعال شد!', flush=True)
    print(f'[INIT] GAME_MODE={GAME_MODE}', flush=True)
    while True:
        try:
            await client.run_until_disconnected()
            break
        except Exception as e:
            print(f'[MAIN] connection lost: {e} - reconnecting in 5s...', flush=True)
            await asyncio.sleep(5)
            try:
                if not client.is_connected():
                    await client.connect()
            except Exception as e2:
                print(f'[MAIN] reconnect failed: {e2}', flush=True)

if __name__ == '__main__':
    asyncio.run(main())
