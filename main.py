import asyncio
import os
import re
import json
import time
import random
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import InputMediaDice

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
GEN = os.getenv('GEN', '0') == '1'
WIPE = os.getenv('WIPE', '0') == '1'
PHONE = os.getenv('PHONE', '')
CODE = os.getenv('CODE', '')
PASS2 = os.getenv('PASS', '')
SESSION_PATH = os.getenv('SESSION_PATH', '/data/sb')

GHOST_MODE = False
CLOCK_ON = False
GAME_MODE = os.getenv('GAME_MODE', 'on') == 'on'
GAME_STYLE = 'roll'
GAME_BUSY = False
BASE_LAST = ''
SEEN = set()
AUTO_ON = True
AUTOS = {}
AUTOS_PATH = '/data/autos.json'

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

SMALL = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹',':':'ː'}
CLOCK_RE = re.compile(r'[⁰¹²۳۴۵۶۷۸۹ː\s]+$')

def small_time():
    tz = timezone(timedelta(hours=3, minutes=30))
    return ''.join(SMALL.get(c, c) for c in datetime.now(tz).strftime('%H:%M'))

def load_autos():
    global AUTOS
    try:
        with open(AUTOS_PATH) as f:
            AUTOS = json.load(f)
    except Exception:
        AUTOS = {}

def save_autos():
    try:
        with open(AUTOS_PATH, 'w') as f:
            json.dump(AUTOS, f)
    except Exception:
        pass

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

async def auto_loop():
    while True:
        try:
            if AUTO_ON:
                now = time.time()
                for cid, item in list(AUTOS.items()):
                    iv = item.get('interval', 300)
                    if now - item.get('last', 0) >= iv:
                        try:
                            if item.get('mode') == 'copy':
                                src = await client.get_messages('me', ids=item['mid'])
                                if src is None:
                                    raise Exception('source message not found')
                                await client.send_message(int(cid), message=src.text, file=src.media)
                            else:
                                await client.send_message(int(cid), item['word'])
                            item['last'] = now
                            save_autos()
                            print(f'[AUTO] sent to {cid}', flush=True)
                        except errors.FloodWaitError as e:
                            print(f'[AUTO] floodwait {e.seconds}s', flush=True)
                            await asyncio.sleep(e.seconds + 1)
                        except Exception as e:
                            print(f'[AUTO] failed {cid}: {e}', flush=True)
                            del AUTOS[cid]
                            save_autos()
                            try:
                                await client.send_message('me', f'⚠️ ارسال خودکار در گروه {cid} متوقف شد (خطا: {e}). از لیست حذف شد.')
                            except Exception:
                                pass
        except Exception as e:
            print(f'[AUTO] loop error: {e}', flush=True)
        await asyncio.sleep(20)

GAME_TARGETS = {'🎲': 6, '🎯': 6, '🏀': 5, '⚽': 5, '🎳': 6}

def looks_like_id(s):
    if not s:
        return False
    if s.startswith('-') and s[1:].isdigit():
        return True
    if s.startswith('+'):
        return True
    return False

async def resolve_target(target):
    if looks_like_id(target):
        ent = await client.get_entity(int(target))
        return ent, str(ent.id)
    else:
        ent = await client.get_entity(target)
        return ent, str(ent.id)

@client.on(events.NewMessage(pattern=r'^/getid$', chats='me'))
async def getid_cmd(event):
    rmsg = await event.get_reply_message()
    
    if rmsg:
        chat_id = rmsg.chat_id
    else:
        async for dialog in client.iter_dialogs(limit=50):
            if dialog.is_group and not dialog.is_channel and dialog.id != event.chat_id:
                async for msg in client.iter_messages(dialog.id, limit=1, from_user='me'):
                    chat_id = dialog.id
                    break
                else:
                    continue
                break
        else:
            await event.edit('❌ روی پیامی از گروه ریپلی بزن یا اول در گروهی پیام بفرست.')
            return
    
    try:
        ent = await client.get_entity(chat_id)
        title = getattr(ent, 'title', None) or getattr(ent, 'first_name', None) or 'chat'
        await event.edit(f'🔢 ID گروه: `{chat_id}`\nعنوان: {title}\n\nحالا می‌توانی این ID را در دستورات /auto استفاده کنی.')
    except Exception as e:
        await event.edit(f'🔢 ID چت: `{chat_id}`\n(خطا در گرفتن عنوان: {e})')

@client.on(events.NewMessage(pattern=r'^/auto\s+(add|addc|del|list|on|off)\s*(.*)$', chats='me'))
async def auto_cmd(event):
    global AUTO_ON
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    if act == 'on':
        AUTO_ON = True
        await event.edit('⏰ ارسال خودکار: روشن ✅')
        return
    if act == 'off':
        AUTO_ON = False
        await event.edit('⏰ ارسال خودکار: خاموش ❌')
        return
    if act == 'list':
        if not AUTOS:
            await event.edit('⏰ لیست خالی است.')
            return
        lines = []
        for k, v in AUTOS.items():
            mins = v.get('interval', 300) // 60
            kind = 'کپی پیام' if v.get('mode') == 'copy' else f'«{v["word"]}»'
            lines.append(f'• {v.get("title", k)} ({k}) → هر {mins} دقیقه: {kind}')
        await event.edit('⏰ لیست ارسال خودکار:\n' + '\n'.join(lines))
        return
    if act == 'add':
        tokens = rest.split(maxsplit=2)
        if not tokens:
            await event.edit('❌ قالب: /auto add @group [دقیقه] متن\nیا: /auto add -100xxx [دقیقه] متن')
            return
        target = tokens[0]
        if len(tokens) >= 2 and tokens[1].isdigit():
            minutes = max(1, int(tokens[1]))
            word = tokens[2] if len(tokens) > 2 else ''
        else:
            minutes = 5
            word = ' '.join(tokens[1:])
        if not word:
            await event.edit('❌ قالب: /auto add @group [دقیقه] متن')
            return
        if len(AUTOS) >= 10:
            await event.edit('❌ سقف ۱۰ گروه (محافظت از اکانت).')
            return
        try:
            ent, key = await resolve_target(target)
        except Exception as e:
            await event.edit(f'❌ چت پیدا نشد: {e}')
            return
        AUTOS[key] = {'mode': 'txt', 'word': word, 'interval': minutes * 60, 'last': 0, 'title': getattr(ent, 'title', None) or getattr(ent, 'first_name', target)}
        save_autos()
        await event.edit(f'✅ هر {minutes} دقیقه «{word}» در {AUTOS[key]["title"]} ارسال می‌شود.')
        return
    if act == 'addc':
        rmsg = await event.get_reply_message()
        if not rmsg:
            await event.edit('❌ روی پیام موردنظر در Saved Messages ریپلی بزن و دوباره بفرست.')
            return
        tokens = rest.split()
        if not tokens:
            await event.edit('❌ قالب: (ریپلی) /auto addc @group [دقیقه]')
            return
        target = tokens[0]
        minutes = max(1, int(tokens[1])) if len(tokens) > 1 and tokens[1].isdigit() else 5
        if len(AUTOS) >= 10:
            await event.edit('❌ سقف ۱۰ گروه (محافظت از اکانت).')
            return
        try:
            ent, key = await resolve_target(target)
        except Exception as e:
            await event.edit(f'❌ چت پیدا نشد: {e}')
            return
        AUTOS[key] = {'mode': 'copy', 'mid': rmsg.id, 'interval': minutes * 60, 'last': 0, 'title': getattr(ent, 'title', None) or getattr(ent, 'first_name', target)}
        save_autos()
        await event.edit(f'✅ هر {minutes} دقیقه کپی پیام در {AUTOS[key]["title"]} ارسال می‌شود.')
        return
    if act == 'del':
        try:
            ent, key = await resolve_target(rest)
        except Exception:
            key = rest
        if AUTOS.pop(key, None) is not None:
            save_autos()
            await event.edit('🗑️ از لیست حذف شد.')
        else:
            await event.edit('❌ در لیست نبود.')
        return

@client.on(events.NewMessage(pattern=r'^/game\s+(on|off|roll|fwd)$', chats='me'))
async def game_cmd(event):
    global GAME_MODE, GAME_STYLE
    m = event.pattern_match.group(1)
    if m == 'off':
        GAME_MODE = False
        await event.edit('🎮 مود بازی: خاموش ❌')
        return
    GAME_MODE = True
    GAME_STYLE = 'fwd' if m == 'fwd' else 'roll'
    await event.edit(f'🎮 مود بازی: روشن ✅ (حالت: {"فورواردی" if GAME_STYLE == "fwd" else "پرتاب انسانی"})')

@client.on(events.NewMessage(pattern=r'^/status$', chats='me'))
async def status_cmd(event):
    await event.edit(f'📊 game={GAME_MODE}({GAME_STYLE}) | ghost={GHOST_MODE} | clock={CLOCK_ON} | auto={AUTO_ON}({len(AUTOS)})')

@client.on(events.NewMessage(outgoing=True))
async def game_fix(event):
    global GAME_BUSY
    if not GAME_MODE or GAME_BUSY:
        return
    if event.message.id in SEEN:
        return
    if not event.message.dice:
        return
    emoji = event.message.dice.emoticon or ''
    target = GAME_TARGETS.get(emoji)
    if target is None:
        return
    print(f'[GAME] dice {emoji} in chat {event.chat_id} - style={GAME_STYLE}', flush=True)
    GAME_BUSY = True
    preroll = []
    try:
        if GAME_STYLE == 'roll':
            msg = event.message
            SEEN.add(msg.id)
            val = msg.dice.value
            for i in range(14):
                if val == target:
                    print(f'[GAME] got {val} - stop', flush=True)
                    break
                await asyncio.sleep(0.45)
                try:
                    await msg.delete()
                    print(f'[GAME] deleted value={val}', flush=True)
                except Exception as e:
                    print(f'[GAME] delete failed: {e}', flush=True)
                    break
                await asyncio.sleep(random.uniform(0.9, 1.6))
                msg = await client.send_file(event.chat_id, InputMediaDice(emoticon=emoji))
                SEEN.add(msg.id)
                val = msg.dice.value
                print(f'[GAME] try {i}: value={val}', flush=True)
        else:
            try:
                await event.message.delete()
            except Exception as e:
                print(f'[GAME] delete failed: {e}', flush=True)
                return
            win = None
            for i in range(30):
                m = await client.send_file('me', InputMediaDice(emoticon=emoji))
                preroll.append(m.id)
                if m.dice and m.dice.value == target:
                    win = m
                    break
                await asyncio.sleep(0.05)
            if win is None:
                win = m
            try:
                fwd = await client.forward_messages(event.chat_id, win.id, 'me', drop_author=True)
            except Exception:
                fwd = await client.forward_messages(event.chat_id, win.id, 'me')
            SEEN.add(fwd.id)
            print('[GAME] forwarded winner', flush=True)
    except Exception as e:
        print(f'[GAME] error: {e}', flush=True)
    finally:
        GAME_BUSY = False
        for mid in preroll:
            try:
                await client.delete_messages('me', mid)
            except Exception:
                pass
        if len(SEEN) > 500:
            SEEN.clear()

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
    await event.edit('🤖 /ping | /save | /del | /getid | /status | /ghost on|off | /clock on|off | /game on|roll|fwd|off | /auto add|addc|del|list|on|off')

async def gen_mode():
    await client.connect()
    if await client.is_user_authorized():
        print('[GEN] already authorized! GEN=0 بگذار و دیپلوی کن.', flush=True)
        await client.disconnect()
        return
    if not CODE:
        r = await client.send_code_request(PHONE)
        with open(SESSION_PATH + '.hash', 'w') as f:
            f.write(r.phone_code_hash)
        print('[GEN] CODE SENT to', PHONE, flush=True)
    else:
        with open(SESSION_PATH + '.hash') as f:
            h = f.read().strip()
        try:
            await client.sign_in(PHONE, CODE, phone_code_hash=h)
        except errors.SessionPasswordNeededError:
            print('[GEN] 2FA required - submitting password...', flush=True)
            await client.sign_in(password=PASS2)
        print('[GEN] AUTHORIZED! حالا GEN=0 بگذار و دیپلوی کن.', flush=True)
    await client.disconnect()

async def main():
    global BASE_LAST
    if WIPE:
        for p in (SESSION_PATH + '.session', SESSION_PATH + '.hash'):
            try:
                os.remove(p)
                print('[WIPE] removed', p, flush=True)
            except Exception:
                pass
    if GEN:
        await gen_mode()
        return
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print('[FATAL] لاگین نیست! GEN=1 بگذار و دیپلوی کن.', flush=True)
            return
    except errors.AuthKeyDuplicatedError:
        print('[FATAL] کلید سوخته! WIPE=1 بگذار و دیپلوی کن، بعد GEN=1.', flush=True)
        return
    load_autos()
    me = await client.get_me()
    BASE_LAST = CLOCK_RE.sub('', me.last_name or '').strip()
    asyncio.create_task(clock_loop())
    asyncio.create_task(auto_loop())
    print('🚀 سلف‌بات فعال شد!', flush=True)
    print(f'[INIT] GAME_MODE={GAME_MODE} STYLE={GAME_STYLE} AUTOS={len(AUTOS)}', flush=True)
    while True:
        try:
            await client.run_until_disconnected()
            break
        except errors.AuthKeyDuplicatedError:
            print('[FATAL] کلید سوخته! WIPE=1 و بعد GEN=1.', flush=True)
            return
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
