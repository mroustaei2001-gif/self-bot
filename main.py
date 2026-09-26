import asyncio
import os
import re
import json
import time
import random
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors, types
from telethon.utils import get_peer_id
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import (InputMediaDice, ChannelParticipantsAdmins,
                               ChannelParticipantCreator, ChatParticipantCreator)
from telethon.tl.custom import Button

BOT_VERSION = '9'

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
GAME_MODE = os.getenv('GAME_MODE', 'off') == 'on'
GAME_STYLE = 'roll'
GAME_BUSY = False
BASE_LAST = ''
SEEN = set()
ME_ID = None
TTL_SAVE = True
BAN_LOG = True
BAN_DEDUPE = {}
WATCH = set()
WATCH_PATH = '/data/watch.json'
LAST_SEEN = {}
AUTO_ON = True
AUTOS = {}
AUTOS_PATH = '/data/autos.json'
CLICK_ON = True
CLICKS = {}
CLICKS_PATH = '/data/clicks.json'
OWNERS = {}
OWNERS_PATH = '/data/owners.json'
TRIED_OWNERS = set()
SPAM_LOCK = False

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

FONTS = [
    {'d': '⁰¹²³⁴⁵⁶⁷⁹', 'c': 'ː'},
    {'d': '₀₁₂₃₄₅₆₇₈₉', 'c': 'ː'},
    {'d': '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿', 'c': ':'},
    {'d': '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡', 'c': ':'},
    {'d': '𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵', 'c': ':'},
    {'d': '⓪①③④⑤⑥⑦⑧⑨', 'c': ':'},
    {'d': '⓿❶❷❸❹❺❻❼❽❾', 'c': ':'},
    {'d': '۰۱۲۳۴۵۶۷۸۹', 'c': ':'},
    {'d': '٠١٢٣٤٥٦٧٨٩', 'c': ':'},
    {'d': '０１２３４５６７８９', 'c': ':'},
]
_ALLC = ''.join(f['d'] for f in FONTS) + ''.join(f['c'] for f in FONTS)
CLOCK_RE = re.compile('[' + re.escape(_ALLC) + r'\s]+$')

def small_time():
    tz = timezone(timedelta(hours=3, minutes=30))
    now = datetime.now(tz)
    f = FONTS[now.hour % len(FONTS)]
    if len(f['d']) != 10:
        return now.strftime('%H:%M')
    table = {ord(d): s for d, s in zip('0123456789', f['d'])}
    table[ord(':')] = f['c']
    return now.strftime('%H:%M').translate(table)

def fa_now():
    tz = timezone(timedelta(hours=3, minutes=30))
    return datetime.now(tz).strftime('%Y/%m/%d %H:%M')

def load_autos():
    global AUTOS
    try:
        with open(AUTOS_PATH) as f:
            AUTOS = json.load(f)
    except Exception:
        AUTOS = {}
    for k, v in list(AUTOS.items()):
        if 'chat' not in v:
            v['chat'] = k

def save_autos():
    try:
        with open(AUTOS_PATH, 'w') as f:
            json.dump(AUTOS, f)
    except Exception:
        pass

def load_clicks():
    global CLICKS
    try:
        with open(CLICKS_PATH) as f:
            CLICKS = json.load(f)
    except Exception:
        CLICKS = {}

def save_clicks():
    try:
        with open(CLICKS_PATH, 'w') as f:
            json.dump(CLICKS, f)
    except Exception:
        pass

def load_owners():
    global OWNERS
    try:
        with open(OWNERS_PATH) as f:
            OWNERS = json.load(f)
    except Exception:
        OWNERS = {}

def save_owners():
    try:
        with open(OWNERS_PATH, 'w') as f:
            json.dump(OWNERS, f)
    except Exception:
        pass

def load_watch():
    global WATCH
    try:
        with open(WATCH_PATH) as f:
            WATCH = set(json.load(f))
    except Exception:
        WATCH = set()

def save_watch():
    try:
        with open(WATCH_PATH, 'w') as f:
            json.dump(list(WATCH), f)
    except Exception:
        pass

def next_key(d):
    nums = [int(k) for k in d.keys() if k.isdigit()]
    return str((max(nums) + 1) if nums else 1)

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

async def probe_loop():
    while True:
        await asyncio.sleep(120)
        if ME_ID is None:
            continue
        for cid in list(WATCH):
            if cid == ME_ID:
                WATCH.discard(cid)
                continue
            try:
                res = await client.get_participant(cid, 'me')
                part = getattr(res, 'participant', res)
                if isinstance(part, types.ChannelParticipantBanned):
                    kicked = getattr(part, 'kicked_by', None)
                    print(f'[BAN] probe banned in {cid} by {kicked}', flush=True)
                    await log_ban(cid, kicked, None)
                    WATCH.discard(cid)
                    save_watch()
            except (errors.UserNotParticipantError, errors.ChannelPrivateError, errors.ChatPrivateError) as e:
                last = LAST_SEEN.get(cid, 0)
                if last > 0 and time.time() - last < 12 * 3600:
                    print(f'[BAN] probe lost access in {cid} ({type(e).__name__}) - logging', flush=True)
                    await log_ban(cid, None, None)
                WATCH.discard(cid)
                save_watch()
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception as e:
                print(f'[BAN] probe error {cid}: {type(e).__name__}: {e}', flush=True)
            await asyncio.sleep(0.3)

async def auto_loop():
    while True:
        try:
            if AUTO_ON:
                now = time.time()
                for key, item in list(AUTOS.items()):
                    cid = item.get('chat', key)
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
                        except (errors.UserBannedInChannelError, errors.ChatWriteForbiddenError) as e:
                            print(f'[AUTO] banned in {cid}: {e}', flush=True)
                            del AUTOS[key]
                            save_autos()
                            try:
                                await log_ban(int(cid), None, None)
                            except Exception:
                                pass
                        except errors.FloodWaitError as e:
                            await asyncio.sleep(e.seconds + 1)
                        except Exception as e:
                            print(f'[AUTO] failed {key}: {e}', flush=True)
                            del AUTOS[key]
                            save_autos()
                            try:
                                await client.send_message('me', f'⚠️ ردیف {key} در گروه {cid} متوقف شد.')
                            except Exception:
                                pass
        except Exception as e:
            print(f'[AUTO] loop error: {e}', flush=True)
        await asyncio.sleep(20)

GAME_TARGETS = {'🎲': 6, '🎯': 6, '🏀': 5, '⚽': 5, '🎳': 6}

def looks_like_id(s):
    return bool(s) and s.startswith('-') and s[1:].isdigit()

async def resolve_target(target):
    if looks_like_id(target):
        ent = await client.get_entity(int(target))
    else:
        ent = await client.get_entity(target)
    return ent, str(ent.id)

async def cache_owner(cid):
    if str(cid) in OWNERS:
        return
    ent = await client.get_entity(cid)
    title = getattr(ent, 'title', None) or getattr(ent, 'first_name', None) or str(cid)
    owner_id = None
    try:
        if getattr(ent, 'channel', False) or getattr(ent, 'megagroup', False) or getattr(ent, 'broadcast', False):
            res = await client(GetParticipantsRequest(ent, ChannelParticipantsAdmins(), 0, 100, 0))
            for p in res.participants:
                if isinstance(p, ChannelParticipantCreator):
                    owner_id = p.user_id
                    break
        else:
            full = await client(GetFullChatRequest(cid))
            for p in full.full_chat.participants.participants:
                if isinstance(p, ChatParticipantCreator):
                    owner_id = p.user_id
                    break
    except Exception:
        pass
    if owner_id:
        try:
            u = await client.get_entity(owner_id)
            OWNERS[str(cid)] = {
                'owner_id': owner_id,
                'owner_name': ((getattr(u, 'first_name', '') or '') + ' ' + (getattr(u, 'last_name', '') or '')).strip(),
                'owner_username': getattr(u, 'username', None),
                'title': title,
            }
            save_owners()
        except Exception:
            pass

@client.on(events.NewMessage(incoming=True))
async def owner_cacher(event):
    cid = event.chat_id
    if cid != ME_ID:
        WATCH.add(cid)
        save_watch()
        LAST_SEEN[cid] = time.time()
    if cid in TRIED_OWNERS or str(cid) in OWNERS:
        return
    TRIED_OWNERS.add(cid)
    try:
        await cache_owner(cid)
    except Exception:
        pass

@client.on(events.NewMessage(outgoing=True))
async def watch_outgoing(event):
    cid = event.chat_id
    if cid != ME_ID:
        WATCH.add(cid)
        save_watch()
        LAST_SEEN[cid] = time.time()

async def log_ban(chat_id, admin_id, chat_title=None):
    if not BAN_LOG:
        return
    key = str(chat_id)
    now = time.time()
    if now - BAN_DEDUPE.get(key, 0) < 120:
        return
    BAN_DEDUPE[key] = now
    try:
        admin = await client.get_entity(admin_id) if admin_id else None
    except Exception:
        admin = None
    try:
        if chat_title is None:
            chat = await client.get_entity(int(chat_id))
            chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', str(chat_id))
    except Exception:
        chat_title = str(chat_id)
    own = OWNERS.get(str(chat_id))
    lines = [f'🚨 **بن/حذف شدی در:** {chat_title}']
    if admin is None:
        lines.append('👤 **بن‌کننده:**  ناشناس/نامشخص')
    else:
        fn = getattr(admin, 'first_name', '') or ''
        ln = getattr(admin, 'last_name', '') or ''
        lines.append(f' **بن‌کننده:** {(fn + " " + ln).strip() or "بدون نام"}')
        lines.append(f'🆔 **ID بن‌کننده:** `{admin.id}`')
        if getattr(admin, 'username', None):
            lines.append(f'🔗 **Username بن‌کننده:** @{admin.username}')
    if own:
        lines.append(f'👑 **مالک/سازنده:** {own["owner_name"] or "بدون نام"}')
        lines.append(f' **ID مالک:** `{own["owner_id"]}`')
        if own.get('owner_username'):
            lines.append(f'🔗 **Username مالک:** @{own["owner_username"]}')
    else:
        lines.append('👑 **مالک:** (کش نشده بود / دسترسی نبود)')
    lines.append(f'⏰ **زمان:** {fa_now()}')
    rows = []
    if admin is not None and getattr(admin, 'username', None):
        rows.append([Button.url('📩 PV بن‌کننده', f'https://t.me/{admin.username}')])
    elif admin is not None:
        rows.append([Button.url('📩 PV بن‌کننده', f'tg://user?id={admin.id}')])
    if own and own.get('owner_username'):
        rows.append([Button.url('👑 PV مالک', f'https://t.me/{own["owner_username"]}')])
    elif own:
        rows.append([Button.url('👑 PV مالک', f'tg://user?id={own["owner_id"]}')])
    try:
        await client.send_message('me', '\n'.join(lines), buttons=rows or None, parse_mode='md')
    except Exception as e:
        print(f'[BAN] log error: {e}', flush=True)

@client.on(events.Raw(types.UpdateChannelParticipant))
async def raw_ban_detector(event):
    if ME_ID is None:
        return
    try:
        if event.user_id != ME_ID:
            return
        np = event.new_participant
        banned = isinstance(np, types.ChannelParticipantBanned)
        left = isinstance(np, types.ChannelParticipantLeft)
        if not (banned or left):
            return
        if banned:
            br = getattr(np, 'banned_rights', None)
            if br is None or not br.view_messages:
                return
        cid = get_peer_id(types.PeerChannel(event.channel_id))
        actor = getattr(event, 'actor_id', None)
        await log_ban(cid, actor, None)
        print(f'[BAN] raw detected in {cid}', flush=True)
    except Exception as e:
        print(f'[BAN] raw detector error: {e}', flush=True)

@client.on(events.ChatAction())
async def ban_detector(event):
    if ME_ID is None:
        return
    try:
        users = await event.get_users() or []
        if not any(u.id == ME_ID for u in users if u):
            return
        if event.user_joined or event.user_added:
            return
        try:
            creator = await event.get_input_user()
            admin_id = getattr(creator, 'user_id', None) if creator else None
        except Exception:
            admin_id = None
        try:
            await cache_owner(event.chat_id)
        except Exception:
            pass
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', str(event.chat_id))
        except Exception:
            chat_title = None
        await log_ban(event.chat_id, admin_id, chat_title)
        print(f'[BAN] detected in {event.chat_id}', flush=True)
    except Exception as e:
        print(f'[BAN] detector error: {e}', flush=True)

@client.on(events.NewMessage(pattern=r'^/banlog\s+(on|off)$', chats='me'))
async def banlog_cmd(event):
    global BAN_LOG
    BAN_LOG = (event.pattern_match.group(1) == 'on')
    await event.edit(f' گزارش بن: {"روشن ✅" if BAN_LOG else "خاموش ❌"}')

@client.on(events.NewMessage(pattern=r'^/spamcheck$', chats='me'))
async def spamcheck_cmd(event):
    global SPAM_LOCK
    if SPAM_LOCK:
        await event.edit('⏳ یک بررسی دیگر در جریان است؛ چند ثانیه صبر کن.')
        return
    SPAM_LOCK = True
    await event.edit('🔍 در حال پرس‌وجو از @SpamBot...')
    try:
        await client.send_message('SpamBot', '/start')
        await asyncio.sleep(4)
        msgs = await client.get_messages('SpamBot', limit=4)
        texts = [m.text for m in msgs if m.text and not m.out]
        if texts:
            await event.edit('📊 **گزارش وضعیت اکانت:**\n\n' + texts[0], parse_mode='md')
        else:
            await event.edit('❌ پاسخی از SpamBot نیامد؛ دوباره تلاش کن.')
    except Exception as e:
        await event.edit(f'❌ خطا: {e}')
    finally:
        SPAM_LOCK = False

@client.on(events.NewMessage(incoming=True))
async def ttl_saver(event):
    if not TTL_SAVE:
        return
    try:
        med = event.message.media
        if med is None:
            return
        ttl = getattr(med, 'ttl_seconds', None)
        if not ttl:
            return
        sender = await event.get_sender()
        name = ((getattr(sender, 'first_name', '') or '') + ' ' + (getattr(sender, 'last_name', '') or '')).strip()
        path = await event.download_media()
        if path:
            await client.send_file('me', path, caption=f'⏳ رسانه نابودشونده ذخیره‌شده از: {name or "ناشناس"}')
            try:
                os.remove(path)
            except Exception:
                pass
    except Exception as e:
        print(f'[TTL] error: {e}', flush=True)

@client.on(events.NewMessage(pattern=r'^/ttl\s+(on|off)$', chats='me'))
async def ttl_cmd(event):
    global TTL_SAVE
    TTL_SAVE = (event.pattern_match.group(1) == 'on')
    await event.edit(f'⏳ ذخیره خودکار مدیای نابودشونده: {"روشن ✅" if TTL_SAVE else "خاموش ❌"}')

@client.on(events.NewMessage(incoming=True))
async def click_watcher(event):
    if not CLICK_ON or not CLICKS:
        return
    try:
        if not event.message.buttons:
            return
        cid = str(event.chat_id)
        print(f'[CLICK] checking buttons in {cid}', flush=True)
        for key, rule in list(CLICKS.items()):
            if rule.get('chat') == cid:
                for row in event.message.buttons:
                    for btn in row:
                        btn_text = btn.text or ''
                        print(f'[CLICK] checking "{btn_text}" vs "{rule["text"]}"', flush=True)
                        if rule['text'] in btn_text:
                            try:
                                await btn.click()
                                print(f'[CLICK] clicked "{rule["text"]}" in {cid}', flush=True)
                            except Exception as e:
                                print(f'[CLICK] failed: {e}', flush=True)
                            return
    except Exception as e:
        print(f'[CLICK] error: {e}', flush=True)

@client.on(events.NewMessage(incoming=True))
async def ghost_mirror(event):
    if not GHOST_MODE:
        return
    if not event.is_private:
        return
    if ME_ID is not None and event.chat_id == ME_ID:
        return
    try:
        sender = await event.get_sender()
        name = ((getattr(sender, 'first_name', '') or '') + ' ' + (getattr(sender, 'last_name', '') or '')).strip()
        header = f'👻 پیام جدید از: {name or "ناشناس"}'
        if event.media:
            path = await event.download_media()
            await client.send_file('me', path, caption=f'{header}\n{event.text or ""}'.strip())
            try:
                os.remove(path)
            except Exception:
                pass
        else:
            await client.send_message('me', f'{header}\n{event.text or ""}'.strip())
    except Exception as e:
        print(f'[MIRROR] error: {e}', flush=True)

@client.on(events.NewMessage(pattern=r'^/click\s+(add|del|list|on|off|clear)\s*(.*)$', chats='me'))
async def click_cmd(event):
    global CLICK_ON
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    if act == 'on':
        CLICK_ON = True
        await event.edit('🖱️ کلیک خودکار: روشن ✅')
        return
    if act == 'off':
        CLICK_ON = False
        await event.edit('🖱️ کلیک خودکار: خاموش ❌')
        return
    if act == 'clear':
        n = len(CLICKS)
        CLICKS.clear()
        save_clicks()
        await event.edit(f'🧹 لیست کلیک پاک شد ({n} مورد).')
        return
    if act == 'list':
        if not CLICKS:
            await event.edit('️ لیست کلیک خالی است.')
            return
        lines = [f'{k}) {v.get("title", v["chat"])} → دکمه «{v["text"]}»' for k, v in CLICKS.items()]
        await event.edit('🖱️ لیست کلیک خودکار:\n' + '\n'.join(lines))
        return
    if act == 'add':
        tokens = rest.split(maxsplit=1)
        if len(tokens) < 2:
            await event.edit('❌ قالب: /click add @group متن_دکمه')
            return
        target, btext = tokens
        try:
            ent, cid = await resolve_target(target)
        except Exception as e:
            await event.edit(f'❌ چت پیدا نشد: {e}')
            return
        key = next_key(CLICKS)
        CLICKS[key] = {'chat': cid, 'text': btext, 'title': getattr(ent, 'title', None) or getattr(ent, 'first_name', target)}
        save_clicks()
        await event.edit(f'🖱️ دکمه‌های «{btext}» در {CLICKS[key]["title"]} خودکار کلیک می‌شوند.')
        return
    if act == 'del':
        if CLICKS.pop(rest, None) is not None:
            save_clicks()
            await event.edit('🗑️ از لیست کلیک حذف شد.')
        else:
            await event.edit('❌ شماره ردیف درست نیست.')
        return

@client.on(events.NewMessage(pattern=r'^/dl\s*(.*)$', chats='me'))
async def dl_cmd(event):
    arg = (event.pattern_match.group(1) or '').strip()
    msg = None
    if arg:
        m = re.search(r'(?:t|telegram)\.me/(?:c/(\d+)/(\d+)|([^/?#]+)/(\d+))', arg)
        if not m:
            await event.edit('❌ لینک معتبر نیست.\nمثال: /dl https://t.me/c/1234567890/1234')
            return
        if m.group(1):
            chat = int('-100' + m.group(1))
        else:
            chat = m.group(3)
        mid = int(m.group(2) or m.group(4))
        try:
            msg = await client.get_messages(chat, ids=mid)
        except Exception as e:
            await event.edit(f' خطا در خواندن پیام: {e}')
            return
    else:
        msg = await event.get_reply_message()
    if msg is None:
        await event.edit('❌ پیام پیدا نشد.')
        return
    if not msg.media:
        await event.edit('❌ پیام حاوی رسانه نیست.')
        return
    await event.edit('⬇️ در حال دانلود...')
    try:
        path = await msg.download_media()
        await client.send_file('me', path, caption=msg.text or '')
        await event.delete()
        try:
            os.remove(path)
        except Exception:
            pass
    except Exception as e:
        await event.edit(f'❌ خطا: {e}')

@client.on(events.NewMessage(pattern=r'^/dlast\s+(\S+)(?:\s+(\d+))?$', chats='me'))
async def dlast_cmd(event):
    target = event.pattern_match.group(1)
    count = min(int(event.pattern_match.group(2) or 1), 10)
    await event.edit(f'⬇️ در حال دانلود {count} رسانه اخیر...')
    try:
        ent = await client.get_entity(int(target) if looks_like_id(target) else target)
    except Exception as e:
        await event.edit(f'❌ چت پیدا نشد: {e}')
        return
    n = 0
    try:
        async for m in client.iter_messages(ent, limit=100):
            if m.media:
                try:
                    path = await m.download_media()
                    await client.send_file('me', path, caption=m.text or '')
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                    n += 1
                except Exception:
                    pass
                if n >= count:
                    break
    except Exception as e:
        await event.edit(f'❌ خطا: {e}')
        return
    await event.edit(f'✅ {n} رسانه در Saved Messages ذخیره شد.')

@client.on(events.NewMessage(pattern=r'^/getmsg\s+(\S+)\s+(\d+)$', chats='me'))
async def getmsg_cmd(event):
    chat_id = event.pattern_match.group(1)
    msg_id = int(event.pattern_match.group(2))
    await event.edit('⬇️ در حال دریافت...')
    try:
        target = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
        msg = await client.get_messages(target, ids=msg_id)
        if msg is None:
            await event.edit('❌ پیام پیدا نشد.')
            return
        if msg.media:
            path = await msg.download_media()
            await client.send_file('me', path, caption=msg.text or f'📥 از {chat_id}/{msg_id}')
            try:
                os.remove(path)
            except Exception:
                pass
        else:
            await client.send_message('me', msg.text or '(پیام خالی)')
        await event.delete()
    except Exception as e:
        await event.edit(f'❌ خطا: {e}')

@client.on(events.NewMessage(pattern=r'^/auto\s+(add|addc|del|list|on|off|clear)\s*(.*)$', chats='me'))
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
        await event.edit(' ارسال خودکار: خاموش ❌')
        return
    if act == 'clear':
        n = len(AUTOS)
        AUTOS.clear()
        save_autos()
        await event.edit(f'🧹 کل لیست پاک شد ({n} ردیف).')
        return
    if act == 'list':
        if not AUTOS:
            await event.edit('⏰ لیست خالی است.')
            return
        lines = []
        for k, v in AUTOS.items():
            mins = v.get('interval', 300) // 60
            kind = 'کپی پیام' if v.get('mode') == 'copy' else f'«{v["word"]}»'
            lines.append(f'{k}) {v.get("title", v.get("chat", k))} → هر {mins} دقیقه: {kind}')
        await event.edit(' لیست ارسال خودکار:\n' + '\n'.join(lines))
        return
    if act == 'add':
        tokens = rest.split(maxsplit=2)
        if not tokens:
            await event.edit('❌ قالب: /auto add @group [دقیقه] متن')
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
        if len(AUTOS) >= 30:
            await event.edit('❌ سقف ۳۰ ردیف.')
            return
        try:
            ent, cid = await resolve_target(target)
        except Exception as e:
            await event.edit(f'❌ چت پیدا نشد: {e}')
            return
        key = next_key(AUTOS)
        AUTOS[key] = {'chat': cid, 'mode': 'txt', 'word': word, 'interval': minutes * 60, 'last': 0, 'title': getattr(ent, 'title', None) or getattr(ent, 'first_name', target)}
        save_autos()
        await event.edit(f'✅ ردیف {key}: هر {minutes} دقیقه «{word}» در {AUTOS[key]["title"]}.')
        return
    if act == 'addc':
        rmsg = await event.get_reply_message()
        if not rmsg:
            await event.edit('❌ روی پیام موردنظر در Saved Messages ریپلی بزن.')
            return
        tokens = rest.split()
        if not tokens:
            await event.edit('❌ قالب: (ریپلی) /auto addc @group [دقیقه]')
            return
        target = tokens[0]
        minutes = max(1, int(tokens[1])) if len(tokens) > 1 and tokens[1].isdigit() else 5
        if len(AUTOS) >= 30:
            await event.edit(' سقف ۳۰ ردیف.')
            return
        try:
            ent, cid = await resolve_target(target)
        except Exception as e:
            await event.edit(f'❌ چت پیدا نشد: {e}')
            return
        key = next_key(AUTOS)
        AUTOS[key] = {'chat': cid, 'mode': 'copy', 'mid': rmsg.id, 'interval': minutes * 60, 'last': 0, 'title': getattr(ent, 'title', None) or getattr(ent, 'first_name', target)}
        save_autos()
        await event.edit(f'✅ ردیف {key}: هر {minutes} دقیقه کپی پیام در {AUTOS[key]["title"]}.')
        return
    if act == 'del':
        if rest.isdigit() and rest in AUTOS:
            del AUTOS[rest]
            save_autos()
            await event.edit(f'🗑️ ردیف {rest} حذف شد.')
            return
        try:
            ent, cid = await resolve_target(rest)
            removed = [k for k, v in AUTOS.items() if v.get('chat') == cid]
            for k in removed:
                del AUTOS[k]
            if removed:
                save_autos()
                await event.edit(f'🗑️ {len(removed)} ردیف مربوط به آن گروه حذف شد.')
            else:
                await event.edit('❌ در لیست نبود.')
        except Exception:
            await event.edit('❌ شماره ردیف یا آدرس درست نیست.')
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
    await event.edit(f'📊 v{BOT_VERSION} | game={GAME_MODE}({GAME_STYLE}) | ghost={GHOST_MODE} | clock={CLOCK_ON} | ttl={TTL_SAVE} | banlog={BAN_LOG} | watch={len(WATCH)} | auto={AUTO_ON}({len(AUTOS)}) | click={CLICK_ON}({len(CLICKS)})')

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
    GAME_BUSY = True
    preroll = []
    try:
        if GAME_STYLE == 'roll':
            msg = event.message
            SEEN.add(msg.id)
            val = msg.dice.value
            for i in range(14):
                if val == target:
                    break
                await asyncio.sleep(0.45)
                try:
                    await msg.delete()
                except Exception:
                    break
                await asyncio.sleep(random.uniform(0.9, 1.6))
                msg = await client.send_file(event.chat_id, InputMediaDice(emoticon=emoji))
                SEEN.add(msg.id)
                val = msg.dice.value
        else:
            try:
                await event.message.delete()
            except Exception:
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
        await event.edit(f'🕐 ساعت زنده روشن شد!\nنمونه الان: {small_time()}')
    else:
        CLOCK_ON = False
        await client(UpdateProfileRequest(last_name=BASE_LAST))
        await event.edit(' ساعت خاموش شد و اسم برگشت.')

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
    if GHOST_MODE:
        await event.edit('👻 حالت روح: روشن ✅\n• تیک دوم نمی‌خوری\n• پیام‌های خصوصی در Saved آینه می‌شوند\n• چت اصلی را باز نکن!')
    else:
        await event.edit('👻 حالت روح: خاموش ❌')

@client.on(events.NewMessage(pattern=r'^/help$', chats='me'))
async def help_cmd(event):
    await event.edit('🤖 /ping | /save | /spamcheck | /ttl on|off | /banlog on|off | /dl لینک | /dlast @ch [n] | /getmsg id msgid | /del | /status | /ghost on|off | /clock on|off | /game on|roll|fwd|off | /auto add|addc|del|clear|list|on|off | /click add|del|clear|list|on|off')

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
    global BASE_LAST, ME_ID
    if WIPE:
        for p in (SESSION_PATH + '.session', SESSION_PATH + '.hash'):
            try:
                os.remove(p)
                print('[WIPE] removed', p, flush=True)
            except Exception:
                pass
    _original_ack = client.send_read_acknowledge
    async def _ghost_ack(*args, **kwargs):
        if GHOST_MODE:
            return None
        return await _original_ack(*args, **kwargs)
    client.send_read_acknowledge = _ghost_ack
    if hasattr(client, 'send_read_stories'):
        _orig_stories = client.send_read_stories
        async def _ghost_stories(*args, **kwargs):
            if GHOST_MODE:
                return None
            return await _orig_stories(*args, **kwargs)
        client.send_read_stories = _ghost_stories
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
    load_clicks()
    load_owners()
    load_watch()
    me = await client.get_me()
    ME_ID = me.id
    BASE_LAST = CLOCK_RE.sub('', me.last_name or '').strip()
    asyncio.create_task(clock_loop())
    asyncio.create_task(auto_loop())
    asyncio.create_task(probe_loop())
    print(f'🚀 سلف‌بات v{BOT_VERSION} فعال شد!', flush=True)
    print(f'[INIT] GAME={GAME_MODE} WATCH={len(WATCH)} OWNERS={len(OWNERS)} CLICKS={len(CLICKS)}', flush=True)
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
