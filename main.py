import asyncio
import os
import re
import json
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors, types
from telethon.sessions import StringSession
from telethon.utils import get_peer_id
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import GetParticipantsRequest, GetParticipantRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import (ChannelParticipantsAdmins,
                               ChannelParticipantCreator, ChatParticipantCreator)
from telethon.tl.custom import Button
BOT_VERSION = '25-FixFonts'
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
GEN = os.getenv('GEN', '0') == '1'
WIPE = os.getenv('WIPE', '0') == '1'
RESET_NAMES = os.getenv('RESET_NAMES', '0') == '1'
PHONE = os.getenv('PHONE', '')
CODE = os.getenv('CODE', '')
PASS2 = os.getenv('PASS', '')
SESSION_PATH = os.getenv('SESSION_PATH', '/data/sb')
SESSION_STRING = os.getenv('SESSION_STRING', '')
PHONE_HASH = os.getenv('PHONE_HASH', '')
NTFY_TOPIC = os.getenv('NTFY_TOPIC', '')
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
PRICE_ON = os.getenv('PRICE_ON', '1') == '1'
PRICE_INTERVAL = int(os.getenv('PRICE_INTERVAL', '300'))
last_bio = ''
NAMES = []
NAMES_PATH = '/data/names.json'
LAST_MSG_BY_USER = {}
PENDING_MENTION = {}
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
RAW_FONTS = [
    {'d':'⁰¹²³⁴⁵⁶⁸⁹','c':'ː'},
    {'d': '₀₁₂₃₄₅₆₇₈₉', 'c': ':'},
    {'d': '𝟘𝟙𝟚𝟛𝟜𝟝𝟟𝟠𝟡', 'c': ':'},
    {'d': '0𝟣𝟤𝟥4𝟧𝟨𝟩8𝟫', 'c': ':'},
    {'d': '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗', 'c': ':'},
    {'d': '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿', 'c': ':'},
    {'d': '⓪①②③④⑤⑥⑦⑧⑨', 'c': ':'},
    {'d': '0123456789', 'c': ':'},
    {'d': '۰۱۲۳۴۵۶۷۸۹', 'c': ':'},
    {'d': '٠١٢٣٤٥٦٧٨٩', 'c': ':'},
    {'d': '０１２３４５６７８９', 'c': '：'},
    {'d': '⓿❶❷❸❹❺❻❼❽❾', 'c': ':'},
]
def validate_font(f):
    if not isinstance(f, dict):
        return False
    d = f.get('d', '')
    c = f.get('c', '')
    if not (isinstance(d, str) and len(d) == 10 and isinstance(c, str) and len(c) >= 1):
        return False
    for ch in d:
        if unicodedata.category(ch) not in ('Nd', 'No'):
            return False
    return True
FONTS = [f for f in RAW_FONTS if validate_font(f)]
CUSTOM_FONTS = []
CUSTOM_FONTS_PATH = '/data/fonts.json'
MAX_NAME_LEN = 58
def load_custom_fonts():
    global CUSTOM_FONTS
    try:
        with open(CUSTOM_FONTS_PATH) as f:
            loaded = json.load(f)
        valid = [x for x in loaded if validate_font(x)]
        if len(valid) != len(loaded):
            CUSTOM_FONTS = valid
            save_custom_fonts()
            print(f'[FONTS] {len(loaded) - len(valid)} فونت نامعتبر حذف شد', flush=True)
        else:
            CUSTOM_FONTS = valid
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
    if RESET_NAMES:
        NAMES = []
        save_names()
        print('[NAMES] لیست اسم‌ها ریست شد', flush=True)
        return
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
    fs = CUSTOM_FONTS if CUSTOM_FONTS else FONTS
    return fs if fs else [{'d': '0123456789', 'c': ':'}]
def get_font_for_hour(hour):
    fs = active_fonts()
    return fs[hour % len(fs)]
def small_time_with_font(font):
    tz = timezone(timedelta(hours=3, minutes=30))
    now = datetime.now(tz)
    time_str = now.strftime('%H:%M')
    if not validate_font(font):
        return time_str
    table = {}
    for i, char in enumerate('0123456789'):
        table[ord(char)] = font['d'][i]
    table[ord(':')] = font['c']
    return time_str.translate(table)
def safe_name_part(name):
    return (name or '')[:MAX_NAME_LEN]
def fa_now():
    tz = timezone(timedelta(hours=3, minutes=30))
    return datetime.now(tz).strftime('%Y/%m/%d %H:%M')
async def fetch_json(url, timeout=15):
    def _get():
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    return await asyncio.get_running_loop().run_in_executor(None, _get)
async def fetch_text(url, timeout=20):
    def _get():
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    return await asyncio.get_running_loop().run_in_executor(None, _get)
async def get_usd_toman():
    try:
        d=await fetch_json('https://api.tgju.org/v2/market/indicator/summary-table-data-usd')
        data=d.get('data',{})if isinstance(d,dict)else{}
        item=data.get('usd')or data.get('USD')if isinstance(data,dict)else None
        if isinstance(item,dict)and item.get('price'):
            v=int(str(item['price']).replace(',',''));print(f'[PRICE] usd(tgju)={v}',flush=True);return v,'آزاد'
    except Exception as e:print(f'[PRICE] tgju failed: {e}',flush=True)
    try:
        d=await fetch_json('https://chand.com/api/v1/prices')
        usd=d.get('usd',{}).get('price')
        if usd:v=int(usd);print(f'[PRICE] usd(chand)={v}',flush=True);return v,'chand'
    except Exception as e:print(f'[PRICE] chand failed: {e}',flush=True)
    try:
        d=await fetch_json('https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/usd/irr.json')
        irr=d.get('irr')
        if irr:v=int(irr/10);print(f'[PRICE] usd(currency-api)={v}',flush=True);return v,'رسمی'
    except Exception as e:print(f'[PRICE] currency-api failed: {e}',flush=True)
    try:
        d=await fetch_json('https://open.er-api.com/v6/latest/USD')
        irr=d.get('rates',{}).get('IRR')
        if irr:v=int(irr/10);print(f'[PRICE] usd(er-api)={v}',flush=True);return v,'رسمی'
    except Exception as e:print(f'[PRICE] er-api failed: {e}',flush=True)
    return None,None
async def get_btc_usd():
    try:
        d=await fetch_json('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
        v=float(d['price']);print(f'[PRICE] btc(binance)={v}',flush=True);return v
    except Exception:pass
    try:
        d=await fetch_json('https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT')
        v=float(d['data'][0]['last']);print(f'[PRICE] btc(okx)={v}',flush=True);return v
    except Exception:pass
    try:
        d=await fetch_json('https://chand.com/api/v1/prices')
        btc=d.get('btc',{}).get('price')
        if btc:v=float(btc);print(f'[PRICE] btc(chand)={v}',flush=True);return v
    except Exception as e:print(f'[PRICE] chand btc failed: {e}',flush=True)
    try:
        d=await fetch_json('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        v=float(d['bitcoin']['usd']);print(f'[PRICE] btc(coingecko)={v}',flush=True);return v
    except Exception as e:print(f'[PRICE] btc failed: {e}',flush=True)
    return None
async def get_gold_oz_usd():
    try:
        d=await fetch_json('https://api.gold-api.com/price/XAU')
        v=float(d['price']);print(f'[PRICE] gold(gold-api)={v}',flush=True);return v
    except Exception as e:print(f'[PRICE] gold-api failed: {e}',flush=True)
    try:
        d=await fetch_json('https://chand.com/api/v1/prices')
        gold=d.get('gold',{}).get('price')
        if gold:v=float(gold);print(f'[PRICE] gold(chand)={v}',flush=True);return v
    except Exception as e:print(f'[PRICE] chand gold failed: {e}',flush=True)
    try:
        d=await fetch_json('https://data-asg.goldprice.org/dbXRates/USD')
        v=float(d['items'][0]['xauPrice']);print(f'[PRICE] gold(goldprice)={v}',flush=True);return v
    except Exception as e:print(f'[PRICE] goldprice failed: {e}',flush=True)
    return None
def slash_fmt(n):
    if n is None:
        return '—'
    return f'{int(round(n)):,}'.replace(',', '/')
async def build_bio():
    usd_toman,label=await get_usd_toman();btc_usd=await get_btc_usd();gold_oz_usd=await get_gold_oz_usd()
    gold_gram_toman=None
    if gold_oz_usd and usd_toman:gold_gram_toman=(gold_oz_usd/31.1035)*0.75*usd_toman
    parts=[]
    if usd_toman:parts.append(f'dollrs {slash_fmt(usd_toman)}')
    if btc_usd:parts.append(f'B {int(round(btc_usd/1000))} k')
    if gold_gram_toman:parts.append(f'Gold {slash_fmt(gold_gram_toman)}')
    bio=' / '.join(parts)
    return '\u200e'+bio if bio else None
async def update_bio(new_bio):
    global last_bio
    if new_bio == last_bio:
        return True
    for attempt in range(3):
        try:
            await client(UpdateProfileRequest(about=new_bio))
            last_bio = new_bio
            return True
        except errors.FloodWaitError as e:
            print(f'[BIO] FloodWait {e.seconds}s', flush=True)
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            print(f'[BIO] attempt {attempt + 1} failed: {e}', flush=True)
            await asyncio.sleep(2)
    return False
async def price_loop():
    print('[PRICE] price_loop started (every ' + str(PRICE_INTERVAL) + 's)', flush=True)
    while True:
        try:
            if PRICE_ON and MASTER_ON:
                bio = await build_bio()
                if bio:
                    bio = bio[:70]
                    ok = await update_bio(bio)
                    print(f'[PRICE] bio updated: {bio}' if ok else '[PRICE] bio update failed', flush=True)
        except Exception as e:
            print(f'[PRICE] error: {e}', flush=True)
        await asyncio.sleep(PRICE_INTERVAL)
async def wait_for_code(topic, timeout=600):
    since = int(time.time())
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            txt = await fetch_text(f'https://ntfy.sh/{topic}/json?poll=1&since={since}')
            for line in txt.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                since = max(since, obj.get('time', since) + 1)
                msg = (obj.get('message') or '').strip()
                if msg.isdigit() and len(msg) >= 4:
                    return msg
        except Exception:
            pass
        await asyncio.sleep(3)
    return None
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
async def update_profile_name(new_name):
    for attempt in range(3):
        try:
            await client(UpdateProfileRequest(last_name=new_name))
            return True
        except errors.FloodWaitError as e:
            print(f'[CLOCK] FloodWait {e.seconds}s', flush=True)
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            print(f'[CLOCK] attempt {attempt + 1} failed: {e}', flush=True)
            await asyncio.sleep(2)
    return False
async def clock_loop():
    last_time = ''
    last_minute = -1
    print('[CLOCK] clock_loop started', flush=True)
    while True:
        try:
            if CLOCK_ON and MASTER_ON:
                tz = timezone(timedelta(hours=3, minutes=30))
                now = datetime.now(tz)
                minute = now.minute
                if minute != last_minute:
                    hour = now.hour
                    font = get_font_for_hour(hour)
                    t = small_time_with_font(font)
                    if NAMES:
                        name_part = safe_name_part(NAMES[hour % len(NAMES)])
                    else:
                        name_part = safe_name_part(BASE_LAST)
                    new_name = f"{name_part} {t}".strip()
                    if new_name != last_time:
                        ok = await update_profile_name(new_name)
                        if ok:
                            last_time = new_name
                            last_minute = minute
            else:
                last_minute = -1
                last_time = ''
        except Exception as e:
            print(f'[CLOCK] error: {e}', flush=True)
        await asyncio.sleep(5)
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
                    await log_ban(cid, kicked, None)
                    WATCH.discard(cid)
                    save_watch()
            except errors.UserNotParticipantError:
                last = LAST_SEEN.get(cid, 0)
                if last > 0 and time.time() - last < 12 * 3600:
                    await log_ban(cid, None, None)
                WATCH.discard(cid)
                save_watch()
            except errors.ChannelPrivateError:
                WATCH.discard(cid)
                save_watch()
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                pass
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
                                    raise Exception('source not found')
                                await client.send_message(int(cid), message=src.text, file=src.media)
                            else:
                                await client.send_message(int(cid), item['word'])
                            item['last'] = now
                            save_autos()
                        except (errors.UserBannedInChannelError, errors.ChatWriteForbiddenError):
                            del AUTOS[key]
                            save_autos()
                            try:
                                await log_ban(int(cid), None, None)
                            except Exception:
                                pass
                        except errors.FloodWaitError as e:
                            await asyncio.sleep(e.seconds + 1)
                        except Exception:
                            del AUTOS[key]
                            save_autos()
        except Exception:
            pass
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
        await client.send_message('me', f'✏️ ادیت در پی‌وی: {name}\nقبلی: {old_text}\nجدید: {event.text or ""}', parse_mode='md')
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
            try:
                await client.send_message('me', f'🗑️ حذف در پی‌وی: {rec["name"]}\n{rec["text"] or "(خالی)"}', parse_mode='md')
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
    lines = [f'🚨 بن/حذف شدی در: {chat_title}']
    if admin:
        fn = getattr(admin, 'first_name', '') or ''
        ln = getattr(admin, 'last_name', '') or ''
        lines.append(f' بن‌کننده: {(fn + " " + ln).strip() or "بدون نام"}')
        lines.append(f'🆔 ID: `{admin.id}`')
        if getattr(admin, 'username', None):
            lines.append(f'🔗 @{admin.username}')
    if own:
        lines.append(f'👑 مالک: {own["owner_name"] or "بدون نام"}')
        lines.append(f'🆔 ID: `{own["owner_id"]}`')
        if own.get('owner_username'):
            lines.append(f'🔗 @{own["owner_username"]}')
    lines.append(f'⏰ {fa_now()}')
    try:
        await client.send_message('me', '\n'.join(lines), parse_mode='md')
    except Exception:
        pass
@client.on(events.Raw(types.UpdateChannelParticipant))
async def raw_ban_detector(event):
    if ME_ID is None or not MASTER_ON:
        return
    try:
        if event.user_id != ME_ID:
            return
        np = event.new_participant
        if not isinstance(np, types.ChannelParticipantBanned):
            return
        br = getattr(np, 'banned_rights', None)
        if br is None or not br.view_messages:
            return
        cid = get_peer_id(types.PeerChannel(event.channel_id))
        actor = getattr(event, 'actor_id', None)
        await log_ban(cid, actor, None)
    except Exception:
        pass
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
        await log_ban(event.chat_id, admin_id, None)
    except Exception:
        pass
RESERVED_COMMANDS = {
    '/rp', '/m', '/mwho', '/bot', '/common', '/name', '/banlog',
    '/pmlog', '/font', '/reveal', '/spamcheck', '/ttl', '/click',
    '/dl', '/dlast', '/getmsg', '/auto', '/status', '/clock',
    '/price', '/ping', '/save', '/del', '/ghost', '/help'
}
async def send_mention_message(chat_id, text, uid):
    try:
        url = f"tg://user?id={int(uid)}"
        await client.send_message(chat_id, f"{text} {url}")
        return True
    except Exception:
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
            PENDING_MENTION[chat_id] = {'uid': sender.id}
            await msg.delete(revoke=True)
            return
        if chat_id in PENDING_MENTION:
            uid = PENDING_MENTION[chat_id]['uid']
            del PENDING_MENTION[chat_id]
            await msg.delete(revoke=True)
            await send_mention_message(chat_id, clean_text, uid)
            return
        first_word = clean_text.split()[0].lower() if clean_text else ''
        if first_word in RESERVED_COMMANDS:
            return
        if clean_text.startswith('/') and msg.reply_to_msg_id:
            rp_text = clean_text[1:].strip()
            if rp_text:
                original_msg = await client.get_messages(chat_id, ids=msg.reply_to_msg_id)
                if original_msg:
                    sender = await original_msg.get_sender()
                    if sender and sender.id:
                        await msg.delete(revoke=True)
                        await send_mention_message(chat_id, rp_text, sender.id)
                        return
    except errors.ChatWriteForbiddenError:
        pass
    except Exception:
        if event.chat_id in PENDING_MENTION:
            del PENDING_MENTION[event.chat_id]
@client.on(events.NewMessage(pattern=r'^/price\s+(on|off)$', chats='me'))
async def price_cmd(event):
    global PRICE_ON
    PRICE_ON = (event.pattern_match.group(1) == 'on')
    if PRICE_ON:
        bio = await build_bio()
        if bio:
            await update_bio(bio[:70])
        await event.edit(f'💰 قیمت‌ها: روشن ✅\n{bio[:70] if bio else "—"}')
    else:
        await update_bio('')
        await event.edit('💰 قیمت‌ها: خاموش ❌')
@client.on(events.NewMessage(pattern=r'^/rp\s*(.*)$', chats='me'))
async def rp_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text:
        await event.edit(' /rp متن')
        return
    rmsg = await event.get_reply_message()
    if not rmsg:
        await event.edit('❌ ریپلای کن')
        return
    sender = await rmsg.get_sender()
    if not sender or not sender.id:
        await event.edit('❌ فرستنده پیدا نشد')
        return
    await send_mention_message(event.chat_id, text, sender.id)
    await event.delete()
@client.on(events.NewMessage(pattern=r'^/m\s*(.*)$', chats='me'))
async def m_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text:
        await event.edit('❌ /m متن')
        return
    cid = event.chat_id
    if cid == ME_ID:
        await event.edit('❌ فقط در گروه')
        return
    target = None
    for (chat_id, user_id), msg in LAST_MSG_BY_USER.items():
        if chat_id == cid and user_id != ME_ID:
            target = (user_id, msg)
            break
    if target is None:
        await event.edit('❌ هنوز پیامی ندیدم')
        return
    uid, msg = target
    await send_mention_message(cid, text, uid)
    await event.delete()
@client.on(events.NewMessage(pattern=r'^/mwho$', chats='me'))
async def mwho_cmd(event):
    cid = event.chat_id
    if cid == ME_ID:
        await event.edit('❌ فقط در گروه')
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
        await event.edit('📭 کسی پیام نداده')
        return
    lines = ['👥 آخرین فرستندگان:']
    for uid, name, un in found[:10]:
        un_str = f' @{un}' if un else ''
        lines.append(f'• {name}{un_str} (`{uid}`)')
    await event.edit('\n'.join(lines), parse_mode='md')
@client.on(events.NewMessage(pattern=r'^/bot\s+(on|off)$', chats='me'))
async def bot_cmd(event):
    global MASTER_ON
    MASTER_ON = (event.pattern_match.group(1) == 'on')
    await event.edit(f' سلف‌بات: {"روشن ✅" if MASTER_ON else "خاموش ❌"}')
@client.on(events.CallbackQuery)
async def bot_buttons(event):
    global MASTER_ON
    if event.data == b'bot_on':
        MASTER_ON = True
        await event.edit('🤖 روشن ✅')
    elif event.data == b'bot_off':
        MASTER_ON = False
        await event.edit('🤖 خاموش ❌')
@client.on(events.NewMessage(pattern=r'^/common\s+(\S+)$', chats='me'))
async def common_cmd(event):
    global COMMON_BUSY
    if COMMON_BUSY:
        await event.edit('⏳ صبر کن')
        return
    COMMON_BUSY = True
    target = event.pattern_match.group(1)
    await event.edit('🔍 در حال بررسی...')
    try:
        uid = int(target) if target.lstrip('-').isdigit() else target
        ent = await client.get_entity(uid)
        uid = ent.id
        uname = ((getattr(ent, 'first_name', '') or '') + ' ' + (getattr(ent, 'last_name', '') or '')).strip()
    except Exception as e:
        await event.edit(f' کاربر پیدا نشد: {e}')
        COMMON_BUSY = False
        return
    found = []
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
            except Exception:
                pass
            await asyncio.sleep(0.25)
    except Exception:
        pass
    lines = [f'🔍 گروه‌های مشترک با {uname or uid}:']
    if found:
        for t, i in found:
            lines.append(f'• {t} (`{i}`)')
    else:
        lines.append('• هیچ گروه مشترکی پیدا نشد')
    lines.append(f'\nبررسی شد: {checked}')
    await event.edit('\n'.join(lines), parse_mode='md')
    COMMON_BUSY = False
@client.on(events.NewMessage(pattern=r'^/name\s+(add|list|del|reset|test)\s*(.*)$', chats='me'))
async def name_cmd(event):
    global NAMES
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    if act == 'list':
        if not NAMES:
            await event.edit(' لیست خالی است\n➕ /name add اسم')
            return
        lines = [f'📝 {len(NAMES)} اسم:']
        for i, n in enumerate(NAMES, 1):
            lines.append(f'{i}) {n}')
        await event.edit('\n'.join(lines))
        return
    if act == 'add':
        if not rest:
            await event.edit(' /name add اسم')
            return
        if len(rest) > MAX_NAME_LEN:
            await event.edit(f'⚠️ حداکثر {MAX_NAME_LEN} کاراکتر')
            return
        NAMES.append(rest)
        save_names()
        await event.edit(f'✅ {len(NAMES)} اسم: {rest}')
        return
    if act == 'del':
        if not rest.isdigit() or not (1 <= int(rest) <= len(NAMES)):
            await event.edit('❌ شماره از /name list')
            return
        removed = NAMES.pop(int(rest) - 1)
        save_names()
        await event.edit(f'🗑️ حذف: {removed}')
        return
    if act == 'reset':
        NAMES = []
        save_names()
        await event.edit('🔄 لیست پاک شد')
        return
    if act == 'test':
        tz = timezone(timedelta(hours=3, minutes=30))
        h = datetime.now(tz).hour
        font = get_font_for_hour(h)
        t = small_time_with_font(font)
        name_part = safe_name_part(NAMES[h % len(NAMES)] if NAMES else BASE_LAST or 'بدون اسم')
        current = f"{name_part} {t}"
        await event.edit(f'🕐 ساعت {h}: {current}\n📏 {len(current)}/64')
        return
@client.on(events.NewMessage(pattern=r'^/banlog\s+(on|off)$', chats='me'))
async def banlog_cmd(event):
    global BAN_LOG
    BAN_LOG = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🚨 گزارش بن: {"✅" if BAN_LOG else ""}')
@client.on(events.NewMessage(pattern=r'^/pmlog\s+(on|off)$', chats='me'))
async def pmlog_cmd(event):
    global PMLOG_ON
    PMLOG_ON = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🕵️ پی‌وی لاگ: {"✅" if PMLOG_ON else "❌"}')
@client.on(events.NewMessage(pattern=r'^/font\s+(list|add|del|reset|test)\s*(.*)$', chats='me'))
async def font_cmd(event):
    global CUSTOM_FONTS
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    if act == 'list':
        lines = [f'🎨 {len(FONTS)} فونت پیش‌فرض:']
        for i, f in enumerate(FONTS, 1):
            lines.append(f'{i}) {f["d"]}')
        if CUSTOM_FONTS:
            lines.append(f'\n⭐ {len(CUSTOM_FONTS)} فونت دلخواه:')
            for i, f in enumerate(CUSTOM_FONTS, 1):
                lines.append(f'{i}) {f["d"]}')
        await event.edit('\n'.join(lines))
        return
    if act == 'add':
        if len(rest) < 10:
            await event.edit(' ۱۰ رقم + دونقطه\nمثال: /font add 𝟘𝟚𝟛𝟜𝟞𝟟𝟠:')
            return
        d = rest[:10]
        c = rest[10] if len(rest) > 10 else ':'
        new_font = {'d': d, 'c': c}
        if not validate_font(new_font):
            await event.edit('❌ فونت نامعتبر (فقط اعداد)')
            return
        CUSTOM_FONTS.append(new_font)
        save_custom_fonts()
        rebuild_clock_re()
        await event.edit('✅ فونت اضافه شد')
        return
    if act == 'del':
        if not rest.isdigit() or not (1 <= int(rest) <= len(CUSTOM_FONTS)):
            await event.edit('❌ شماره از /font list')
            return
        CUSTOM_FONTS.pop(int(rest) - 1)
        save_custom_fonts()
        rebuild_clock_re()
        await event.edit('🗑️ حذف شد')
        return
    if act == 'reset':
        CUSTOM_FONTS = []
        save_custom_fonts()
        rebuild_clock_re()
        await event.edit(f'🗑️ ریست شد ({len(FONTS)} فونت)')
        return
    if act == 'test':
        tz = timezone(timedelta(hours=3, minutes=30))
        h = datetime.now(tz).hour
        f = get_font_for_hour(h)
        table = {ord(x): y for x, y in zip('0123456789', f['d'])}
        table[ord(':')] = f['c']
        cur = '12:34'.translate(table)
        await event.edit(f'🕐 ساعت {h}: {cur}')
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
            m = re.search(r'(-?\d{5,15})', rmsg.text)
            if m:
                try:
                    uid = int(m.group(1))
                except Exception:
                    pass
    if uid is None:
        await event.edit('❌ /reveal 123456789')
        return
    await event.edit('🔍 شناسایی...')
    try:
        ent = await client.get_entity(uid)
    except Exception as e:
        await event.edit(f'❌ پیدا نشد: {e}')
        return
    fn = getattr(ent, 'first_name', '') or ''
    ln = getattr(ent, 'last_name', '') or ''
    name = (fn + ' ' + ln).strip() or 'بدون نام'
    un = getattr(ent, 'username', None)
    phone = getattr(ent, 'phone', None)
    lines = [f' {name}']
    lines.append(f'🆔 `{ent.id}`')
    if un:
        lines.append(f'🔗 @{un}')
    if phone:
        lines.append(f'📞 +{phone}')
    await client.send_message('me', '\n'.join(lines), parse_mode='md')
    await event.delete()
@client.on(events.NewMessage(pattern=r'^/spamcheck$', chats='me'))
async def spamcheck_cmd(event):
    global SPAM_LOCK
    if SPAM_LOCK:
        await event.edit('⏳ صبر کن')
        return
    SPAM_LOCK = True
    await event.edit('🔍 SpamBot...')
    try:
        await client.send_message('SpamBot', '/start')
        await asyncio.sleep(4)
        msgs = await client.get_messages('SpamBot', limit=4)
        texts = [m.text for m in msgs if m.text and not m.out]
        if texts:
            await event.edit(f'📊\n{texts[0]}')
        else:
            await event.edit('❌ پاسخ نیامد')
    except Exception as e:
        await event.edit(f'❌ {e}')
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
            await client.send_file('me', path, caption=f'📸 {name or "ناشناس"}')
            try:
                os.remove(path)
            except Exception:
                pass
    except Exception:
        pass
@client.on(events.NewMessage(pattern=r'^/ttl\s+(on|off)$', chats='me'))
async def ttl_cmd(event):
    global TTL_SAVE
    TTL_SAVE = (event.pattern_match.group(1) == 'on')
    await event.edit(f'⏳ TTL: {"✅" if TTL_SAVE else "❌"}')
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
    for key, rule in list(CLICKS.items()):
        if rule.get('chat') in (cid, '*'):
            for row in event.message.buttons:
                for btn in row:
                    if rule['text'] in (btn.text or ''):
                        try:
                            await btn.click()
                        except Exception:
                            pass
                        return
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
        if event.media:
            path = await event.download_media()
            await client.send_file('me', path, caption=f'👻 {name or "ناشناس"}\n{event.text or ""}'.strip())
            try:
                os.remove(path)
            except Exception:
                pass
        else:
            await client.send_message('me', f'👻 {name or "ناشناس"}\n{event.text or ""}'.strip())
    except Exception:
        pass
@client.on(events.NewMessage(pattern=r'^/click\s+(add|addh|addany|del|list|on|off|clear|peek)\s*(.*)$', chats='me'))
async def click_cmd(event):
    global CLICK_ON
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    if act == 'on':
        CLICK_ON = True
        await event.edit('🖱️ کلیک: ✅')
        return
    if act == 'off':
        CLICK_ON = False
        await event.edit('️ کلیک: ❌')
        return
    if act == 'peek':
        if LAST_BTN is None:
            await event.edit('❌ دکمه‌ای ندیدم')
            return
        await event.edit(f'👀 {LAST_BTN}\n' + '\n'.join(f'• {t}' for t in LAST_BTN_TEXTS))
        return
    if act == 'clear':
        n = len(CLICKS)
        CLICKS.clear()
        save_clicks()
        await event.edit(f'🧹 {n} مورد پاک شد')
        return
    if act == 'list':
        if not CLICKS:
            await event.edit('️ خالی')
            return
        lines = [f'{k}) {v["chat"]} → «{v["text"]}»' for k, v in CLICKS.items()]
        await event.edit('\n'.join(lines))
        return
    if act == 'addany':
        if not rest:
            await event.edit('❌ /click addany متن')
            return
        key = next_key(CLICKS)
        CLICKS[key] = {'chat': '*', 'text': rest, 'title': 'همه'}
        save_clicks()
        await event.edit(f'🖱️ «{rest}» همه گروه‌ها')
        return
    if act == 'addh':
        if LAST_BTN is None:
            await event.edit('❌ اول peek')
            return
        if not rest:
            await event.edit('❌ /click addh متن')
            return
        key = next_key(CLICKS)
        CLICKS[key] = {'chat': str(LAST_BTN), 'text': rest, 'title': str(LAST_BTN)}
        save_clicks()
        await event.edit(f'🖱️ «{rest}» در {LAST_BTN}')
        return
    if act == 'add':
        tokens = rest.split(maxsplit=1)
        if len(tokens) < 2:
            await event.edit('❌ /click add @group متن')
            return
        target, btext = tokens
        try:
            ent, cid = await resolve_target(target)
        except Exception as e:
            await event.edit(f'❌ {e}')
            return
        key = next_key(CLICKS)
        CLICKS[key] = {'chat': cid, 'text': btext, 'title': getattr(ent, 'title', target)}
        save_clicks()
        await event.edit(f'️ «{btext}» در {CLICKS[key]["title"]}')
        return
    if act == 'del':
        if CLICKS.pop(rest, None) is not None:
            save_clicks()
            await event.edit('🗑️ حذف')
        else:
            await event.edit('❌ نیست')
        return
@client.on(events.NewMessage(pattern=r'^/dl\s*(.*)$', chats='me'))
async def dl_cmd(event):
    arg = (event.pattern_match.group(1) or '').strip()
    msg = None
    if arg:
        m = re.search(r'(?:t|telegram)\.me/(?:c/(\d+)/(\d+)|([^/?#]+)/(\d+))', arg)
        if not m:
            await event.edit('❌ لینک معتبر نیست')
            return
        if m.group(1):
            chat = int('-100' + m.group(1))
        else:
            chat = m.group(3)
        mid = int(m.group(2) or m.group(4))
        try:
            msg = await client.get_messages(chat, ids=mid)
        except Exception as e:
            await event.edit(f'❌ {e}')
            return
    else:
        msg = await event.get_reply_message()
    if msg is None:
        await event.edit('❌ پیام پیدا نشد')
        return
    if not msg.media:
        await event.edit('📭 رسانه نیست')
        return
    await event.edit('⬇️ دانلود...')
    try:
        path = await msg.download_media()
        await client.send_file('me', path, caption=msg.text or '')
        await event.delete()
        try:
            os.remove(path)
        except Exception:
            pass
    except Exception as e:
        await event.edit(f'❌ {e}')
@client.on(events.NewMessage(pattern=r'^/dlast\s+(\S+)(?:\s+(\d+))?$', chats='me'))
async def dlast_cmd(event):
    target = event.pattern_match.group(1)
    count = min(int(event.pattern_match.group(2) or 1), 10)
    await event.edit(f'⬇️ {count} رسانه...')
    try:
        ent = await client.get_entity(int(target) if looks_like_id(target) else target)
    except Exception as e:
        await event.edit(f'❌ {e}')
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
    except Exception:
        pass
    await event.edit(f'✅ {n} رسانه')
@client.on(events.NewMessage(pattern=r'^/getmsg\s+(\S+)\s+(\d+)$', chats='me'))
async def getmsg_cmd(event):
    chat_id = event.pattern_match.group(1)
    msg_id = int(event.pattern_match.group(2))
    await event.edit('️ دریافت...')
    try:
        target = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
        msg = await client.get_messages(target, ids=msg_id)
        if msg is None:
            await event.edit('❌ پیدا نشد')
            return
        if msg.media:
            path = await msg.download_media()
            await client.send_file('me', path, caption=msg.text or f'{chat_id}/{msg_id}')
            try:
                os.remove(path)
            except Exception:
                pass
        else:
            await client.send_message('me', msg.text or '(خالی)')
        await event.delete()
    except Exception as e:
        await event.edit(f'❌ {e}')
@client.on(events.NewMessage(pattern=r'^/auto\s+(add|addc|del|list|on|off|clear)\s*(.*)$', chats='me'))
async def auto_cmd(event):
    global AUTO_ON
    act = event.pattern_match.group(1)
    rest = (event.pattern_match.group(2) or '').strip()
    if act == 'on':
        AUTO_ON = True
        await event.edit(' اتو: ✅')
        return
    if act == 'off':
        AUTO_ON = False
        await event.edit('⏰ اتو: ❌')
        return
    if act == 'clear':
        n = len(AUTOS)
        AUTOS.clear()
        save_autos()
        await event.edit(f'🧹 {n} ردیف')
        return
    if act == 'list':
        if not AUTOS:
            await event.edit('⏰ خالی')
            return
        lines = []
        for k, v in AUTOS.items():
            mins = v.get('interval', 300) // 60
            kind = 'کپی' if v.get('mode') == 'copy' else f'«{v["word"]}»'
            lines.append(f'{k}) {v.get("title", v.get("chat", k))} → {mins}د: {kind}')
        await event.edit('\n'.join(lines))
        return
    if act == 'add':
        tokens = rest.split(maxsplit=2)
        if not tokens:
            await event.edit('📝 /auto add @group [دقیقه] متن')
            return
        target = tokens[0]
        if len(tokens) >= 2 and tokens[1].isdigit():
            minutes = max(1, int(tokens[1]))
            word = tokens[2] if len(tokens) > 2 else ''
        else:
            minutes = 5
            word = ' '.join(tokens[1:])
        if not word:
            await event.edit('❌ متن بده')
            return
        if len(AUTOS) >= 30:
            await event.edit('❌ سقف 30')
            return
        try:
            ent, cid = await resolve_target(target)
        except Exception as e:
            await event.edit(f' {e}')
            return
        key = next_key(AUTOS)
        AUTOS[key] = {'chat': cid, 'mode': 'txt', 'word': word, 'interval': minutes * 60, 'last': 0, 'title': getattr(ent, 'title', target)}
        save_autos()
        await event.edit(f'✅ ردیف {key}')
        return
    if act == 'addc':
        rmsg = await event.get_reply_message()
        if not rmsg:
            await event.edit('❌ ریپلای کن')
            return
        tokens = rest.split()
        if not tokens:
            await event.edit('❌ (ریپلی) /auto addc @group [دقیقه]')
            return
        target = tokens[0]
        minutes = max(1, int(tokens[1])) if len(tokens) > 1 and tokens[1].isdigit() else 5
        if len(AUTOS) >= 30:
            await event.edit('❌ سقف 30')
            return
        try:
            ent, cid = await resolve_target(target)
        except Exception as e:
            await event.edit(f'❌ {e}')
            return
        key = next_key(AUTOS)
        AUTOS[key] = {'chat': cid, 'mode': 'copy', 'mid': rmsg.id, 'interval': minutes * 60, 'last': 0, 'title': getattr(ent, 'title', target)}
        save_autos()
        await event.edit(f'✅ ردیف {key}')
        return
    if act == 'del':
        if rest.isdigit() and rest in AUTOS:
            del AUTOS[rest]
            save_autos()
            await event.edit(f'🗑️ {rest}')
            return
        try:
            ent, cid = await resolve_target(rest)
            removed = [k for k, v in AUTOS.items() if v.get('chat') == cid]
            for k in removed:
                del AUTOS[k]
            if removed:
                save_autos()
                await event.edit(f'🗑️ {len(removed)} ردیف')
            else:
                await event.edit('❌ نبود')
        except Exception:
            await event.edit('❌ درست نیست')
        return
@client.on(events.NewMessage(pattern=r'^/status$', chats='me'))
async def status_cmd(event):
    await event.edit(f'📊 v{BOT_VERSION}\nmaster={MASTER_ON} ghost={GHOST_MODE} clock={CLOCK_ON} names={len(NAMES)} fonts={len(active_fonts())} ttl={TTL_SAVE} banlog={BAN_LOG} pmlog={PMLOG_ON} watch={len(WATCH)} auto={AUTO_ON}({len(AUTOS)}) click={CLICK_ON}({len(CLICKS)}) price={PRICE_ON}')
@client.on(events.NewMessage(pattern=r'^/clock\s+(on|off)$', chats='me'))
async def clock_cmd(event):
    global CLOCK_ON, BASE_LAST
    if event.pattern_match.group(1) == 'on':
        me = await client.get_me()
        BASE_LAST = safe_name_part(CLOCK_RE.sub('', me.last_name or '').strip())
        CLOCK_ON = True
        tz = timezone(timedelta(hours=3, minutes=30))
        h = datetime.now(tz).hour
        font = get_font_for_hour(h)
        t = small_time_with_font(font)
        name_part = safe_name_part(NAMES[h % len(NAMES)] if NAMES else BASE_LAST)
        new_name = f"{name_part} {t}".strip()
        await update_profile_name(new_name)
        await event.edit(f' روشن\n{new_name}')
    else:
        CLOCK_ON = False
        await update_profile_name(BASE_LAST)
        await event.edit('🕐 خاموش')
@client.on(events.NewMessage(pattern=r'^/ping$', chats='me'))
async def ping(event):
    await event.edit('🏓 پونگ')
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
    await event.edit(f'👻 روح: {"✅" if GHOST_MODE else "❌"}')
@client.on(events.NewMessage(pattern=r'^/help$', chats='me'))
async def help_cmd(event):
    await event.edit('''🤖 سلف‌بات v25
🎯 منشن: /rp /m /mwho
💰 قیمت: /price on|off
🕐 ساعت: /clock on|off
📝 اسم: /name add|list|del|reset|test
 فونت: /font list|add|del|reset|test
🔧 عمومی: /bot /ping /status /help
/reveal /common /pmlog /ttl /banlog /ghost
🖱️ کلیک: /click add|addh|addany|peek|del|clear|list|on|off
⏰ اتو: /auto add|addc|del|clear|list|on|off
📥 دانلود: /dl /dlast /getmsg /save /del
🔍 اسپم: /spamcheck''')
async def gen_mode():
    await client.connect()
    if await client.is_user_authorized():
        print('[GEN] already authorized!', flush=True)
        print('[GEN] SESSION_STRING:', client.session.save(), flush=True)
        await client.disconnect()
        return
    h = PHONE_HASH
    code = CODE
    if not code:
        r = await client.send_code_request(PHONE)
        h = r.phone_code_hash
        print('[GEN] CODE SENT to', PHONE, flush=True)
        print('[GEN] PHONE_HASH:', h, flush=True)
        if NTFY_TOPIC:
            print(f'[GEN] منتظر کد هستم... https://ntfy.sh/{NTFY_TOPIC}', flush=True)
            code = await wait_for_code(NTFY_TOPIC, 600)
        if not code:
            print('[GEN] کدی نرسید!', flush=True)
            await client.disconnect()
            return
    try:
        await client.sign_in(PHONE, code, phone_code_hash=h)
    except errors.SessionPasswordNeededError:
        await client.sign_in(password=PASS2)
    print('[GEN] AUTHORIZED!', flush=True)
    print('[GEN] SESSION_STRING:', client.session.save(), flush=True)
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
    if GEN:
        await gen_mode()
        return
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print('[FATAL] لاگین نیست! GEN=1 بگذار و دیپلوی کن.', flush=True)
            return
    except errors.AuthKeyDuplicatedError:
        print('[FATAL] کلید سوخته! WIPE=1 و GEN=1 بگذار.', flush=True)
        return
    load_autos()
    load_clicks()
    load_owners()
    load_watch()
    load_custom_fonts()
    load_names()
    me = await client.get_me()
    ME_ID = me.id
    BASE_LAST = safe_name_part(CLOCK_RE.sub('', me.last_name or '').strip())
    await normalize_stored()
    asyncio.create_task(clock_loop())
    asyncio.create_task(auto_loop())
    asyncio.create_task(probe_loop())
    if PRICE_ON:
        asyncio.create_task(price_loop())
    print(f'🚀 سلف‌بات v{BOT_VERSION} فعال شد!', flush=True)
    print(f'[INIT] WATCH={len(WATCH)} OWNERS={len(OWNERS)} CLICKS={len(CLICKS)} FONTS={len(active_fonts())} NAMES={len(NAMES)}', flush=True)
    while True:
        try:
            await client.run_until_disconnected()
            break
        except errors.AuthKeyDuplicatedError:
            print('[FATAL] کلید سوخته!', flush=True)
            return
        except Exception as e:
            print(f'[MAIN] error: {e} - reconnecting...', flush=True)
            await asyncio.sleep(5)
            try:
                if not client.is_connected():
                    await client.connect()
            except Exception:
                pass
if __name__ == '__main__':
    asyncio.run(main())
