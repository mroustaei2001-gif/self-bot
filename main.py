import asyncio, os, re, json, time, unicodedata, urllib.request, urllib.parse, io
from PIL import Image
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors, types
from telethon.sessions import StringSession
from telethon.utils import get_peer_id
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import GetParticipantsRequest, GetParticipantRequest
from telethon.tl.functions.messages import GetFullChatRequest, UploadMediaRequest
from telethon.tl.functions.stickers import CreateStickerSetRequest, AddStickerToSetRequest
from telethon.tl.types import (
    ChannelParticipantsAdmins, ChannelParticipantCreator, ChatParticipantCreator,
    InputStickerSetShortName, InputStickerSetItem, InputMediaUploadedDocument, DocumentAttributeFilename
)

AI_AVAILABLE = True
BOT_VERSION = '42-FeatureRich'
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
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '9281074111:AAECnfbvDKiOv8CtLHuFJ_1Gl5mvR10eXTA')

PRICE_CHANNEL = os.getenv('PRICE_CHANNEL', '@nerkhonlinechannel')
PRICE_BOT = os.getenv('PRICE_BOT', '@arnaeco_bot')
PRICE_BOT_CMD = os.getenv('PRICE_BOT_CMD', '/start')
PRICE_BOT_BTN = os.getenv('PRICE_BOT_BTN', 'به صورت کلی')
MASTER_ON = True
GHOST_MODE = False
CLOCK_ON = False
BASE_LAST = ''
ME_ID = None
ME_USER = None
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
AI_LOCK = {}
PRICE_ON = os.getenv('PRICE_ON', '1') == '1'
PRICE_INTERVAL = int(os.getenv('PRICE_INTERVAL', '600'))
last_bio = ''
NAMES = []
NAMES_PATH = '/data/names.json'
LAST_MSG_BY_USER = {}
PENDING_MENTION = {}

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

RAW_FONTS = [
    {'d': '⁰¹²³⁴⁵⁶⁷⁸⁹', 'c': 'ː'},
    {'d': '₀₁₂₃₄₅₆₇₈₉', 'c': ':'},
    {'d': '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡', 'c': ':'},
    {'d': '0𝟣𝟤𝟥𝟧𝟨𝟩𝟫', 'c': ':'},
    {'d': '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗', 'c': ':'},
    {'d': '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿', 'c': ':'},
    {'d': '①②③④⑤⑦⑧⑨', 'c': ':'},
    {'d': '0123456789', 'c': ':'},
    {'d': '۰۱۲۳۴۵۶۷۸۹', 'c': ':'},
    {'d': '٠١٢٣٤٥٦٧٨٩', 'c': ':'},
    {'d': '０１۲۳۴۵۶۷۸۹', 'c': '：'},
    {'d': '⓿❶❷❸❹❺❻❼❽❾', 'c': ':'},
    {'d': '𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫', 'c': ':'},
    {'d': '𝟱𝟲𝟳𝟴𝟵𝟬𝟭𝟮𝟯𝟰', 'c': ':'},
    {'d': '➀➁➂➃➄➅➆➇➈➉', 'c': '·'},
    {'d': '⟦0⟧⟦1⟧⟦2⟧⟦3⟧⟦4⟧⟦5⟧⟦6⟧⟦7⟧⟦8⟧⟦9⟧', 'c': ':'},
    {'d': '🄋➀➁➂➃➄➅➆➇➈', 'c': ':'}
]

def validate_font(f):
    if not isinstance(f, dict): return False
    d = f.get('d', ''); c = f.get('c', '')
    if not (isinstance(d, str) and len(d) >= 10 and isinstance(c, str) and len(c) >= 1): return False
    return True

FONTS = [f for f in RAW_FONTS if validate_font(f)]
CUSTOM_FONTS = []
CUSTOM_FONTS_PATH = '/data/fonts.json'
MAX_NAME_LEN = 58

def load_custom_fonts():
    global CUSTOM_FONTS
    try:
        with open(CUSTOM_FONTS_PATH, 'r', encoding='utf-8') as f: loaded = json.load(f)
        valid = [x for x in loaded if validate_font(x)]
        if len(valid) != len(loaded):
            CUSTOM_FONTS = valid; save_custom_fonts()
        else: CUSTOM_FONTS = valid
    except Exception: CUSTOM_FONTS = []

def save_custom_fonts():
    try:
        with open(CUSTOM_FONTS_PATH, 'w', encoding='utf-8') as f: json.dump(CUSTOM_FONTS, f, ensure_ascii=False)
    except Exception: pass

def load_names():
    global NAMES
    if RESET_NAMES: NAMES = []; save_names(); return
    try:
        with open(NAMES_PATH, 'r', encoding='utf-8') as f: NAMES = json.load(f)
        NAMES = [n for n in NAMES if isinstance(n, str) and len(n) > 0]
    except Exception: NAMES = []

def save_names():
    try:
        with open(NAMES_PATH, 'w', encoding='utf-8') as f: json.dump(NAMES, f, ensure_ascii=False)
    except Exception: pass

def visual_len(name):
    name = name or ''
    count = 0
    for ch in name:
        cat = unicodedata.category(ch)
        if cat in ('Zl', 'Zp') or cat[0] in ('M', 'C'): continue
        count += 1
    return count

def safe_name_part(name):
    name = name or ''
    result = []; v_count = 0
    for ch in name:
        cat = unicodedata.category(ch)
        if cat in ('Zl', 'Zp'): continue
        if cat[0] == 'M': result.append(ch); continue
        if cat[0] == 'C': continue
        result.append(ch); v_count += 1
        if v_count >= MAX_NAME_LEN: break
    return ''.join(result)

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
    if not validate_font(font): return time_str
    digits = font['d']
    if len(digits) == 10:
        table = {ord(char): digits[i] for i, char in enumerate('0123456789')}
        table[ord(':')] = font['c']
        return time_str.translate(table)
    return time_str

def fa_now():
    tz = timezone(timedelta(hours=3, minutes=30))
    return datetime.now(tz).strftime('%Y/%m/%d %H:%M')

async def fetch_json(url, timeout=15):
    def _get():
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode('utf-8'))
    return await asyncio.get_running_loop().run_in_executor(None, _get)

async def fetch_text(url, timeout=20):
    def _get():
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.read().decode('utf-8', errors='ignore')
    return await asyncio.get_running_loop().run_in_executor(None, _get)

def _web_search(query, max_results=3):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='ignore')
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
            clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:max_results]]
            if clean_snippets:
                return "\n".join(clean_snippets)
    except Exception:
        pass
    return ""

def _gemini_sync(question, timeout=30):
    cleaned_key = (GEMINI_API_KEY or '').strip().replace('\n', '').replace('\r', '')
    if not cleaned_key:
        return '❌ کلید API در تنظیمات ریل‌وی تنظیم نشده است.'

    web_context = _web_search(question)
    system_prompt = (
        "You are an up-to-date, highly accurate AI assistant. "
        "Use the provided recent web search results to answer current events, rosters, and news accurately. "
        "Always reply concisely in Persian."
    )
    if web_context:
        system_prompt += f"\n\nRecent Web Search Information:\n{web_context}"

    active_free_models = []
    try:
        req_models = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req_models, timeout=10) as r:
            m_data = json.loads(r.read().decode('utf-8'))
            for item in m_data.get('data', []):
                mid = item.get('id', '')
                pricing = item.get('pricing', {})
                if ':free' in mid or (pricing.get('prompt') == '0' and pricing.get('completion') == '0'):
                    active_free_models.append(mid)
    except Exception:
        pass

    fallback_models = [
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ]
    models_to_test = active_free_models[:5] if active_free_models else fallback_models

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {cleaned_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://railway.app',
        'X-Title': 'Telegram SelfBot'
    }

    last_error = ""
    for model_name in models_to_test:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                choices = res_json.get('choices', [])
                if choices:
                    msg = choices[0].get('message', {}).get('content', '')
                    if msg: return msg.strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            last_error = f"{e.code}: {err_body[:100]}"
            continue
        except Exception as e:
            last_error = str(e)[:100]
            continue

    return f'❌ خطا در ارتباط: {last_error}'

async def ask_ai(question, timeout=40):
    try:
        resp = await asyncio.get_running_loop().run_in_executor(None, _gemini_sync, question, timeout)
        resp = (resp or '').strip()
        if len(resp) > 3900: resp = resp[:3900] + '\n...(بریده شد)'
        return resp
    except Exception as e:
        return f'❌ خطا در تسک AI: {str(e)[:150]}'

def _fa_to_en(txt):
    return txt.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))

def parse_price_text(txt):
    res = {'usd': None, 'btc_usd': None, 'gold_gram': None, 'gold_oz': None}
    txt = _fa_to_en(txt or '')
    m = re.search(r'دلار[^0-9]{0,80}?([0-9][0-9,\.]{3,})', txt)
    if m:
        v = int(m.group(1).replace(',', '').replace('.', ''))
        if 50000 <= v <= 2000000: res['usd'] = v
    m = re.search(r'(?:بیت\s?کوین|بیتکوین|BTC)[^0-9]{0,80}?([0-9][0-9,\.]{3,})', txt)
    if m:
        raw = float(m.group(1).replace(',', ''))
        if 1000 <= raw < 1000000: res['btc_usd'] = raw
        elif res['usd'] and raw >= 1000000: res['btc_usd'] = raw / res['usd']
    m = re.search(r'(?:طلای\s?18|18\s?عیار|عیار\s?18)[^0-9]{0,80}?([0-9][0-9,\.]{3,})', txt)
    if m:
        v = int(m.group(1).replace(',', '').replace('.', ''))
        if 500000 <= v <= 500000000: res['gold_gram'] = v
    if not res['gold_gram']:
        m = re.search(r'(?:انس|اونس|XAU)[^0-9]{0,80}?([0-9][0-9,\.]{3,})', txt)
        if m:
            v = float(m.group(1).replace(',', ''))
            if 200 <= v <= 100000: res['gold_oz'] = v
    return res

async def get_channel_prices():
    res = {'usd': None, 'btc_usd': None, 'gold_gram': None, 'gold_oz': None}
    if PRICE_BOT:
        try:
            ent = await client.get_entity(PRICE_BOT)
            await client.send_message(ent, PRICE_BOT_CMD)
            await asyncio.sleep(4)
            if PRICE_BOT_BTN:
                clicked = False
                for mg in await client.get_messages(ent, limit=4):
                    if mg.buttons:
                        for row in mg.buttons:
                            for btn in row:
                                if PRICE_BOT_BTN in (btn.text or ''):
                                    await btn.click(); clicked = True; break
                            if clicked: break
                    if clicked: break
            await asyncio.sleep(4)
            for mg in await client.get_messages(ent, limit=5):
                r = parse_price_text(mg.text)
                for k in res:
                    if res[k] is None and r.get(k): res[k] = r[k]
        except Exception: pass
    try:
        async for mg in client.iter_messages(PRICE_CHANNEL, limit=10):
            r = parse_price_text(mg.text)
            for k in res:
                if res[k] is None and r.get(k): res[k] = r[k]
            if res['usd'] and res['btc_usd'] and res['gold_gram']: break
    except Exception: pass
    return res

async def get_usd_toman():
    try:
        d = await fetch_json('https://api.navasan.tech/latest/?api_key=free&base=usd&to=irr', timeout=10)
        if d.get('usd') and d['usd'].get('price'): return int(float(d['usd']['price'])), 'آزاد'
    except Exception: pass
    try:
        d = await fetch_json('https://alanchand.com/api/v1/prices', timeout=10)
        if d.get('usd') and d['usd'].get('price'): return int(d['usd']['price']), 'آزاد'
    except Exception: pass
    return None, None

async def get_btc_usd():
    try:
        d = await fetch_json('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', timeout=10)
        if d.get('bitcoin') and d['bitcoin'].get('usd'): return float(d['bitcoin']['usd'])
    except Exception: pass
    return None

async def get_gold_oz_usd():
    try:
        d = await fetch_json('https://api.gold-api.com/price/XAU', timeout=10)
        return float(d['price'])
    except Exception: pass
    return None

def slash_fmt(n):
    if n is None: return '—'
    return f'{int(round(n)):,}'.replace(',', '،')

async def build_bio():
    ch = await get_channel_prices()
    usd_toman = ch['usd']
    if not usd_toman: usd_toman, _ = await get_usd_toman()
    btc_usd = ch['btc_usd']
    if not btc_usd: btc_usd = await get_btc_usd()
    gold_gram = ch['gold_gram']
    gold_oz = ch.get('gold_oz')
    if not gold_gram:
        if not gold_oz: gold_oz = await get_gold_oz_usd()
        if gold_oz and usd_toman: gold_gram = (gold_oz / 31.1035) * 0.75 * usd_toman
    
    parts = []
    if usd_toman: parts.append(f'💵 دلار: {slash_fmt(usd_toman)}')
    if btc_usd: parts.append(f'🪙 بیت: ${int(round(btc_usd)):,}')
    if gold_gram: parts.append(f'🪙 طلا: {slash_fmt(gold_gram)}')
    
    bio = ' | '.join(parts)
    return bio if bio else None

async def update_bio(new_bio):
    global last_bio
    if new_bio == last_bio: return True
    for attempt in range(3):
        try:
            await client(UpdateProfileRequest(about=new_bio)); last_bio = new_bio; return True
        except errors.FloodWaitError as e: await asyncio.sleep(e.seconds + 1)
        except Exception: await asyncio.sleep(2)
    return False

async def price_loop():
    while True:
        try:
            if PRICE_ON and MASTER_ON:
                bio = await build_bio()
                if bio:
                    bio = bio[:70]
                    await update_bio(bio)
        except Exception: pass
        await asyncio.sleep(PRICE_INTERVAL)

async def wait_for_code(topic, timeout=600):
    since = int(time.time()); deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            txt = await fetch_text(f'https://ntfy.sh/{topic}/json?poll=1&since={since}')
            for line in txt.strip().splitlines():
                if not line.strip(): continue
                try: obj = json.loads(line)
                except Exception: continue
                since = max(since, obj.get('time', since) + 1)
                msg = (obj.get('message') or '').strip()
                if msg.isdigit() and len(msg) >= 4: return msg
        except Exception: pass
        await asyncio.sleep(3)
    return None

def load_autos():
    global AUTOS
    try:
        with open(AUTOS_PATH, 'r', encoding='utf-8') as f: AUTOS = json.load(f)
    except Exception: AUTOS = {}
    for k, v in list(AUTOS.items()):
        if 'chat' not in v: v['chat'] = k

def save_autos():
    try:
        with open(AUTOS_PATH, 'w', encoding='utf-8') as f: json.dump(AUTOS, f, ensure_ascii=False)
    except Exception: pass

def load_clicks():
    global CLICKS
    try:
        with open(CLICKS_PATH, 'r', encoding='utf-8') as f: CLICKS = json.load(f)
    except Exception: CLICKS = {}

def save_clicks():
    try:
        with open(CLICKS_PATH, 'w', encoding='utf-8') as f: json.dump(CLICKS, f, ensure_ascii=False)
    except Exception: pass

def load_owners():
    global OWNERS
    try:
        with open(OWNERS_PATH, 'r', encoding='utf-8') as f: OWNERS = json.load(f)
    except Exception: OWNERS = {}

def save_owners():
    try:
        with open(OWNERS_PATH, 'w', encoding='utf-8') as f: json.dump(OWNERS, f, ensure_ascii=False)
    except Exception: pass

def load_watch():
    global WATCH
    try:
        with open(WATCH_PATH, 'r', encoding='utf-8') as f: WATCH = set(json.load(f))
    except Exception: WATCH = set()

def save_watch():
    try:
        with open(WATCH_PATH, 'w', encoding='utf-8') as f: json.dump(list(WATCH), f)
    except Exception: pass

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
                    v['chat'] = str(get_peer_id(ent)); changed = True
                except Exception: pass
    if changed: save_autos(); save_clicks()

async def update_profile_name(new_name):
    for attempt in range(3):
        try:
            await client(UpdateProfileRequest(last_name=new_name)); return True
        except errors.FloodWaitError as e: await asyncio.sleep(e.seconds + 1)
        except Exception: await asyncio.sleep(2)
    return False

async def clock_loop():
    last_time = ''; last_minute = -1
    while True:
        try:
            if CLOCK_ON and MASTER_ON:
                tz = timezone(timedelta(hours=3, minutes=30)); now = datetime.now(tz); minute = now.minute
                if minute != last_minute:
                    hour = now.hour; font = get_font_for_hour(hour); t = small_time_with_font(font)
                    name_part = safe_name_part(NAMES[hour % len(NAMES)]) if NAMES else safe_name_part(BASE_LAST)
                    new_name = f"{name_part} {t}".strip()
                    if new_name != last_time:
                        ok = await update_profile_name(new_name)
                        if ok: last_time = new_name; last_minute = minute
            else: last_minute = -1; last_time = ''
        except Exception: pass
        await asyncio.sleep(5)

async def probe_loop():
    while True:
        await asyncio.sleep(120)
        if ME_ID is None or not MASTER_ON: continue
        for cid in list(WATCH):
            if cid == ME_ID: WATCH.discard(cid); continue
            try:
                ent = await client.get_entity(cid)
                if not (getattr(ent, 'channel', False) or getattr(ent, 'megagroup', False) or getattr(ent, 'broadcast', False)): continue
                inp = getattr(ent, 'input_channel', None)
                if inp is None: continue
                res = await client(GetParticipantRequest(inp, types.InputUserSelf()))
                part = getattr(res, 'participant', None)
                if isinstance(part, types.ChannelParticipantBanned):
                    kicked = getattr(part, 'kicked_by', None)
                    await log_ban(cid, kicked, None); WATCH.discard(cid); save_watch()
            except errors.UserNotParticipantError:
                last = LAST_SEEN.get(cid, 0)
                if last > 0 and time.time() - last < 12 * 3600: await log_ban(cid, None, None)
                WATCH.discard(cid); save_watch()
            except errors.ChannelPrivateError: WATCH.discard(cid); save_watch()
            except errors.FloodWaitError as e: await asyncio.sleep(e.seconds + 1)
            except Exception: pass
            await asyncio.sleep(0.3)

async def auto_loop():
    while True:
        try:
            if AUTO_ON and MASTER_ON:
                now = time.time()
                for key, item in list(AUTOS.items()):
                    cid = item.get('chat', key); iv = item.get('interval', 300)
                    if now - item.get('last', 0) >= iv:
                        try:
                            if item.get('mode') == 'copy':
                                src = await client.get_messages('me', ids=item['mid'])
                                if src is None: raise Exception('source not found')
                                await client.send_message(int(cid), message=src.text, file=src.media)
                            else: await client.send_message(int(cid), item['word'])
                            item['last'] = now; save_autos()
                        except (errors.UserBannedInChannelError, errors.ChatWriteForbiddenError):
                            del AUTOS[key]; save_autos()
                            try: await log_ban(int(cid), None, None)
                            except Exception: pass
                        except errors.FloodWaitError as e: await asyncio.sleep(e.seconds + 1)
                        except Exception: del AUTOS[key]; save_autos()
        except Exception: pass
        await asyncio.sleep(20)

def looks_like_id(s): return bool(s) and s.startswith('-') and s[1:].isdigit()

async def resolve_target(target):
    if looks_like_id(target): ent = await client.get_entity(int(target))
    else: ent = await client.get_entity(target)
    return ent, str(get_peer_id(ent))

async def cache_owner(cid):
    if str(cid) in OWNERS: return
    ent = await client.get_entity(cid)
    title = getattr(ent, 'title', None) or getattr(ent, 'first_name', None) or str(cid)
    owner_id = None
    try:
        if getattr(ent, 'channel', False) or getattr(ent, 'megagroup', False) or getattr(ent, 'broadcast', False):
            res = await client(GetParticipantsRequest(ent, ChannelParticipantsAdmins(), 0, 100, 0))
            for p in res.participants:
                if isinstance(p, ChannelParticipantCreator): owner_id = p.user_id; break
        else:
            full = await client(GetFullChatRequest(cid))
            for p in full.full_chat.participants.participants:
                if isinstance(p, ChatParticipantCreator): owner_id = p.user_id; break
    except Exception: pass
    if owner_id:
        try:
            u = await client.get_entity(owner_id)
            OWNERS[str(cid)] = {'owner_id': owner_id, 'owner_name': ((getattr(u, 'first_name', '') or '') + ' ' + (getattr(u, 'last_name', '') or '')).strip(), 'owner_username': getattr(u, 'username', None), 'title': title}
            save_owners()
        except Exception: pass

@client.on(events.NewMessage(incoming=True))
async def owner_cacher(event):
    cid = event.chat_id
    if cid != ME_ID: WATCH.add(cid); save_watch(); LAST_SEEN[cid] = time.time()
    if cid in TRIED_OWNERS or str(cid) in OWNERS: return
    TRIED_OWNERS.add(cid)
    try: await cache_owner(cid)
    except Exception: pass

@client.on(events.NewMessage(outgoing=True))
async def watch_outgoing(event):
    cid = event.chat_id
    if cid != ME_ID: WATCH.add(cid); save_watch(); LAST_SEEN[cid] = time.time()

@client.on(events.NewMessage(incoming=True))
async def track_last_msg(event):
    if not MASTER_ON: return
    cid = event.chat_id; sender = await event.get_sender()
    if not sender or not sender.id or sender.id == ME_ID: return
    LAST_MSG_BY_USER[(cid, sender.id)] = event.message

@client.on(events.NewMessage(incoming=True))
async def pm_cache(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None: return
    if not event.is_private or event.chat_id == ME_ID: return
    sender = await event.get_sender()
    if getattr(sender, 'bot', False): return
    name = ((getattr(sender, 'first_name', '') or '') + ' ' + (getattr(sender, 'last_name', '') or '')).strip()
    PM_CACHE[(event.chat_id, event.id)] = {'text': event.text or '', 'name': name or 'ناشناس', 'media': bool(event.media)}
    if len(PM_CACHE) > 3000:
        for k in list(PM_CACHE.keys())[:500]: PM_CACHE.pop(k, None)

@client.on(events.MessageEdited(incoming=True))
async def pm_edit_logger(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None: return
    if not event.is_private or event.chat_id == ME_ID: return
    sender = await event.get_sender()
    if getattr(sender, 'bot', False): return
    key = (event.chat_id, event.id); old = PM_CACHE.get(key, {})
    old_text = old.get('text', '(نامشخص)'); name = old.get('name', 'ناشناس')
    PM_CACHE[key] = {'text': event.text or '', 'name': name, 'media': bool(event.media)}
    try: await client.send_message('me', f'✏️ ادیت در پی‌وی: {name}\nقبلی: {old_text}\nجدید: {event.text or ""}', parse_mode='md')
    except Exception: pass

@client.on(events.MessageDeleted)
async def pm_delete_logger(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None: return
    chat_id = getattr(event, 'chat_id', None)
    if chat_id is None: return
    for mid in getattr(event, 'deleted_ids', []):
        key = (chat_id, mid); rec = PM_CACHE.pop(key, None)
        if rec:
            try: await client.send_message('me', f'🗑️ حذف در پی‌وی: {rec["name"]}\n{rec["text"] or "(خالی)"}', parse_mode='md')
            except Exception: pass

async def log_ban(chat_id, admin_id, chat_title=None):
    if not BAN_LOG: return
    key = str(chat_id); now = time.time()
    if now - BAN_DEDUPE.get(key, 0) < 120: return
    BAN_DEDUPE[key] = now
    try: admin = await client.get_entity(admin_id) if admin_id else None
    except Exception: admin = None
    try:
        if chat_title is None:
            chat = await client.get_entity(int(chat_id))
            chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', str(chat_id))
    except Exception: chat_title = str(chat_id)
    own = OWNERS.get(str(chat_id))
    lines = [f'🚨 بن/حذف شدی در: {chat_title}']
    if admin:
        fn = getattr(admin, 'first_name', '') or ''; ln = getattr(admin, 'last_name', '') or ''
        lines.append(f'👤 بن‌کننده: {(fn+" "+ln).strip() or "بدون نام"}')
        lines.append(f'🆔 ID: `{admin.id}`')
        if getattr(admin, 'username', None): lines.append(f'🔗 @{admin.username}')
    if own:
        lines.append(f'👑 مالک: {own["owner_name"] or "بدون نام"}')
        lines.append(f'🆔 ID: `{own["owner_id"]}`')
        if own.get('owner_username'): lines.append(f'🔗 @{own["owner_username"]}')
    lines.append(f'⏰ {fa_now()}')
    try: await client.send_message('me', '\n'.join(lines), parse_mode='md')
    except Exception: pass

@client.on(events.Raw(types.UpdateChannelParticipant))
async def raw_ban_detector(event):
    if ME_ID is None or not MASTER_ON: return
    try:
        if event.user_id != ME_ID: return
        np = event.new_participant
        if not isinstance(np, types.ChannelParticipantBanned): return
        br = getattr(np, 'banned_rights', None)
        if br is None or not br.view_messages: return
        cid = get_peer_id(types.PeerChannel(event.channel_id))
        actor = getattr(event, 'actor_id', None)
        await log_ban(cid, actor, None)
    except Exception: pass

@client.on(events.ChatAction())
async def ban_detector(event):
    if ME_ID is None or not MASTER_ON: return
    try:
        ids = getattr(event, 'user_id', None) or []
        if isinstance(ids, int): ids = [ids]
        if ME_ID not in ids: return
        if event.user_joined or event.user_added: return
        admin_id = None
        try:
            am = event.action_message
            if am is not None and getattr(am, 'from_id', None) is not None: admin_id = getattr(am.from_id, 'user_id', None)
        except Exception: admin_id = None
        await log_ban(event.chat_id, admin_id, None)
    except Exception: pass

RESERVED_COMMANDS = {'/rp', '/m', '/mwho', '/bot', '/common', '/name', '/banlog', '/pmlog', '/font', '/reveal', '/spamcheck', '/ttl', '/click', '/dl', '/dlast', '/getmsg', '/auto', '/status', '/clock', '/price', '/ping', '/save', '/del', '/ghost', '/help', '/ask', '/type', '/hack', '/hearts', '/moon', '/timer', '/userinfo', '/kang'}

async def send_mention_message(chat_id, text, uid):
    try:
        url = f"tg://user?id={int(uid)}"
        await client.send_message(chat_id, f"{text} {url}")
        return True
    except Exception: return False

@client.on(events.NewMessage(outgoing=True))
async def smart_rp_handler(event):
    try:
        msg = event.message; text = msg.text; chat_id = event.chat_id
        if not text: return
        clean_text = text.strip()
        if clean_text.startswith('**') and clean_text.endswith('**'): clean_text = clean_text[2:-2].strip()
        first_word = clean_text.split()[0].lower() if clean_text else ''
        is_reserved = first_word in RESERVED_COMMANDS
        if clean_text == '/':
            reply_to_id = msg.reply_to_msg_id
            if not reply_to_id:
                await msg.delete(revoke=True); return
            original_msg = await client.get_messages(chat_id, ids=reply_to_id)
            if not original_msg:
                await msg.delete(revoke=True); return
            sender = await original_msg.get_sender()
            if not sender or not sender.id:
                await msg.delete(revoke=True); return
            PENDING_MENTION[chat_id] = {'uid': sender.id}
            await msg.delete(revoke=True); return
        if chat_id in PENDING_MENTION:
            if is_reserved:
                del PENDING_MENTION[chat_id]
                return
            uid = PENDING_MENTION[chat_id]['uid']; del PENDING_MENTION[chat_id]
            await msg.delete(revoke=True); await send_mention_message(chat_id, clean_text, uid); return
        if is_reserved: return
        if clean_text.startswith('/') and msg.reply_to_msg_id:
            rp_text = clean_text[1:].strip()
            if rp_text:
                original_msg = await client.get_messages(chat_id, ids=msg.reply_to_msg_id)
                if original_msg:
                    sender = await original_msg.get_sender()
                    if sender and sender.id:
                        await msg.delete(revoke=True); await send_mention_message(chat_id, rp_text, sender.id); return
    except errors.ChatWriteForbiddenError: pass
    except Exception:
        if event.chat_id in PENDING_MENTION: del PENDING_MENTION[event.chat_id]

# --- بخش هوش مصنوعی ---
@client.on(events.NewMessage(pattern=r'^/ask(?:\s+([\s\S]*))?$', outgoing=True))
async def ask_cmd(event):
    question = (event.pattern_match.group(1) or '').strip()
    rmsg = await event.get_reply_message()
    if not question and rmsg:
        question = (rmsg.text or '').strip()
    if not question:
        try: await event.edit('❌ سوالی مطرح نکردید.\nمثال: `/ask پایتخت ایتالیا کجاست؟`', parse_mode='md')
        except Exception: pass
        return
    
    cid = event.chat_id
    if cid in AI_LOCK:
        try: await event.edit('⏳ در حال پاسخگویی به درخواست قبلی...')
        except Exception: pass
        return
    
    AI_LOCK[cid] = True
    try: await event.edit('🤖 *در حال جستجو و پردازش پاسخ...*', parse_mode='md')
    except Exception: pass

    try:
        resp = await ask_ai(question)
        full_text = f"🤖 **پاسخ هوش مصنوعی:**\n\n{resp}"
        chunks = [full_text[i:i+3800] for i in range(0, len(full_text), 3800)]
        try:
            await event.edit(chunks[0], parse_mode='md')
            for extra in chunks[1:]:
                await asyncio.sleep(1)
                await client.send_message(cid, extra, parse_mode='md')
        except Exception:
            await client.send_message(cid, full_text, reply_to=rmsg.id if rmsg else None)
    except Exception as e:
        try: await event.edit(f'❌ خطا در پردازش: {str(e)[:150]}')
        except Exception: pass
    finally:
        AI_LOCK.pop(cid, None)

# --- دستورات فان و متحرک ---
@client.on(events.NewMessage(pattern=r'^/type(?:\s+([\s\S]+))?$', outgoing=True))
async def type_cmd(event):
    text = event.pattern_match.group(1)
    if not text:
        rmsg = await event.get_reply_message()
        if rmsg and rmsg.text: text = rmsg.text
    if not text:
        await event.edit('❌ متنی برای تایپ ننوشتید.'); return
    typing_symbol = '▒'
    current_text = ''
    for char in text:
        current_text += char
        try:
            await event.edit(current_text + typing_symbol)
            await asyncio.sleep(0.08)
        except Exception:
            await asyncio.sleep(0.2)
    try: await event.edit(text)
    except Exception: pass

@client.on(events.NewMessage(pattern=r'^/hack$', outgoing=True))
async def hack_cmd(event):
    rmsg = await event.get_reply_message()
    target_name = "هدف"
    if rmsg:
        sender = await rmsg.get_sender()
        if sender:
            target_name = getattr(sender, 'first_name', '') or str(sender.id)
    steps = [
        f"💻 [0%] در حال اتصال به دیتابیس تلگرام {target_name}...",
        f"🔍 [20%] دور زدن فایروال و رمز دوم...",
        f"📥 [45%] استخراج پیام‌ها، عکس‌ها و نشست‌های فعال...",
        f"⚙️ [75%] انتقال دسترسی به سرور ریل‌وی...",
        f"⚠️ [95%] پاک‌سازی لاگ‌ها و ردپاها...",
        f"💀 **[100%] دسترسی کامل به اکانت {target_name} برقرار شد!**"
    ]
    for step in steps:
        try:
            await event.edit(step, parse_mode='md')
            await asyncio.sleep(0.9)
        except Exception: pass

@client.on(events.NewMessage(pattern=r'^/hearts$', outgoing=True))
async def hearts_cmd(event):
    hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤍", "🤎", "🖤", "💖"]
    for h in hearts:
        try:
            await event.edit(h)
            await asyncio.sleep(0.4)
        except Exception: pass
    try: await event.edit("❤️‍🔥")
    except Exception: pass

@client.on(events.NewMessage(pattern=r'^/moon$', outgoing=True))
async def moon_cmd(event):
    phases = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑", "✨ Good Night ✨"]
    for p in phases:
        try:
            await event.edit(p)
            await asyncio.sleep(0.4)
        except Exception: pass

# --- تایمر و شمارشگر معکوس ---
@client.on(events.NewMessage(pattern=r'^/timer\s+(\d+)$', outgoing=True))
async def timer_cmd(event):
    secs = int(event.pattern_match.group(1))
    if secs > 300:
        await event.edit('⚠️ حداکثر زمان تایمر ۳۰۰ ثانیه است.'); return
    while secs > 0:
        m, s = divmod(secs, 60)
        try:
            await event.edit(f"⏳ **تایمر معکوس:** `{m:02d}:{s:02d}`", parse_mode='md')
            await asyncio.sleep(1)
            secs -= 1
        except Exception:
            await asyncio.sleep(2)
    try: await event.edit("⏰ **زمان به پایان رسید!**", parse_mode='md')
    except Exception: pass

# --- اطلاعات دقیق و جامع کاربر ---
@client.on(events.NewMessage(pattern=r'^/userinfo(?:\s+(\S+))?$', outgoing=True))
async def userinfo_cmd(event):
    arg = event.pattern_match.group(1)
    user = None
    if arg:
        try: user = await client.get_entity(int(arg) if arg.lstrip('-').isdigit() else arg)
        except Exception as e: await event.edit(f'❌ کاربر یافت نشد: {e}'); return
    else:
        rmsg = await event.get_reply_message()
        if rmsg: user = await rmsg.get_sender()
    if not user:
        await event.edit('❌ لطفاً روی یک پیام ریپلای کنید یا آیدی کاربر را وارد نمایید.'); return

    await event.edit('🔍 در حال دریافت اطلاعات...')
    fn = getattr(user, 'first_name', '') or ''
    ln = getattr(user, 'last_name', '') or ''
    un = f"@{user.username}" if getattr(user, 'username', None) else "ندارد"
    uid = user.id
    is_bot = "بله 🤖" if getattr(user, 'bot', False) else "خیر 👤"
    is_scam = "بله ⚠️" if getattr(user, 'scam', False) else "خیر ✅"
    dc_id = getattr(user.photo, 'dc_id', 'نامشخص') if getattr(user, 'photo', None) else 'فاقد عکس'

    info = f"""👤 **اطلاعات کاربر:**
▫️ **نام:** {fn} {ln}
▫️ **یوزرنیم:** {un}
▫️ **آیدی عددی:** `{uid}`
▫️ **دیتاسنتر (DC):** `{dc_id}`
▫️ **ربات:** {is_bot}
▫️ **نشان اسکَم (Scam):** {is_scam}
▫️ **لینک دائمی:** [پروفایل](tg://user?id={uid})"""
    await event.edit(info, parse_mode='md')

# --- استیکرساز سریع (Kang) ---
# --- استیکرساز سریع (Kang) ---
# --- استیکرساز سریع و استاندارد (Kang) ---
@client.on(events.NewMessage(pattern=r'^/kang(?:\s+([\s\S]+))?$', outgoing=True))
async def kang_cmd(event):
    emoji = (event.pattern_match.group(1) or '🤔').strip()
    rmsg = await event.get_reply_message()
    if not rmsg or not rmsg.media:
        await event.edit('❌ لطفاً روی یک عکس، میم یا استیکر ریپلای کنید.'); return
    await event.edit('🎨 در حال تغییر ابعاد و ساخت استیکر استاندارد...')
    try:
        photo_bytes = await rmsg.download_media(file=bytes)
        if not photo_bytes:
            await event.edit('❌ دریافت فایل انجام نشد.'); return

        # تغییر سایز استاندارد به حداکثر 512 پیکسل با حفظ نسبت ابعاد
        image = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
        max_size = 512
        w, h = image.size
        scale = max_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # تبدیل به بایت‌های PNG
        output_io = io.BytesIO()
        image.save(output_io, format="PNG")
        resized_bytes = output_io.getvalue()

        # نام و مشخصات پک کاربری
        pack_name = f"kang_{ME_ID}_v1_by_{ME_USER}" if ME_USER else f"kang_{ME_ID}_v1"
        pack_title = f"@{ME_USER or 'My'} Kang Pack"

        file = await client.upload_file(resized_bytes)
        doc = InputMediaUploadedDocument(
            file=file,
            mime_type='image/png',
            attributes=[DocumentAttributeFilename('sticker.png')]
        )
        res = await client(UploadMediaRequest(peer=types.InputPeerSelf(), media=doc))
        doc_item = types.InputDocument(
            id=res.document.id,
            access_hash=res.document.access_hash,
            file_reference=res.document.file_reference
        )

        try:
            await client(AddStickerToSetRequest(
                stickerset=InputStickerSetShortName(short_name=pack_name),
                sticker=InputStickerSetItem(document=doc_item, emoji=emoji)
            ))
            await event.edit(f'✅ به پک اضافه شد!\n🔗 https://t.me/addstickers/{pack_name}')
        except errors.StickersetInvalidError:
            await client(CreateStickerSetRequest(
                user_id=types.InputUserSelf(),
                title=pack_title,
                short_name=pack_name,
                stickers=[InputStickerSetItem(document=doc_item, emoji=emoji)]
            ))
            await event.edit(f'🎉 پک استیکر ساخته و استیکر اضافه شد!\n🔗 https://t.me/addstickers/{pack_name}')
    except Exception as e:
        await event.edit(f'❌ خطا در ساخت استیکر: {str(e)[:150]}')

# --- سایر دستورات سلف‌بات ---
@client.on(events.NewMessage(pattern=r'^/price\s+(on|off)$', chats='me'))
async def price_cmd(event):
    global PRICE_ON
    PRICE_ON = (event.pattern_match.group(1) == 'on')
    if PRICE_ON:
        bio = await build_bio()
        if bio: await update_bio(bio[:70])
        await event.edit(f'💰 قیمت‌ها: روشن ✅\n{bio[:70] if bio else "—"}')
    else:
        await update_bio('')
        await event.edit('💰 قیمت‌ها: خاموش ❌')

@client.on(events.NewMessage(pattern=r'^/rp\s*(.*)$', chats='me'))
async def rp_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text: await event.edit('❌ /rp متن'); return
    rmsg = await event.get_reply_message()
    if not rmsg: await event.edit('❌ ریپلای کن'); return
    sender = await rmsg.get_sender()
    if not sender or not sender.id: await event.edit('❌ فرستنده پیدا نشد'); return
    await send_mention_message(event.chat_id, text, sender.id)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^/m\s*(.*)$', chats='me'))
async def m_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text: await event.edit('❌ /m متن'); return
    cid = event.chat_id
    if cid == ME_ID: await event.edit('❌ فقط در گروه'); return
    target = None
    for (chat_id, user_id), msg in LAST_MSG_BY_USER.items():
        if chat_id == cid and user_id != ME_ID: target = (user_id, msg); break
    if target is None: await event.edit('❌ هنوز پیامی ندیدم'); return
    uid, msg = target
    await send_mention_message(cid, text, uid)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^/mwho$', chats='me'))
async def mwho_cmd(event):
    cid = event.chat_id
    if cid == ME_ID: await event.edit('❌ فقط در گروه'); return
    found = []
    for (chat_id, user_id), msg in list(LAST_MSG_BY_USER.items()):
        if chat_id == cid and user_id != ME_ID:
            sender = await msg.get_sender()
            fn = getattr(sender, 'first_name', '') or ''; ln = getattr(sender, 'last_name', '') or ''; uname = getattr(sender, 'username', None)
            name = (fn + ' ' + ln).strip() or 'بدون نام'
            found.append((user_id, name, uname))
    if not found: await event.edit('📭 کسی پیام نداده'); return
    lines = ['👥 آخرین فرستندگان:']
    for uid, name, un in found[:10]:
        un_str = f' @{un}' if un else ''
        lines.append(f'• {name}{un_str} (`{uid}`)')
    await event.edit('\n'.join(lines), parse_mode='md')

@client.on(events.NewMessage(pattern=r'^/bot\s+(on|off)$', chats='me'))
async def bot_cmd(event):
    global MASTER_ON
    MASTER_ON = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🤖 سلف‌بات: {"روشن ✅" if MASTER_ON else "خاموش ❌"}')

@client.on(events.NewMessage(pattern=r'^/status$', chats='me'))
@client.on(events.NewMessage(pattern=r'^/status$', chats='me'))
async def status_cmd(event):
    active_fonts_count = len(CUSTOM_FONTS) if CUSTOM_FONTS else len(FONTS)
    names_count = len(NAMES) if NAMES else 0
    auto_count = len(AUTOS)
    click_count = len(CLICKS)
    watch_count = len(WATCH)
    
    text = (
        f"📊 v{BOT_VERSION}\n"
        f"master={MASTER_ON} ghost={GHOST_MODE} clock={CLOCK_ON} "
        f"names={names_count} fonts={active_fonts_count} "
        f"ttl={TTL_SAVE} banlog={BAN_LOG} pmlog={PMLOG_ON} "
        f"watch={watch_count} auto={AUTO_ON}({auto_count}) "
        f"click={CLICK_ON}({click_count}) price={PRICE_ON} ai={AI_AVAILABLE}\n"
        f"📡 bot={PRICE_BOT} channel={PRICE_CHANNEL}"
    )
    await event.edit(text)

@client.on(events.NewMessage(pattern=r'^/clock\s+(on|off)$', chats='me'))
async def clock_cmd(event):
    global CLOCK_ON, BASE_LAST
    if event.pattern_match.group(1) == 'on':
        me = await client.get_me()
        BASE_LAST = safe_name_part(CLOCK_RE.sub('', me.last_name or '').strip())
        CLOCK_ON = True
        tz = timezone(timedelta(hours=3, minutes=30)); h = datetime.now(tz).hour
        font = get_font_for_hour(h); t = small_time_with_font(font)
        name_part = safe_name_part(NAMES[h % len(NAMES)] if NAMES else BASE_LAST)
        new_name = f"{name_part} {t}".strip()
        await update_profile_name(new_name)
        await event.edit(f'🕐 ساعت فعال شد:\n{new_name}')
    else:
        CLOCK_ON = False; await update_profile_name(BASE_LAST); await event.edit('🕐 ساعت خاموش شد')

@client.on(events.NewMessage(pattern=r'^/ping$', chats='me'))
async def ping(event): await event.edit('🏓 پونگ')

@client.on(events.NewMessage(pattern=r'^/save$', chats='me'))
async def save(event):
    if event.is_reply: await event.get_reply_message().forward_to('me'); await event.delete()

@client.on(events.NewMessage(pattern=r'^/del$', chats='me'))
async def delete(event):
    if event.is_reply: await event.get_reply_message().delete()
    await event.delete()

@client.on(events.NewMessage(pattern=r'^/ghost\s+(on|off)$', chats='me'))
async def ghost(event):
    global GHOST_MODE
    GHOST_MODE = (event.pattern_match.group(1) == 'on')
    await event.edit(f'👻 روح: {"✅" if GHOST_MODE else "❌"}')

@client.on(events.NewMessage(pattern=r'^/help$', chats='me'))
async def help_cmd(event):
    await event.edit('''🤖 **راهنمای سلف‌بات نسخه جدید:**
🧠 **هوش مصنوعی:** `/ask متن سوال` (مجهز به وب)
🔍 **مشخصات کاربر:** `/userinfo` (با ریپلای یا آیدی)
⏳ **تایمر معکوس:** `/timer ثانیه`
🎨 **استیکرساز:** `/kang ایموجی` (با ریپلای روی عکس)
🎭 **دستورات انیمیشن و فان:**
   ▫️ `/type متن` (تایپ زنده)
   ▫️ `/hack` (ترمینال هک با ریپلای)
   ▫️ `/hearts` (بارش رنگی قلب‌ها)
   ▫️ `/moon` (مراحل ماه)
💰 **قیمت در بیو:** `/price on|off`
🕐 **ساعت در نام:** `/clock on|off`
🎯 **منشن و ریپلای:** `/rp` | `/m` | `/mwho`
⚙️ **سیستم:** `/bot` | `/ping` | `/status` | `/ghost` | `/save` | `/del`''', parse_mode='md')

async def gen_mode():
    await client.connect()
    if await client.is_user_authorized():
        print('[GEN] SESSION_STRING:', client.session.save(), flush=True)
        await client.disconnect(); return
    h = PHONE_HASH; code = CODE
    if not code:
        r = await client.send_code_request(PHONE); h = r.phone_code_hash
        print('[GEN] CODE SENT. PHONE_HASH:', h, flush=True)
        if NTFY_TOPIC: code = await wait_for_code(NTFY_TOPIC, 600)
        if not code: await client.disconnect(); return
    try: await client.sign_in(PHONE, code, phone_code_hash=h)
    except errors.SessionPasswordNeededError: await client.sign_in(password=PASS2)
    print('[GEN] SESSION_STRING:', client.session.save(), flush=True)
    await client.disconnect()

# ==================== ربات اینلاین و پردازشگر خودکار ====================
# ==================== ربات اینلاین با قابلیت ویرایش خودکار ====================
# ==================== ربات اینلاین ====================
bot_client = None
if BOT_TOKEN:
    from telethon.sessions import MemorySession
    bot_client = TelegramClient(MemorySession(), API_ID, API_HASH)

    @bot_client.on(events.InlineQuery)
    async def inline_menu_handler(event):
        builder = event.builder
        results = [
            builder.article(
                title="🌙 انیمیشن فازهای ماه",
                description="اجرای چرخه ماه",
                text="🌑"
            ),
            builder.article(
                title="❤️ انیمیشن قلب‌های رنگی",
                description="اجرای چرخه قلب‌ها",
                text="🤍"
            ),
            builder.article(
                title="💀 هک نمایشی",
                description="ترمینال نفوذ",
                text="💻 `ورود به ترمینال...`"
            ),
            builder.article(
                title="⏳ تایمر ۳۰ ثانیه‌ای",
                description="شمارش معکوس ۳۰ ثانیه",
                text="⏳ زمان باقی‌مانده: 30 ثانیه"
            )
        ]
        await event.answer(results, cache_time=1)

# پردازشگر انیمیشن روی کلاینت اصلی
@client.on(events.NewMessage(outgoing=True))
async def anim_trigger_handler(event):
    msg_text = (event.raw_text or '').strip()

    if msg_text == '🌑':
        for m in ["🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑"]:
            await asyncio.sleep(0.4)
            try:
                await event.edit(m)
            except Exception:
                break

    elif msg_text == '🤍':
        for h in ["💜", "💙", "🩵", "💚", "💛", "🧡", "❤️"]:
            await asyncio.sleep(0.35)
            try:
                await event.edit(h)
            except Exception:
                break

    elif 'ورود به ترمینال' in msg_text:
        steps = ["🔍 اسکن پورت‌ها...", "🔓 دور زدن فایروال...", "📥 استخراج داده‌ها...", "✅ اتمام دسترسی!"]
        for s in steps:
            await asyncio.sleep(0.8)
            try:
                await event.edit(f"`{s}`")
            except Exception:
                break

    elif 'زمان باقی‌مانده: 30 ثانیه' in msg_text:
        for s in range(29, 0, -1):
            await asyncio.sleep(1)
            try:
                await event.edit(f"⏳ زمان باقی‌مانده: **{s}** ثانیه")
            except Exception:
                break
        try:
            await event.edit("⏰ **زمان به پایان رسید!**")
        except Exception:
            pass


# ==================== تابع اصلی و استارت کلاینت‌ها ====================
async def main():
    print("🚀 در حال اتصال سلف‌بات...")
    await client.start()
    me = await client.get_me()
    print(f"✅ سلف‌بات متصل شد: {me.first_name}")

    if bot_client:
        print("🤖 در حال اتصال ربات اینلاین...")
        await bot_client.start(bot_token=BOT_TOKEN)
        print("✅ ربات اینلاین فعال شد.")

    print("⚡ سلف‌بات در حال اجراست...")
    
    tasks = [client.run_until_disconnected()]
    if bot_client:
        tasks.append(bot_client.run_until_disconnected())
        
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

