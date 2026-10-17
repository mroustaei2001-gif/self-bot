import asyncio
import os
import re
import json
import time
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors, types
from telethon.utils import get_peer_id
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import GetParticipantsRequest, GetParticipantRequest
from telethon.tl.functions.messages import GetFullChatRequest, SendMessageRequest
from telethon.tl.types import (ChannelParticipantsAdmins,
                               ChannelParticipantCreator, ChatParticipantCreator,
                               MessageEntityTextUrl)
from telethon.tl.custom import Button

BOT_VERSION = '21-SmartMention'
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
GEN = os.getenv('GEN', '0') == '1'
WIPE = os.getenv('WIPE', '0') == '1'
PHONE = os.getenv('PHONE', '')
CODE = os.getenv('CODE', '')
PASS2 = os.getenv('PASS', '')
SESSION_PATH = os.getenv('SESSION_PATH', '/data/sb')

MASTER_ON = True
GHOST_MODE = False
CLOCK_ON = False
BASE_LAST = ''
ME_ID = None
TTL_SAVE = True
BAN_LOG = True
BAN_DEDUPE = {}
PMLOG_ON = True
PM_CACHE = {}
WATCH = set()
WATCH_PATH = '/data/watch.json'
LAST_SEEN = {}
LAST_BTN = None
LAST_BTN_TEXTS = []
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
COMMON_BUSY = False

NAMES = []
NAMES_PATH = '/data/names.json'
LAST_MSG_BY_USER = {}

# ══════════════════════════════════════════
# سیستم منشن هوشمند - ذخیره UID برای پیام بعدی
# ═══════════════════════════════════════════
PENDING_MENTION = {}  # {chat_id: {'uid': uid, 'username': username}}

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

FONTS = [
    {'d': '⁰¹²³⁵⁶⁷⁸⁹', 'c': ''},
    {'d': '₀₁₂₄₅⁷⁸', 'c': ''},
    {'d': '𝟸𝟹𝟺𝟼', 'c': ':'},
    {'d': '𝟘𝟙𝟟', 'c': ':'},
    {'d': '𝟭𝟮𝟳', 'c': ':'},
    {'d': '①②⑤⑥⑦⑧⑨', 'c': ':'},
    {'d': '⓿❺❼❾', 'c': ':'},
    {'d': '۰۲۴۷۸', 'c': ':'},
    {'d': '٢٣٤٦٧٨٩', 'c': ':'},
    {'d': '0123456789', 'c': ':'},
    {'d': '𝟎𝟔𝟗', 'c': ':'},
    {'d': '𝟢𝟨𝟪', 'c': ':'},
]
CUSTOM_FONTS = []
CUSTOM_FONTS_PATH = '/data/fonts.json'

def load_custom_fonts():
    global CUSTOM_FONTS
    try:
        with open(CUSTOM_FONTS_PATH) as f:
            CUSTOM_FONTS = json.load(f)
    except Exception:
        CUSTOM_FONTS = []

def save_custom_fonts():
    try:
        with open(CUSTOM_FONTS_PATH, 'w') as f:
            json.dump(CUSTOM_FONTS, f)
    except Exception:
        pass

def load_names():
    global NAMES
    try:
        with open(NAMES_PATH) as f:
            NAMES = json.load(f)
    except Exception:
        NAMES = []

def save_names():
    try:
        with open(NAMES_PATH, 'w') as f:
            json.dump(NAMES, f)
    except Exception:
        pass

def rebuild_clock_re():
    global CLOCK_RE
    allc = ''.join(f['d'] for f in FONTS + CUSTOM_FONTS) + ''.join(f['c'] for f in FONTS + CUSTOM_FONTS)
    CLOCK_RE = re.compile('[' + re.escape(allc) + r'\s]+$')

rebuild_clock_re()

def active_fonts():
    return CUSTOM_FONTS if CUSTOM_FONTS else FONTS

def get_font_for_hour(hour):
    fs = active_fonts()
    return fs[hour % len(fs)]

def small_time_with_font(font):
    tz = timezone(timedelta(hours=3, minutes=30))
    now = datetime.now(tz)
    if len(font['d']) != 10:
        return now.strftime('%H:%M')
    table = {ord(d): s for d, s in zip('0123456789', font['d'])}
    table[ord(':')] = font['c']
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

async def normalize_stored():
    changed = False
    for store in (AUTOS, CLICKS):
        for k, v in list(store.items()):
            c = str(v.get('chat', ''))
            if c.isdigit():
                try:
                    ent = await client.get_entity(int(c))
                    v['chat'] = str(get_peer_id(ent))
                    changed = True
                except Exception:
                    pass
    if changed:
        save_autos()
        save_clicks()
        print('[FIX] stored ids normalized', flush=True)

async def clock_loop():
    last_time = ''
    last_hour = -1
    current_font = None
    while True:
        try:
            if CLOCK_ON and MASTER_ON:
                tz = timezone(timedelta(hours=3, minutes=30))
                now = datetime.now(tz)
                hour = now.hour
                if hour != last_hour:
                    last_hour = hour
                    current_font = get_font_for_hour(hour)
                    print(f'[CLOCK] hour={hour} font_idx={hour % len(active_fonts())}', flush=True)
                if current_font:
                    t = small_time_with_font(current_font)
                    name_part = NAMES[hour % len(NAMES)] if NAMES else BASE_LAST
                    new_name = f"{name_part} {t}".strip()
                    if new_name != last_time:
                        await client(UpdateProfileRequest(last_name=new_name))
                        last_time = new_name
        except Exception as e:
            print(f'[CLOCK] error: {e}', flush=True)
        await asyncio.sleep(10)

async def probe_loop():
    while True:
        await asyncio.sleep(120)
        if ME_ID is None or not MASTER_ON:
            continue
        for cid in list(WATCH):
            if cid == ME_ID:
                WATCH.discard(cid)
                continue
            try:
                ent = await client.get_entity(cid)
                if not (getattr(ent, 'channel', False) or getattr(ent, 'megagroup', False) or getattr(ent, 'broadcast', False)):
                    continue
                inp = getattr(ent, 'input_channel', None)
                if inp is None:
                    continue
                res = await client(GetParticipantRequest(inp, types.InputUserSelf()))
                part = getattr(res, 'participant', None)
                if isinstance(part, types.ChannelParticipantBanned):
                    kicked = getattr(part, 'kicked_by', None)
                    print(f'[BAN] probe banned in {cid} by {kicked}', flush=True)
                    await log_ban(cid, kicked, None)
                    WATCH.discard(cid)
                    save_watch()
            except errors.UserNotParticipantError:
                last = LAST_SEEN.get(cid, 0)
                if last > 0 and time.time() - last < 12 * 3600:
                    print(f'[BAN] probe lost access in {cid} - logging', flush=True)
                    await log_ban(cid, None, None)
                WATCH.discard(cid)
                save_watch()
            except errors.ChannelPrivateError:
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
            if AUTO_ON and MASTER_ON:
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
                                await client.send_message('me', f'️ ردیف {key} در گروه {cid} متوقف شد.')
                            except Exception:
                                pass
        except Exception as e:
            print(f'[AUTO] loop error: {e}', flush=True)
        await asyncio.sleep(20)

def looks_like_id(s):
    return bool(s) and s.startswith('-') and s[1:].isdigit()

async def resolve_target(target):
    if looks_like_id(target):
        ent = await client.get_entity(int(target))
    else:
        ent = await client.get_entity(target)
    return ent, str(get_peer_id(ent))

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

@client.on(events.NewMessage(incoming=True))
async def track_last_msg(event):
    if not MASTER_ON:
        return
    cid = event.chat_id
    sender = await event.get_sender()
    if not sender or not sender.id or sender.id == ME_ID:
        return
    LAST_MSG_BY_USER[(cid, sender.id)] = event.message

@client.on(events.NewMessage(incoming=True))
async def pm_cache(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None:
        return
    if not event.is_private or event.chat_id == ME_ID:
        return
    sender = await event.get_sender()
    name = ((getattr(sender, 'first_name', '') or '') + ' ' + (getattr(sender, 'last_name', '') or '')).strip()
    PM_CACHE[(event.chat_id, event.id)] = {'text': event.text or '', 'name': name or 'ناشناس', 'media': bool(event.media)}
    if len(PM_CACHE) > 3000:
        for k in list(PM_CACHE.keys())[:500]:
            PM_CACHE.pop(k, None)

@client.on(events.MessageEdited(incoming=True))
async def pm_edit_logger(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None:
        return
    if not event.is_private or event.chat_id == ME_ID:
        return
    key = (event.chat_id, event.id)
    old = PM_CACHE.get(key, {})
    old_text = old.get('text', '(نامشخص)')
    name = old.get('name', 'ناشناس')
    PM_CACHE[key] = {'text': event.text or '', 'name': name, 'media': bool(event.media)}
    try:
        await client.send_message('me', f'✏️ **ادیت در پی‌وی** توسط: {name}\n متن قبلی: {old_text}\n متن جدید: {event.text or ""}', parse_mode='md')
    except Exception:
        pass

@client.on(events.MessageDeleted)
async def pm_delete_logger(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None:
        return
    chat_id = getattr(event, 'chat_id', None)
    if chat_id is None:
        return
    for mid in getattr(event, 'deleted_ids', []):
        key = (chat_id, mid)
        rec = PM_CACHE.pop(key, None)
        if rec:
            extra = ' (داشت رسانه)' if rec.get('media') else ''
            try:
                await client.send_message('me', f'🗑️ **حذف در پی‌وی** توسط: {rec["name"]}{extra}\n متن حذف‌شده: {rec["text"] or "(خالی)"}', parse_mode='md')
            except Exception:
                pass

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
        lines.append('👤 **بن‌کننده:** 🎭 ناشناس/نامشخص')
    else:
        fn = getattr(admin, 'first_name', '') or ''
        ln = getattr(admin, 'last_name', '') or ''
        lines.append(f'👤 **بن‌کننده:** {(fn + " " + ln).strip() or "بدون نام"}')
        lines.append(f'🆔 **ID بن‌کننده:** `{admin.id}`')
        if getattr(admin, 'username', None):
            lines.append(f' **Username بن‌کننده:** @{admin.username}')
    if own:
        lines.append(f' **مالک/سازنده:** {own["owner_name"] or "بدون نام"}')
        lines.append(f'🆔 **ID مالک:** `{own["owner_id"]}`')
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
    if ME_ID is None or not MASTER_ON:
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
    if ME_ID is None or not MASTER_ON:
        return
    try:
        ids = getattr(event, 'user_id', None) or []
        if isinstance(ids, int):
            ids = [ids]
        if ME_ID not in ids:
            return
        if event.user_joined or event.user_added:
            return
        admin_id = None
        try:
            am = event.action_message
            if am is not None and getattr(am, 'from_id', None) is not None:
                admin_id = getattr(am.from_id, 'user_id', None)
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

# ═══════════════════════════════════════════
# سیستم منشن هوشمند - روش Zero-Width Space برای دور زدن ربات نگهبان
# ═══════════════════════════════════════════

RESERVED_COMMANDS = {
    '/rp', '/m', '/mwho', '/bot', '/common', '/name', '/banlog',
    '/pmlog', '/font', '/reveal', '/spamcheck', '/ttl', '/click',
    '/dl', '/dlast', '/getmsg', '/auto', '/status', '/clock',
    '/ping', '/save', '/del', '/ghost', '/help'
}

async def send_mention_message(chat_id, text, uid):
    """
    ارسال پیام با منشن مخفی با استفاده از Zero-Width Space برای دور زدن ربات نگهبان.
    """
    try:
        # دریافت InputPeer برای چت
        peer = await client.get_input_entity(chat_id)
        
        # اضافه کردن کاراکتر نامرئی (Zero-Width Space) به انتهای متن
        # این کاراکتر در نمایش دیده نمی‌شود اما در متن وجود دارد
        invisible_char = '\u200b'
        modified_text = text + invisible_char
        
        # ساخت entity برای منشن مخفی - لینک tg://user?id=UID
        url = f"tg://user?id={int(uid)}"
        entities = [MessageEntityTextUrl(offset=0, length=len(modified_text), url=url)]
        
        # ارسال مستقیم با SendMessageRequest
        await client(SendMessageRequest(
            peer=peer,
            message=modified_text,
            entities=entities
        ))
        return True
    except Exception as e:
        print(f'[SEND_MENTION] error: {e}', flush=True)
        return False

@client.on(events.NewMessage(outgoing=True))
async def smart_rp_handler(event):
    try:
        msg = event.message
        text = msg.text
        chat_id = event.chat_id
        
        if not text:
            return
        
        clean_text = text.strip()
        if clean_text.startswith('**') and clean_text.endswith('**'):
            clean_text = clean_text[2:-2].strip()
        
        # حالت 1: فقط "/" - ثبت کاربر برای منشن بعدی و حذف فوری
        if clean_text == '/':
            reply_to_id = msg.reply_to_msg_id
            if not reply_to_id:
                await msg.delete(revoke=True)
                return
            
            original_msg = await client.get_messages(chat_id, ids=reply_to_id)
            if not original_msg:
                await msg.delete(revoke=True)
                return
            
            sender = await original_msg.get_sender()
            if not sender or not sender.id:
                await msg.delete(revoke=True)
                return
            
            uid = sender.id
            username = getattr(sender, 'username', None)
            
            # ذخیره UID برای پیام بعدی
            PENDING_MENTION[chat_id] = {'uid': uid, 'username': username}
            
            # حذف فوری پیام "/"
            await msg.delete(revoke=True)
            return
        
        # حالت 2: پیام ساده با منشن در انتظار - ارسال با Zero-Width Space
        if chat_id in PENDING_MENTION:
            pending = PENDING_MENTION[chat_id]
            uid = pending['uid']
            
            # ریست سیستم
            del PENDING_MENTION[chat_id]
            
            # حذف پیام ساده
            await msg.delete(revoke=True)
            
            # ارسال پیام با منشن مخفی و Zero-Width Space
            await send_mention_message(chat_id, clean_text, uid)
            return
        
        # حالت 3: دستورات رزرو شده (نادیده گرفته می‌شوند تا اجرا شوند)
        first_word = clean_text.split()[0].lower() if clean_text else ''
        if first_word in RESERVED_COMMANDS:
            return
        
        # حالت 4: /متن با ریپلای (روش قدیمی - با Zero-Width Space)
        if clean_text.startswith('/') and msg.reply_to_msg_id:
            rp_text = clean_text[1:].strip()
            if rp_text:
                reply_to_id = msg.reply_to_msg_id
                original_msg = await client.get_messages(chat_id, ids=reply_to_id)
                if original_msg:
                    sender = await original_msg.get_sender()
                    if sender and sender.id:
                        uid = sender.id
                        
                        await msg.delete(revoke=True)
                        await send_mention_message(chat_id, rp_text, uid)
                        return
        
    except errors.ChatWriteForbiddenError:
        pass
    except Exception as e:
        print(f'[SMART_RP] error: {e}', flush=True)
        if event.chat_id in PENDING_MENTION:
            del PENDING_MENTION[event.chat_id]

# ═══════════════════════════════════════════
# بقیه دستورات اصلی
# ═══════════════════════════════════════════

@client.on(events.NewMessage(pattern=r'^/rp\s*(.*)$', chats='me'))
async def rp_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text:
        await event.edit(' قالب: /rp متن پیام\n(روی پیام طرف ریپلای بزن)')
        return
    
    rmsg = await event.get_reply_message()
    if not rmsg:
        await event.edit('⚠️ باید روی پیام طرف ریپلای بزنی!')
        return
    
    sender = await rmsg.get_sender()
    if not sender or not sender.id:
        await event.edit('❌ فرستنده پیام شناسایی نشد.')
        return
    
    uid = sender.id
    
    await send_mention_message(event.chat_id, text, uid)
    await event.delete()


@client.on(events.NewMessage(pattern=r'^/m\s*(.*)$', chats='me'))
async def m_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text:
        await event.edit('❌ قالب: /m متن پیام')
        return
    
    cid = event.chat_id
    if cid == ME_ID:
        await event.edit('❌ این دستور فقط در گروه کار می‌کند.')
        return
    
    target = None
    for (chat_id, user_id), msg in LAST_MSG_BY_USER.items():
        if chat_id == cid and user_id != ME_ID:
            target = (user_id, msg)
            break
    
    if target is None:
        await event.edit('❌ هنوز پیامی از کسی در این گروه ندیده‌ام. صبر کن یک پیام بیاید.')
        return
    
    uid, msg = target
    
    await send_mention_message(cid, text, uid)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^/mwho$', chats='me'))
async def mwho_cmd(event):
    cid = event.chat_id
    if cid == ME_ID:
        await event.edit('❌ فقط در گروه کار می‌کند.')
        return
    
    found = []
    for (chat_id, user_id), msg in list(LAST_MSG_BY_USER.items()):
        if chat_id == cid and user_id != ME_ID:
            sender = await msg.get_sender()
            fn = getattr(sender, 'first_name', '') or ''
            ln = getattr(sender, 'last_name', '') or ''
            uname = getattr(sender, 'username', None)
            name = (fn + ' ' + ln).strip() or 'بدون نام'
            found.append((user_id, name, uname))
    
    if not found:
        await event.edit('📭 هنوز پیامی از کسی در این گروه ثبت نشده.')
        return
    
    lines = [f'👥 **آخرین فرستندگان در این گروه:**']
    for uid, name, un in found[:10]:
        un_str = f' @{un}' if un else ''
        lines.append(f'• {name}{un_str} (`{uid}`)')
    await event.edit('\n'.join(lines), parse_mode='md')

@client.on(events.NewMessage(pattern=r'^/bot\s+(on|off)$', chats='me'))
async def bot_cmd(event):
    global MASTER_ON
    MASTER_ON = (event.pattern_match.group(1) == 'on')
    if MASTER_ON:
        await event.edit('🤖 سلف‌بات: روشن ✅', buttons=[[Button.inline('❌ خاموش کردن', b'bot_off')]])
    else:
        await event.edit('🤖 سلف‌بات: خاموش ❌\n(همه کارهای خودکار متوقف؛ دستورات فعال)', buttons=[[Button.inline('✅ روشن کردن', b'bot_on')]])

@client.on(events.CallbackQuery)
async def bot_buttons(event):
    global MASTER_ON
    try:
        if event.data == b'bot_on':
            MASTER_ON = True
            await event.edit('🤖 سلف‌بات: روشن ✅', buttons=[[Button.inline('❌ خاموش کردن', b'bot_off')]])
        elif event.data == b'bot_off':
            MASTER_ON = False
            await event.edit('🤖 سلف‌بات: خاموش ❌\n(همه کارهای خودکار متوقف؛ دستورات فعال)', buttons=[[Button.inline('✅ روشن کردن', b'bot_on')]])
    except Exception:
        pass

@client.on(events.NewMessage(pattern=r'^/common\s+(\S+)$', chats='me'))
async def common_cmd(event):
    global COMMON_BUSY
    if COMMON_BUSY:
        await event.edit('⏳ یک بررسی دیگر در جریان است؛ صبر کن.')
        return
    COMMON_BUSY = True
    target = event.pattern_match.group(1)
    await event.edit(' در حال بررسی گروه‌های مشترک... (ممکن است ۱-۲ دقیقه طول بکشد)')
    try:
        uid = int(target) if target.lstrip('-').isdigit() else target
        ent = await client.get_entity(uid)
        uid = ent.id
        uname = ((getattr(ent, 'first_name', '') or '') + ' ' + (getattr(ent, 'last_name', '') or '')).strip()
    except Exception as e:
        await event.edit(f'❌ کاربر پیدا نشد: {type(e).__name__}')
        COMMON_BUSY = False
        return
    found = []
    skipped = 0
    checked = 0
    try:
        async for d in client.iter_dialogs(limit=100):
            if not (d.is_group or d.is_channel):
                continue
            checked += 1
            try:
                await client.get_participant(d.id, uid)
                found.append((d.title, d.id))
            except errors.UserNotParticipantError:
                pass
            except (errors.ChatAdminRequiredError, errors.ChannelPrivateError, errors.ChatPrivateError):
                skipped += 1
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                skipped += 1
            await asyncio.sleep(0.25)
    except Exception as e:
        await event.edit(f'❌ خطا: {e}')
        COMMON_BUSY = False
        return
    lines = [f'🔍 **گروه‌های مشترک تو و {uname or uid}:**']
    if found:
        for t, i in found:
            lines.append(f'• {t} (`{i}`)')
    else:
        lines.append('• هیچ گروه مشترکی پیدا نشد.')
    if skipped:
        lines.append(f'\n⚠️ {skipped} چت قابل بررسی نبود (لیست اعضا مخفی)')
    lines.append(f'\n(بررسی شد: {checked} چت)')
    await event.edit('\n'.join(lines), parse_mode='md')
    COMMON_BUSY = False

@client.on(events.NewMessage(pattern=r'^/name\s+(add|list|del|reset|test)\s*(.*)$', chats='me'))
async def name_cmd(event):
    global NAMES
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    
    if act == 'list':
        if not NAMES:
            await event.edit(' لیست اسم‌ها خالی است.\n(فقط اسم اصلی پروفایل استفاده می‌شود)\n➕ افزودن: /name add علی ')
            return
        lines = [f'📝 **لیست اسم‌های پروفایل ({len(NAMES)} اسم):**']
        for i, n in enumerate(NAMES, 1):
            lines.append(f'{i}) {n}')
        lines.append('\n💡 هر ساعت یکی از این اسم‌ها نمایش داده می‌شود.')
        await event.edit('\n'.join(lines))
        return
    
    if act == 'add':
        if not rest:
            await event.edit('❌ قالب: /name add اسم دلخواه\nمثال: /name add علی 👑\nیا: /name add  ستاره 🌟')
            return
        NAMES.append(rest)
        save_names()
        await event.edit(f'✅ اسم اضافه شد!\nالان {len(NAMES)} اسم داری.\n اسم جدید: {rest}')
        return
    
    if act == 'del':
        if not rest.isdigit() or not (1 <= int(rest) <= len(NAMES)):
            await event.edit('❌ شماره اسم را بده (از /name list)')
            return
        removed = NAMES.pop(int(rest) - 1)
        save_names()
        await event.edit(f'🗑️ اسم حذف شد: {removed}')
        return
    
    if act == 'reset':
        NAMES = []
        save_names()
        await event.edit('🔄 لیست اسم‌ها پاک شد.\n(فقط اسم اصلی پروفایل استفاده می‌شود)')
        return
    
    if act == 'test':
        tz = timezone(timedelta(hours=3, minutes=30))
        h = datetime.now(tz).hour
        font = get_font_for_hour(h)
        t = small_time_with_font(font)
        if NAMES:
            name_part = NAMES[h % len(NAMES)]
            next_name = NAMES[(h + 1) % len(NAMES)]
        else:
            name_part = BASE_LAST or 'بدون اسم'
            next_name = name_part
        current = f"{name_part} {t}"
        next_h = (h + 1) % 24
        next_font = get_font_for_hour(next_h)
        next_t = small_time_with_font(next_font)
        next_full = f"{next_name} {next_t}"
        await event.edit(f'🕐 **الان (ساعت {h}):**\n{current}\n\n **ساعت بعد ({next_h}):**\n{next_full}\n\n🔢 تعداد اسم‌ها: {len(NAMES)}\n🔤 فونت الان: {font["d"][:5]}...')
        return

@client.on(events.NewMessage(pattern=r'^/banlog\s+(on|off)$', chats='me'))
async def banlog_cmd(event):
    global BAN_LOG
    BAN_LOG = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🚨 گزارش بن: {"روشن ✅" if BAN_LOG else "خاموش ❌"}')

@client.on(events.NewMessage(pattern=r'^/pmlog\s+(on|off)$', chats='me'))
async def pmlog_cmd(event):
    global PMLOG_ON
    PMLOG_ON = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🕵️ ثبت ادیت/حذف پی‌وی: {"روشن ✅" if PMLOG_ON else "خاموش ❌"}')

@client.on(events.NewMessage(pattern=r'^/font\s+(list|add|del|reset|test)\s*(.*)$', chats='me'))
async def font_cmd(event):
    global CUSTOM_FONTS
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    if act == 'list':
        lines = [f'🎨 فونت‌های پیش‌فرض: {len(FONTS)}']
        for i, f in enumerate(FONTS, 1):
            lines.append(f'{i}) {f["d"][:5]}...')
        lines.append(f'\n⭐ فونت‌های دلخواه تو: {len(CUSTOM_FONTS)}')
        for i, f in enumerate(CUSTOM_FONTS, 1):
            lines.append(f'{i}) {f["d"]}')
        lines.append('\n💡 اگر فونت دلخواه داشته باشی، فقط همان‌ها استفاده می‌شوند.')
        lines.append('➕ افزودن: /font add ۰۱۳۴۵۶۷۹:')
        await event.edit('\n'.join(lines))
        return
    if act == 'add':
        if len(rest) < 10:
            await event.edit('❌ قالب: /font add <۱۰ رقم به ترتیب ۰ تا ۹>[<کاراکتر دونقطه>]\nمثال: /font add 𝟘𝟙𝟚𝟜𝟝𝟞𝟠𝟡:')
            return
        d = rest[:10]
        c = rest[10] if len(rest) > 10 else ':'
        CUSTOM_FONTS.append({'d': d, 'c': c})
        save_custom_fonts()
        rebuild_clock_re()
        table = {ord(x): y for x, y in zip('0123456789', d)}
        table[ord(':')] = c
        sample = '12:34'.translate(table)
        await event.edit(f'✅ فونت اضافه شد! نمونه: {sample}\nالان {len(CUSTOM_FONTS)} فونت دلخواه داری و هر ساعت عوض می‌شود.')
        return
    if act == 'del':
        if not rest.isdigit() or not (1 <= int(rest) <= len(CUSTOM_FONTS)):
            await event.edit('❌ شماره فونت دلخواه را بده (از /font list)')
            return
        removed = CUSTOM_FONTS.pop(int(rest) - 1)
        save_custom_fonts()
        rebuild_clock_re()
        await event.edit(f'️ فونت {removed["d"]} حذف شد.')
        return
    if act == 'reset':
        CUSTOM_FONTS = []
        save_custom_fonts()
        rebuild_clock_re()
        await event.edit('🗑️ فونت‌های دلخواه پاک شدند؛ برمی‌گردد به ۲ فونت پیش‌فرض.')
        return
    if act == 'test':
        tz = timezone(timedelta(hours=3, minutes=30))
        h = datetime.now(tz).hour
        f = get_font_for_hour(h)
        table = {ord(x): y for x, y in zip('0123456789', f['d'])}
        table[ord(':')] = f['c']
        cur = '12:34'.translate(table)
        f2 = get_font_for_hour((h + 1) % 24)
        t2 = {ord(x): y for x, y in zip('0123456789', f2['d'])}
        t2[ord(':')] = f2['c']
        nxt = '12:34'.translate(t2)
        await event.edit(f'🕐 فونت الان (ساعت {h}): {cur}\n🕐 فونت ساعت بعد ({(h+1)%24}): {nxt}\n(مجموع {len(active_fonts())} فونت فعال)')
        return

@client.on(events.NewMessage(pattern=r'^/reveal\s*(.*)$', chats='me'))
async def reveal_cmd(event):
    arg = (event.pattern_match.group(1) or '').strip()
    uid = None
    if arg:
        m = re.search(r'-?\d+', arg)
        if m:
            try:
                uid = int(m.group())
            except Exception:
                pass
    if uid is None:
        rmsg = await event.get_reply_message()
        if rmsg and rmsg.text:
            m = re.search(r'(?:آیدی|ایدی|ID|id|آی‌دی|عدد[یي])\s*(?:عددی|عدد)?\s*:?\s*(-?\d+)', rmsg.text)
            if not m:
                m = re.search(r'(-?\d{5,15})', rmsg.text)
            if m:
                try:
                    uid = int(m.group(1))
                except Exception:
                    pass
    if uid is None:
        await event.edit('❌ قالب: /reveal 123456789\nیا روی پیام ربات reply بزن.')
        return
    await event.edit('🔍 در حال شناسایی...')
    try:
        ent = await client.get_entity(uid)
    except Exception as e:
        await event.edit(f'❌ کاربر پیدا نشد: {type(e).__name__}\nممکن است اکانت حذف شده باشد، ID مال ربات/کانال باشد، یا ربات ناشناس ID جعلی نشان داده باشد.')
        return
    fn = getattr(ent, 'first_name', '') or ''
    ln = getattr(ent, 'last_name', '') or ''
    name = (fn + ' ' + ln).strip() or 'بدون نام'
    un = getattr(ent, 'username', None)
    phone = getattr(ent, 'phone', None)
    is_bot = getattr(ent, 'bot', False)
    lines = [f' **کاربر شناسایی شد!**']
    lines.append(f'👤 **نام:** {name}')
    lines.append(f'🆔 **ID:** `{ent.id}`')
    if un:
        lines.append(f'🔗 **Username:** @{un}')
    if phone:
        lines.append(f'📞 **شماره:** +{phone}')
    else:
        lines.append(f' **شماره:** (خصوصی است — تلگرام اجازه نمی‌دهد)')
    if is_bot:
        lines.append(f'🤖 **نوع:** ربات (نه کاربر عادی)')
    rows = []
    if un:
        rows.append([Button.url(f'📩 پی‌وی {name}', f'https://t.me/{un}')])
    else:
        rows.append([Button.url(f'📩 پی‌وی {name}', f'tg://user?id={ent.id}')])
    try:
        await client.send_message('me', '\n'.join(lines), buttons=rows, parse_mode='md')
        await event.delete()
    except Exception as e:
        await event.edit('\n'.join(lines) + f'\n(خطا: {e})')

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
        await event.edit(f' خطا: {e}')
    finally:
        SPAM_LOCK = False

@client.on(events.NewMessage(incoming=True))
async def ttl_saver(event):
    if not TTL_SAVE or not MASTER_ON:
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
            await client.send_file('me', path, caption=f' رسانه نابودشونده ذخیره‌شده از: {name or "ناشناس"}')
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
    global LAST_BTN, LAST_BTN_TEXTS
    if not CLICK_ON or not MASTER_ON:
        return
    try:
        if not event.message.buttons:
            return
    except Exception:
        return
    cid = str(event.chat_id)
    texts = []
    for row in event.message.buttons:
        for btn in row:
            texts.append(btn.text or '')
    LAST_BTN = event.chat_id
    LAST_BTN_TEXTS = texts
    print(f'[CLICK] buttons seen in {cid}: {texts}', flush=True)
    matched = False
    for key, rule in list(CLICKS.items()):
        if rule.get('chat') in (cid, '*'):
            matched = True
            for row in event.message.buttons:
                for btn in row:
                    btn_text = btn.text or ''
                    if rule['text'] in btn_text:
                        try:
                            await btn.click()
                            print(f'[CLICK] clicked "{rule["text"]}" in {cid}', flush=True)
                        except Exception as e:
                            print(f'[CLICK] failed: {e}', flush=True)
                        return
    if not matched:
        print(f'[CLICK] no rule for {cid} | rules={CLICKS}', flush=True)

@client.on(events.NewMessage(incoming=True))
async def ghost_mirror(event):
    if not GHOST_MODE or not MASTER_ON:
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

@client.on(events.NewMessage(pattern=r'^/click\s+(add|addh|addany|del|list|on|off|clear|peek)\s*(.*)$', chats='me'))
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
        await event.edit('️ کلیک خودکار: خاموش ❌')
        return
    if act == 'peek':
        if LAST_BTN is None:
            await event.edit('❌ هنوز هیچ پیام دکمه‌داری ندیده‌ام.')
            return
        try:
            ent = await client.get_entity(LAST_BTN)
            title = getattr(ent, 'title', None) or getattr(ent, 'first_name', str(LAST_BTN))
        except Exception:
            title = str(LAST_BTN)
        await event.edit(f'👀 آخرین پیام دکمه‌دار:\nگروه: {title} ({LAST_BTN})\nدکمه‌ها:\n' + '\n'.join(f'• {t}' for t in LAST_BTN_TEXTS))
        return
    if act == 'clear':
        n = len(CLICKS)
        CLICKS.clear()
        save_clicks()
        await event.edit(f'🧹 لیست کلیک پاک شد ({n} مورد).')
        return
    if act == 'list':
        if not CLICKS:
            await event.edit('🖱️ لیست کلیک خالی است.')
            return
        lines = [f'{k}) {v.get("title", v["chat"])} → دکمه «{v["text"]}»' for k, v in CLICKS.items()]
        await event.edit('🖱️ لیست کلیک خودکار:\n' + '\n'.join(lines))
        return
    if act == 'addany':
        if not rest:
            await event.edit('❌ قالب: /click addany متن_دکمه')
            return
        key = next_key(CLICKS)
        CLICKS[key] = {'chat': '*', 'text': rest, 'title': 'همه گروه‌ها'}
        save_clicks()
        await event.edit(f'🖱️ از این به بعد دکمه‌های حاوی «{rest}» در **همه گروه‌ها** خودکار کلیک می‌شوند.')
        return
    if act == 'addh':
        if LAST_BTN is None:
            await event.edit('❌ اول /click peek را بزن تا گروه شناسایی شود.')
            return
        if not rest:
            await event.edit('❌ قالب: /click addh متن_دکمه')
            return
        try:
            ent = await client.get_entity(LAST_BTN)
            title = getattr(ent, 'title', None) or getattr(ent, 'first_name', str(LAST_BTN))
        except Exception:
            title = str(LAST_BTN)
        key = next_key(CLICKS)
        CLICKS[key] = {'chat': str(LAST_BTN), 'text': rest, 'title': title}
        save_clicks()
        await event.edit(f'🖱️ دکمه‌های حاوی «{rest}» در {title} خودکار کلیک می‌شوند.')
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
            await event.edit(f'❌ خطا در خواندن پیام: {e}')
            return
    else:
        msg = await event.get_reply_message()
    if msg is None:
        await event.edit('❌ پیام پیدا نشد.')
        return
    if not msg.media:
        await event.edit('📭 پیام حاوی رسانه نیست.')
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
            await event.edit('📝 قالب: /auto add @group [دقیقه] متن')
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
            await event.edit(f' چت پیدا نشد: {e}')
            return
        key = next_key(AUTOS)
        AUTOS[key] = {'chat': cid, 'mode': 'txt', 'word': word, 'interval': minutes * 60, 'last': 0, 'title': getattr(ent, 'title', None) or getattr(ent, 'first_name', target)}
        save_autos()
        await event.edit(f'✅ ردیف {key}: هر {minutes} دقیقه «{word}» در {AUTOS[key]["title"]}.')
        return
    if act == 'addc':
        rmsg = await event.get_reply_message()
        if not rmsg:
            await event.edit('❌ روی پیام موردنظر در Saved Messages ریپلای بزن.')
            return
        tokens = rest.split()
        if not tokens:
            await event.edit('❌ قالب: (ریپلی) /auto addc @group [دقیقه]')
            return
        target = tokens[0]
        minutes = max(1, int(tokens[1])) if len(tokens) > 1 and tokens[1].isdigit() else 5
        if len(AUTOS) >= 30:
            await event.edit('❌ سقف ۳۰ ردیف.')
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

@client.on(events.NewMessage(pattern=r'^/status$', chats='me'))
async def status_cmd(event):
    await event.edit(f'📊 v{BOT_VERSION} | master={MASTER_ON} | ghost={GHOST_MODE} | clock={CLOCK_ON} | names={len(NAMES)} | fonts={len(active_fonts())} | ttl={TTL_SAVE} | banlog={BAN_LOG} | pmlog={PMLOG_ON} | watch={len(WATCH)} | auto={AUTO_ON}({len(AUTOS)}) | click={CLICK_ON}({len(CLICKS)})', buttons=[[Button.inline('✅ روشن', b'bot_on'), Button.inline('❌ خاموش', b'bot_off')]])

@client.on(events.NewMessage(pattern=r'^/clock\s+(on|off)$', chats='me'))
async def clock_cmd(event):
    global CLOCK_ON, BASE_LAST
    if event.pattern_match.group(1) == 'on':
        me = await client.get_me()
        BASE_LAST = CLOCK_RE.sub('', me.last_name or '').strip()
        CLOCK_ON = True
        tz = timezone(timedelta(hours=3, minutes=30))
        h = datetime.now(tz).hour
        font = get_font_for_hour(h)
        t = small_time_with_font(font)
        if NAMES:
            name_part = NAMES[h % len(NAMES)]
        else:
            name_part = BASE_LAST
        new_name = f"{name_part} {t}".strip()
        await client(UpdateProfileRequest(last_name=new_name))
        await event.edit(f' ساعت زنده روشن شد!\nنمونه الان: {new_name}\n(ساعت هر دقیقه آپدیت، فونت و اسم هر ساعت)\n(/name test برای دیدن اسم‌ها)')
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
        await event.delete()

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
    await event.edit('🤖 دستورات سلف‌بات v21-SmartMention:\n\n'
        '🎯 منشن هوشمند (روش Zero-Width Space):\n'
        'مرحله 1: روی پیام کسی ریپلای بزن + فقط / بنویس\n'
        'مرحله 2: ریپلای را کنسل کن\n'
        'مرحله 3: متن ساده بنویس (بدون ریپلای)\n'
        '→ پیام با منشن مخفی ارسال می‌شود (با کاراکتر نامرئی برای دور زدن ربات نگهبان)\n\n'
        '/rp متن → منشن با ریپلای (روش قدیمی)\n'
        '/m متن → منشن سریع آخرین فرستنده\n'
        '/mwho → لیست آخرین فرستندگان\n\n'
        '🔧 عمومی: /bot on|off | /ping | /status | /help\n'
        '👤 شناسایی: /reveal [id] | /common id\n'
        '👤 پروفایل: /name add|list|del|reset|test | /clock on|off | /font list|add|del|reset|test\n'
        '🔒 حریم: /pmlog on|off | /ttl on|off | /banlog on|off | /ghost on|off\n'
        '🖱️ کلیک: /click add|addh|addany|peek|del|clear|list|on|off\n'
        '⏰ اتو: /auto add|addc|del|clear|list|on|off\n'
        '📥 دانلود: /dl لینک | /dlast | /getmsg | /save | /del\n'
        '🔍 اسپم: /spamcheck')

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
    load_custom_fonts()
    load_names()
    me = await client.get_me()
    ME_ID = me.id
    BASE_LAST = CLOCK_RE.sub('', me.last_name or '').strip()
    await normalize_stored()
    asyncio.create_task(clock_loop())
    asyncio.create_task(auto_loop())
    asyncio.create_task(probe_loop())
    print(f'🚀 سلف‌بات v{BOT_VERSION} فعال شد!', flush=True)
    print(f'[INIT] WATCH={len(WATCH)} OWNERS={len(OWNERS)} CLICKS={len(CLICKS)} FONTS={len(active_fonts())} NAMES={len(NAMES)}', flush=True)
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
