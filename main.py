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
    InputStickerSetShortName, InputStickerSetItem, InputMediaUploadedDocument, DocumentAttributeFilename,
    MessageEntityTextUrl
)

AI_AVAILABLE = True
BOT_VERSION = '46-TargetClicker'
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
AUTO_ON = True
AUTOS = {}
AUTOS_PATH = '/data/autos.json'
CLICK_ON = True
CLICKS = {}
CLICKS_PATH = '/data/clicks.json'
OWNERS = {}
OWNERS_PATH = '/data/owners.json'
TRIED_OWNERS = set()
AI_LOCK = {}
PRICE_ON = os.getenv('PRICE_ON', '1') == '1'
PRICE_INTERVAL = int(os.getenv('PRICE_INTERVAL', '600'))
last_bio = ''
NAMES = []
NAMES_PATH = '/data/names.json'
LAST_MSG_BY_USER = {}
PENDING_READ_ANIMATIONS = {}

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

RAW_FONTS = [
    {'d': '⁰¹²³⁴⁵⁶⁷⁸⁹', 'c': 'ː'},
    {'d': '₀₁₂₃₄₅₆₇₈₉', 'c': ':'},
    {'d': '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡', 'c': ':'},
    {'d': '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗', 'c': ':'},
    {'d': '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿', 'c': ':'},
    {'d': '0123456789', 'c': ':'},
    {'d': '۰۱۲۳۴۵۶۷۸۹', 'c': ':'},
    {'d': '٠١٢٣٤٥٦٧٨٩', 'c': ':'},
    {'d': '𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫', 'c': ':'},
    {'d': '𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵', 'c': ':'},
    {'d': '➀➁➂➃➄➅➆➇➈➉', 'c': '·'},
    {'d': '⟦0⟧⟦1⟧⟦2⟧⟦3⟧⟦4⟧⟦5⟧⟦6⟧⟦7⟧⟦8⟧⟦9⟧', 'c': ':'},
    {'d': '🄋➀➁➂➃➄➅➆➇➈', 'c': ':'}
]

def validate_font(f):
    if not isinstance(f, dict): return False
    d = f.get('d', ''); c = f.get('c', '')
    return isinstance(d, str) and len(d) >= 10 and isinstance(c, str) and len(c) >= 1

FONTS = [f for f in RAW_FONTS if validate_font(f)]
CUSTOM_FONTS = []
CUSTOM_FONTS_PATH = '/data/fonts.json'
MAX_NAME_LEN = 58

def load_custom_fonts():
    global CUSTOM_FONTS
    try:
        with open(CUSTOM_FONTS_PATH, 'r', encoding='utf-8') as f: loaded = json.load(f)
        CUSTOM_FONTS = [x for x in loaded if validate_font(x)]
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

def small_time_with_font(font=None):
    tz = timezone(timedelta(hours=3, minutes=30))
    time_str = datetime.now(tz).strftime('%H:%M')
    circle_map = {'0': '⓪', '1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤', '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨', ':': '•'}
    return ''.join(circle_map.get(ch, ch) for ch in time_str)

def fa_now():
    tz = timezone(timedelta(hours=3, minutes=30))
    return datetime.now(tz).strftime('%Y/%m/%d %H:%M')

def get_utf16_len(text):
    return len(text.encode('utf-16-le')) // 2

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

def _clean_btn_text(txt: str) -> str:
    """حذف کامل ایموجی‌ها، علامت‌ها، اعراب، نیم‌فاصله و یکدست‌سازی حروف فارسی و عربی"""
    if not txt: return ""
    txt = str(txt)
    char_map = {
        'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 'آ': 'ا', 'أ': 'ا', 'إ': 'ا',
        'ئ': 'ی', 'ؤ': 'و', '۰': '0', '۱': '1', '۲': '2', '۳': '3',
        '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    for k, v in char_map.items():
        txt = txt.replace(k, v)
    # حذف نیم‌فاصله و اعراب
    txt = re.sub(r'[\u200c\u200b\u200d\u200e\u200f\u064b-\u065f]', '', txt)
    # حذف کامل تمام ایموجی‌ها، نمادها، علامت‌های نگارشی و خط تیره‌ها
    txt = re.sub(r'[^\w\s]', ' ', txt)
    return ' '.join(txt.split()).strip().lower()

def _web_search(query, max_results=3):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='ignore')
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
            clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:max_results]]
            if clean_snippets: return "\n".join(clean_snippets)
    except Exception: pass
    return ""

def _gemini_sync(question, timeout=30):
    cleaned_key = (GEMINI_API_KEY or '').strip().replace('\n', '').replace('\r', '')
    if not cleaned_key: return '❌ کلید API در تنظیمات ریل‌وی تنظیم نشده است.'
    web_context = _web_search(question)
    system_prompt = "شما یک دستیار هوش مصنوعی بسیار دقیق، روان و مسلط به زبان فارسی هستید. پاسخ را فقط و فقط به زبان فارسی سلیس بنویسید."
    if web_context: system_prompt += f"\n\nاطلاعات استخراج شده از اینترنت:\n{web_context}"

    free_target_models = [
        "google/gemini-2.0-flash-lite-preview:free",
        "deepseek/deepseek-chat:free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free"
    ]
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {'Authorization': f'Bearer {cleaned_key}', 'Content-Type': 'application/json', 'HTTP-Referer': 'https://railway.app'}

    for model_name in free_target_models:
        payload = {"model": model_name, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}], "temperature": 0.4, "max_tokens": 1000}
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                choices = res_json.get('choices', [])
                if choices:
                    msg = choices[0].get('message', {}).get('content', '')
                    if msg and msg.strip(): return msg.strip()
        except Exception: continue
    return '❌ سرورهای هوش مصنوعی پاسخگو نیستند.'

async def ask_ai(question, timeout=40):
    try:
        resp = await asyncio.get_running_loop().run_in_executor(None, _gemini_sync, question, timeout)
        resp = (resp or '').strip()
        if len(resp) > 3900: resp = resp[:3900] + '\n...(بریده شد)'
        return resp
    except Exception as e: return f'❌ خطا در تسک AI: {str(e)[:150]}'

def _fa_to_en(txt):
    return (txt or '').translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))

def parse_price_text(txt):
    res = {'usd': None, 'btc_usd': None, 'gold_gram': None}
    txt = _fa_to_en(txt)
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
    return res

async def get_channel_prices():
    res = {'usd': None, 'btc_usd': None, 'gold_gram': None}
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

async def build_bio():
    ch = await get_channel_prices()
    usd_toman = ch['usd']
    if not usd_toman: usd_toman, _ = await get_usd_toman()
    btc_usd = ch['btc_usd']
    if not btc_usd: btc_usd = await get_btc_usd()
    gold_gram = ch['gold_gram']
    
    parts = []
    if usd_toman: parts.append(f'💵 {usd_toman:,}')
    if btc_usd: parts.append(f'🪙 ${int(btc_usd):,}')
    if gold_gram: parts.append(f'🟡 {int(gold_gram):,}')

    if parts:
        return f"{' | '.join(parts)}\nchannel: @remixiyu"[:70]
    return "channel: @remixiyu"

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
                if bio: await update_bio(bio)
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
                    cid = item.get('chat'); iv = item.get('interval', 300)
                    if not cid: continue
                    if now - item.get('last', 0) >= iv:
                        try:
                            target_peer = int(cid) if str(cid).lstrip('-').isdigit() else cid
                            await client.send_message(target_peer, item.get('word', ''))
                            item['last'] = now
                            save_autos()
                        except Exception: pass
        except Exception: pass
        await asyncio.sleep(10)

def get_clean_active_targets(chat_id_to_check=None):
    """استخراج تارگت‌های معتبر کلیکر بدون مقادیر خالی"""
    targets = []
    if isinstance(CLICKS, dict):
        for v in CLICKS.values():
            if isinstance(v, dict):
                chat = v.get('chat')
                if chat_id_to_check is not None and chat:
                    try:
                        if str(chat).strip() != str(chat_id_to_check).strip():
                            continue
                    except Exception: pass
                btn_word = v.get('btn')
                if btn_word:
                    cleaned = _clean_btn_text(btn_word)
                    if len(cleaned) >= 2: # حداقل ۲ حرف باشد تا تصادفی نخورد
                        targets.append(cleaned)
    return targets

async def click_loop():
    while True:
        try:
            if CLICK_ON and MASTER_ON and CLICKS:
                for key, item in list(CLICKS.items()):
                    chat = item.get('chat')
                    btn_target = item.get('btn')
                    if not chat or not btn_target: continue
                    target_clean = _clean_btn_text(btn_target)
                    if not target_clean or len(target_clean) < 2: continue
                    try:
                        target_peer = int(chat) if str(chat).lstrip('-').isdigit() else chat
                        async for msg in client.iter_messages(target_peer, limit=4):
                            if msg.buttons:
                                for row in msg.buttons:
                                    for btn in row:
                                        raw_text = getattr(btn, 'text', '') or ''
                                        cleaned = _clean_btn_text(raw_text)
                                        # تطابق دقیق متن هدف با متن داخل دکمه
                                        if cleaned and (target_clean in cleaned):
                                            try:
                                                await btn.click()
                                                break
                                            except Exception:
                                                await msg.click(text=raw_text)
                                                break
                    except Exception: pass
        except Exception: pass
        await asyncio.sleep(4)

@client.on(events.NewMessage)
@client.on(events.MessageEdited)
async def instant_clicker_handler(event):
    if not CLICK_ON or not MASTER_ON: return
    buttons = getattr(event, 'buttons', None)
    if not buttons: return

    # دریافت تارگت‌های مربوط به همین چت (یا تارگت‌های کلی)
    targets = get_clean_active_targets(event.chat_id)
    if not targets:
        return

    try:
        for row_idx, row in enumerate(buttons):
            for col_idx, btn in enumerate(row):
                raw_text = getattr(btn, 'text', '') or ''
                cleaned = _clean_btn_text(raw_text)
                if not cleaned: continue

                # فقط در صورتی کلیک کن که متن تنظیم شده واقعاً در متن دکمه باشد
                matched = any(t in cleaned for t in targets)

                if matched:
                    try: await btn.click(); return
                    except Exception:
                        try: await event.click(row_idx, col_idx); return
                        except Exception: pass
    except Exception: pass

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
    PM_CACHE[event.id] = {'chat_id': event.chat_id, 'sender_id': sender.id if sender else event.chat_id, 'text': event.text or '', 'name': name or 'ناشناس', 'media': bool(event.media)}
    if len(PM_CACHE) > 3000:
        for k in list(PM_CACHE.keys())[:500]: PM_CACHE.pop(k, None)

@client.on(events.MessageEdited(incoming=True))
async def pm_edit_logger(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None: return
    if not event.is_private or event.chat_id == ME_ID: return
    sender = await event.get_sender()
    if getattr(sender, 'bot', False): return
    old = PM_CACHE.get(event.id, {})
    old_text = old.get('text', '(نامشخص)')
    name = old.get('name', 'ناشناس')
    PM_CACHE[event.id] = {'chat_id': event.chat_id, 'sender_id': sender.id if sender else event.chat_id, 'text': event.text or '', 'name': name, 'media': bool(event.media)}
    try: await client.send_message('me', f'✏️ **ادیت در پی‌وی:** {name}\n**قبلی:** {old_text}\n**جدید:** {event.text or ""}', parse_mode='md')
    except Exception: pass

@client.on(events.MessageDeleted)
async def pm_delete_logger(event):
    if not PMLOG_ON or not MASTER_ON or ME_ID is None: return
    for mid in event.deleted_ids:
        rec = PM_CACHE.pop(mid, None)
        if rec:
            media_info = " [حاوی مدیا]" if rec.get('media') else ""
            txt = rec.get('text') or '(بدون متن)'
            name = rec.get('name', 'ناشناس')
            uid = rec.get('sender_id', '')
            try: await client.send_message('me', f'🗑️ **حذف در پی‌وی:** {name} (`{uid}`)\n**متن پیام:** {txt}{media_info}', parse_mode='md')
            except Exception: pass

async def get_group_owner(cid):
    try:
        ent = await client.get_entity(cid)
        owner_id = None
        if getattr(ent, 'broadcast', False) or getattr(ent, 'megagroup', False) or getattr(ent, 'channel', False):
            res = await client(GetParticipantsRequest(ent, ChannelParticipantsAdmins(), 0, 100, 0))
            for p in res.participants:
                if isinstance(p, ChannelParticipantCreator): owner_id = p.user_id; break
        else:
            full = await client(GetFullChatRequest(cid))
            for p in full.full_chat.participants.participants:
                if isinstance(p, ChatParticipantCreator): owner_id = p.user_id; break
        if owner_id:
            u = await client.get_entity(owner_id)
            name = ((getattr(u, 'first_name', '') or '') + ' ' + (getattr(u, 'last_name', '') or '')).strip() or "بدون نام"
            return {'id': owner_id, 'name': name, 'username': f"@{u.username}" if getattr(u, 'username', None) else "ندارد", 'link': f"tg://openmessage?user_id={owner_id}"}
    except Exception: pass
    return None

async def log_ban(chat_id, admin_id, chat_title=None):
    if not BAN_LOG: return
    key = str(chat_id); now = time.time()
    if now - BAN_DEDUPE.get(key, 0) < 120: return
    BAN_DEDUPE[key] = now

    admin = None
    if admin_id:
        try: admin = await client.get_entity(admin_id)
        except Exception: admin = None

    if chat_title is None:
        try:
            chat = await client.get_entity(int(chat_id))
            chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', str(chat_id))
        except Exception: chat_title = str(chat_id)

    owner_info = await get_group_owner(chat_id)
    lines = [f'🚨 **بن/حذف شدی در:** {chat_title}']

    if admin:
        name = ((getattr(admin, 'first_name', '') or '') + ' ' + (getattr(admin, 'last_name', '') or '')).strip() or "بدون نام"
        un = f"@{admin.username}" if getattr(admin, 'username', None) else "ندارد"
        link = f"tg://openmessage?user_id={admin.id}"
        lines.extend([f'👤 **بن‌کننده:** [{name}]({link})', f'🆔 **ID:** `{admin.id}`', f'🔗 **یوزرنیم:** {un}'])
    elif admin_id:
        lines.append(f'🆔 **ID بن‌کننده:** `{admin_id}`')
    else:
        lines.append('👤 **بن‌کننده:** نامشخص (توسط سیستم یا ربات)')

    lines.append('—' * 15)
    if owner_info:
        lines.extend([f'👑 **مالک گروه:** [{owner_info["name"]}]({owner_info["link"]})', f'🆔 **ID مالک:** `{owner_info["id"]}`', f'🔗 **یوزرنیم:** {owner_info["username"]}'])
    lines.append(f'⏰ `{fa_now()}`')

    try: await client.send_message('me', '\n'.join(lines), parse_mode='md', link_preview=False)
    except Exception: pass

@client.on(events.ChatAction())
async def ban_detector(event):
    if ME_ID is None or not MASTER_ON or not BAN_LOG: return
    try:
        if event.user_kicked or event.user_left:
            ids = getattr(event, 'user_id', None) or []
            if isinstance(ids, int): ids = [ids]
            if ME_ID in ids:
                admin_id = None
                try:
                    am = event.action_message
                    if am and getattr(am, 'from_id', None):
                        admin_id = getattr(am.from_id, 'user_id', None)
                except Exception: pass
                await log_ban(event.chat_id, admin_id, None)
    except Exception: pass

async def send_mention_message(chat_id, text, target_user_id):
    try:
        user = await client.get_entity(target_user_id)
        name = user.first_name or "کاربر"
        full = f"{name}: {text}"
        ent = MessageEntityTextUrl(offset=0, length=get_utf16_len(name), url=f"tg://user?id={user.id}")
        await client.send_message(chat_id, full, formatting_entities=[ent])
    except Exception:
        await client.send_message(chat_id, text)

@client.on(events.NewMessage(outgoing=True))
async def stealth_mention_handler(event):
    if not event.is_group and not event.is_channel: return
    text = (event.raw_text or '').strip()
    if not text: return

    target_user = None; clean_msg = ""
    if text.startswith('//') and event.is_reply:
        clean_msg = text[2:].strip()
        rmsg = await event.get_reply_message()
        if rmsg and rmsg.sender_id:
            try: target_user = await event.client.get_entity(rmsg.sender_id)
            except Exception: pass

    elif text.startswith('+ ') or text.startswith('++'):
        clean_msg = text.lstrip('+').strip()
        cid = event.chat_id
        for (c_id, u_id), msg in reversed(list(LAST_MSG_BY_USER.items())):
            if c_id == cid and u_id != ME_ID:
                try: target_user = await event.client.get_entity(u_id); break
                except Exception: pass

    if target_user and clean_msg:
        try:
            await event.delete()
            name = target_user.first_name or "کاربر"
            final_text = f"{name}: {clean_msg}"
            ent = MessageEntityTextUrl(offset=0, length=get_utf16_len(name), url=f"tg://user?id={target_user.id}")
            await event.client.send_message(event.chat_id, final_text, formatting_entities=[ent])
        except Exception: pass

@client.on(events.NewMessage(outgoing=True))
async def fun_animations_handler(event):
    if not event.text: return
    text = event.raw_text.strip().lower()

    if text in ['.moon', '/moon']:
        frames = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑"]
        try:
            msg = await event.edit(frames[0])
            PENDING_READ_ANIMATIONS[msg.id] = {'chat_id': event.chat_id, 'frames': frames}
        except Exception: pass

    elif text in ['.heart', '.hearts', '/heart', '/hearts']:
        frames = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "💖", "🥰"]
        try:
            msg = await event.edit(frames[0])
            PENDING_READ_ANIMATIONS[msg.id] = {'chat_id': event.chat_id, 'frames': frames}
        except Exception: pass

@client.on(events.MessageRead(inbox=False))
async def on_message_read(event):
    read_max_id = event.max_id
    chat_id = event.chat_id

    to_animate = []
    for msg_id, data in list(PENDING_READ_ANIMATIONS.items()):
        if data['chat_id'] == chat_id and msg_id <= read_max_id:
            to_animate.append((msg_id, data['frames']))
            del PENDING_READ_ANIMATIONS[msg_id]

    for msg_id, frames in to_animate:
        asyncio.create_task(run_fun_animation(chat_id, msg_id, frames))

async def run_fun_animation(chat_id, message_id, frames):
    try:
        for f in frames[1:]:
            await asyncio.sleep(0.4)
            await client.edit_message(chat_id, message_id, f)
    except Exception: pass

@client.on(events.NewMessage(pattern=r'^[./]ask(?:\s+([\s\S]*))?$', outgoing=True))
async def ask_cmd(event):
    question = (event.pattern_match.group(1) or '').strip()
    rmsg = await event.get_reply_message()
    if not question and rmsg: question = (rmsg.text or '').strip()
    if not question:
        await event.edit('❌ سوالی مطرح نکردید.\nمثال: `/ask پایتخت ایتالیا کجاست؟`'); return

    cid = event.chat_id
    if cid in AI_LOCK:
        await event.edit('⏳ در حال پاسخگویی به درخواست قبلی...'); return

    AI_LOCK[cid] = True
    await event.edit('🤖 *در حال جستجو و پردازش پاسخ...*', parse_mode='md')
    try:
        resp = await ask_ai(question)
        await event.edit(f"🤖 **پاسخ هوش مصنوعی:**\n\n{resp}", parse_mode='md')
    except Exception as e:
        await event.edit(f'❌ خطا در پردازش: {str(e)[:150]}')
    finally: AI_LOCK.pop(cid, None)

@client.on(events.NewMessage(pattern=r'^[./]type(?:\s+([\s\S]+))?$', outgoing=True))
async def type_cmd(event):
    text = event.pattern_match.group(1)
    if not text:
        rmsg = await event.get_reply_message()
        if rmsg and rmsg.text: text = rmsg.text
    if not text:
        await event.edit('❌ متنی برای تایپ ننوشتید.'); return
    current_text = ''
    for char in text:
        current_text += char
        try:
            await event.edit(current_text + '▒')
            await asyncio.sleep(0.08)
        except Exception: await asyncio.sleep(0.2)
    try: await event.edit(text)
    except Exception: pass

@client.on(events.NewMessage(pattern=r'^[./]hack$', outgoing=True))
async def hack_cmd(event):
    rmsg = await event.get_reply_message()
    target_name = "کاربر"
    if rmsg:
        sender = await rmsg.get_sender()
        if sender: target_name = getattr(sender, 'first_name', '') or str(sender.id)
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

@client.on(events.NewMessage(pattern=r'^[./]timer\s+(\d+)$', outgoing=True))
async def timer_cmd(event):
    secs = int(event.pattern_match.group(1))
    if secs > 300: await event.edit('⚠️ حداکثر زمان تایمر ۳۰۰ ثانیه است.'); return
    while secs > 0:
        m, s = divmod(secs, 60)
        try:
            await event.edit(f"⏳ **تایمر معکوس:** `{m:02d}:{s:02d}`", parse_mode='md')
            await asyncio.sleep(1)
            secs -= 1
        except Exception: await asyncio.sleep(2)
    try: await event.edit("⏰ **زمان به پایان رسید!**", parse_mode='md')
    except Exception: pass

@client.on(events.NewMessage(pattern=r'^[./]userinfo(?:\s+(\S+))?$', outgoing=True))
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
        await event.edit('❌ روی یک پیام ریپلای کنید یا آیدی کاربر را وارد نمایید.'); return

    fn = getattr(user, 'first_name', '') or ''
    ln = getattr(user, 'last_name', '') or ''
    un = f"@{user.username}" if getattr(user, 'username', None) else "ندارد"
    uid = user.id
    info = f"👤 **اطلاعات کاربر:**\n▫️ **نام:** {fn} {ln}\n▫️ **یوزرنیم:** {un}\n▫️ **آیدی عددی:** `{uid}`\n▫️ **پروفایل:** [مشاهده](tg://user?id={uid})"
    await event.edit(info, parse_mode='md')

@client.on(events.NewMessage(pattern=r'^[./]kang(?:\s+([\s\S]+))?$', outgoing=True))
async def kang_cmd(event):
    emoji = (event.pattern_match.group(1) or '🤔').strip()
    rmsg = await event.get_reply_message()
    if not rmsg or not rmsg.media:
        await event.edit('❌ روی عکس، گیف یا استیکر ریپلای کنید.'); return
    await event.edit('🎨 در حال تبدیل استیکر...')
    try:
        photo_bytes = await rmsg.download_media(file=bytes)
        image = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
        scale = 512 / max(image.size[0], image.size[1])
        image = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)), Image.Resampling.LANCZOS)
        out = io.BytesIO(); image.save(out, format="PNG")
        pack_name = f"kang_{ME_ID}_v1_by_{ME_USER}" if ME_USER else f"kang_{ME_ID}_v1"
        pack_title = f"@{ME_USER or 'My'} Pack"
        file = await client.upload_file(out.getvalue())
        doc = InputMediaUploadedDocument(file=file, mime_type='image/png', attributes=[DocumentAttributeFilename('sticker.png')])
        res = await client(UploadMediaRequest(peer=types.InputPeerSelf(), media=doc))
        doc_item = types.InputDocument(id=res.document.id, access_hash=res.document.access_hash, file_reference=res.document.file_reference)
        try:
            await client(AddStickerToSetRequest(stickerset=InputStickerSetShortName(short_name=pack_name), sticker=InputStickerSetItem(document=doc_item, emoji=emoji)))
            await event.edit(f'✅ به پک اضافه شد!\n🔗 https://t.me/addstickers/{pack_name}')
        except errors.StickersetInvalidError:
            await client(CreateStickerSetRequest(user_id=types.InputUserSelf(), title=pack_title, short_name=pack_name, stickers=[InputStickerSetItem(document=doc_item, emoji=emoji)]))
            await event.edit(f'🎉 پک ساخته شد!\n🔗 https://t.me/addstickers/{pack_name}')
    except Exception as e: await event.edit(f'❌ خطا: {str(e)[:100]}')

@client.on(events.NewMessage(pattern=r'^[./]rp\s*(.*)$', outgoing=True))
async def rp_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text: await event.edit('❌ دستور: /rp متن'); return
    rmsg = await event.get_reply_message()
    if not rmsg or not rmsg.sender_id: await event.edit('❌ روی پیام کاربر ریپلای کنید'); return
    await send_mention_message(event.chat_id, text, rmsg.sender_id)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^[./]m\s*(.*)$', outgoing=True))
async def m_cmd(event):
    text = (event.pattern_match.group(1) or '').strip()
    if not text: await event.edit('❌ دستور: /m متن'); return
    cid = event.chat_id
    target = None
    for (chat_id, user_id), msg in LAST_MSG_BY_USER.items():
        if chat_id == cid and user_id != ME_ID: target = user_id; break
    if target is None: await event.edit('❌ پیامی از کاربری در این چت ثبت نشده'); return
    await send_mention_message(cid, text, target)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^[./]status$', outgoing=True))
async def status_cmd(event):
    text = (
        f"📊 **وضعیت سلف‌بات نسخه {BOT_VERSION}:**\n\n"
        f"🔹 وضعیت کلی: `{'روشن ✅' if MASTER_ON else 'خاموش ❌'}`\n"
        f"🕒 ساعت در اسم: `{'روشن ✅' if CLOCK_ON else 'خاموش ❌'}`\n"
        f"💰 بیوگرافی قیمت: `{'روشن ✅' if PRICE_ON else 'خاموش ❌'}`\n"
        f"⚡ ارسال خودکار (Auto): `{'روشن ✅' if AUTO_ON else 'خاموش ❌'}` ({len(AUTOS)} چت)\n"
        f"🎯 کلیکر هوشمند: `{'روشن ✅' if CLICK_ON else 'خاموش ❌'}` ({len(CLICKS)} دکمه)\n"
        f"⏳ ذخیره مدیاهای تایمردار: `{'روشن ✅' if TTL_SAVE else 'خاموش ❌'}`\n"
        f"📩 لاگر پی‌وی: `{'روشن ✅' if PMLOG_ON else 'خاموش ❌'}`\n"
        f"🚨 لاگ اخراج و بن: `{'روشن ✅' if BAN_LOG else 'خاموش ❌'}`"
    )
    await event.edit(text, parse_mode='md')

@client.on(events.NewMessage(pattern=r'^[./]auto\s+(on|off)$', outgoing=True))
async def auto_toggle(event):
    global AUTO_ON
    AUTO_ON = (event.pattern_match.group(1) == 'on')
    await event.edit(f'⚡ ارسال خودکار (Auto): {"روشن ✅" if AUTO_ON else "خاموش ❌"}')

@client.on(events.NewMessage(pattern=r'^[./]auto\s+add\s+(\d+)\s+(.+)$', outgoing=True))
async def auto_add(event):
    interval = int(event.pattern_match.group(1))
    text = event.pattern_match.group(2).strip()
    cid = str(event.chat_id)
    k = next_key(AUTOS)
    AUTOS[k] = {'chat': cid, 'word': text, 'interval': interval, 'last': 0}
    save_autos()
    await event.edit(f'✅ ارسال خودکار هر `{interval}` ثانیه تنظیم شد:\n«{text}»', parse_mode='md')

@client.on(events.NewMessage(pattern=r'^[./]auto\s+del\s+(\S+)$', outgoing=True))
async def auto_del(event):
    k = event.pattern_match.group(1).strip()
    if k in AUTOS:
        del AUTOS[k]; save_autos()
        await event.edit(f'🗑️ ارسال خودکار ردیف {k} حذف شد.')
    else: await event.edit('❌ ردیف یافت نشد.')

@client.on(events.NewMessage(pattern=r'^[./]auto\s+list$', outgoing=True))
async def auto_list(event):
    if not AUTOS: await event.edit('📭 هیچ پیام خودکاری تنظیم نشده است.'); return
    lines = ['📋 **لیست ارسال خودکار:**']
    for k, v in AUTOS.items():
        lines.append(f"• `{k}`: هر `{v.get('interval')}` ثانیه در چت `{v.get('chat')}` ⇦ «{v.get('word')}»")
    await event.edit('\n'.join(lines), parse_mode='md')

@client.on(events.NewMessage(pattern=r'^[./]click\s+(on|off)$', outgoing=True))
async def click_toggle(event):
    global CLICK_ON
    CLICK_ON = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🔘 کلیکر: {"روشن ✅" if CLICK_ON else "خاموش ❌"}')

@client.on(events.NewMessage(pattern=r'^[./]click\s+add\s+(.+)$', outgoing=True))
async def click_add(event):
    btn_text = event.pattern_match.group(1).strip()
    cid = str(event.chat_id)
    k = next_key(CLICKS)
    CLICKS[k] = {'chat': cid, 'btn': btn_text, 'interval': 3}
    save_clicks()
    await event.edit(f'✅ کلیک خودکار فقط روی کلمه «{btn_text}» تنظیم شد.')

@client.on(events.NewMessage(pattern=r'^[./]click\s+del\s+(\S+)$', outgoing=True))
async def click_del(event):
    k = event.pattern_match.group(1).strip()
    if k in CLICKS:
        del CLICKS[k]; save_clicks()
        await event.edit(f'🗑️ کلیکر ردیف {k} حذف شد.')
    else: await event.edit('❌ ردیف یافت نشد.')

@client.on(events.NewMessage(pattern=r'^[./]click\s+list$', outgoing=True))
async def click_list(event):
    if not CLICKS: await event.edit('📭 هیچ کلیکری فعال نیست.'); return
    lines = ['📋 **لیست کلیکرها:**']
    for k, v in CLICKS.items():
        lines.append(f"• `{k}`: فقط کلمه «{v.get('btn')}» در چت `{v.get('chat')}`")
    await event.edit('\n'.join(lines), parse_mode='md')

@client.on(events.NewMessage(pattern=r'^[./]ping$', outgoing=True))
async def ping(event): await event.edit('🏓 پونگ!')

@client.on(events.NewMessage(pattern=r'^[./]clock\s+(on|off)$', outgoing=True))
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
        CLOCK_ON = False; await update_profile_name(BASE_LAST); await event.edit('🕐 ساعت خاموش شد.')

@client.on(events.NewMessage(pattern=r'^[./]price\s+(on|off)$', outgoing=True))
async def price_cmd(event):
    global PRICE_ON
    PRICE_ON = (event.pattern_match.group(1) == 'on')
    if PRICE_ON:
        bio = await build_bio()
        if bio: await update_bio(bio)
        await event.edit(f'💰 قیمت‌ها: روشن ✅\n{bio}')
    else:
        await update_bio('channel: @remixiyu')
        await event.edit('💰 قیمت‌ها: خاموش ❌')

@client.on(events.NewMessage(pattern=r'^[./]pmlog\s+(on|off)$', outgoing=True))
async def pmlog_toggle(event):
    global PMLOG_ON
    PMLOG_ON = (event.pattern_match.group(1) == 'on')
    await event.edit(f'📩 لاگ پی‌وی: {"روشن ✅" if PMLOG_ON else "خاموش ❌"}')

@client.on(events.NewMessage(pattern=r'^[./]banlog\s+(on|off)$', outgoing=True))
async def banlog_toggle(event):
    global BAN_LOG
    BAN_LOG = (event.pattern_match.group(1) == 'on')
    await event.edit(f'🚨 لاگ بن و اخراج: {"روشن ✅" if BAN_LOG else "خاموش ❌"}')

@client.on(events.NewMessage(incoming=True))
async def ttl_saver_handler(event):
    if not TTL_SAVE or not MASTER_ON or ME_ID is None: return
    if not event.is_private or event.chat_id == ME_ID: return
    media = event.media
    if not media: return
    ttl_period = getattr(media, 'ttl_seconds', None)
    if ttl_period:
        file_path = None
        try:
            sender = await event.get_sender()
            name = ((getattr(sender, 'first_name', '') or '') + ' ' + (getattr(sender, 'last_name', '') or '')).strip() or 'ناشناس'
            uid = sender.id if sender else event.chat_id
            file_path = await event.download_media(file='/tmp/')
            if file_path and os.path.exists(file_path):
                caption = f"⏳ **رسانه تایمردار ذخیره شد!**\n👤 فرستنده: {name} (`{uid}`)\n⏰ زمان خودتخریبی: {ttl_period} ثانیه"
                await client.send_file('me', file_path, caption=caption, parse_mode='md')
        except Exception: pass
        finally:
            if file_path and os.path.exists(file_path):
                try: os.remove(file_path)
                except Exception: pass

@client.on(events.NewMessage(pattern=r'^[./]help$', outgoing=True))
async def help_cmd(event):
    await event.edit('''🤖 **راهنمای جامع سلف‌بات:**
🧠 **هوش مصنوعی:** `/ask سوال`
⏳ **تایمر معکوس:** `/timer ثانیه`
🎨 **استیکرساز:** `/kang ایموجی`
🔍 **مشخصات کاربر:** `/userinfo`
🎭 **فان (سین‌چک):**
   ▫️ `.moon` یا `/moon` (مراحل ماه بعد از سین)
   ▫️ `.heart` یا `/heart` (بارش قلب بعد از سین)
   ▫️ `/type متن` | `/hack`
⚡ **ارسال خودکار:**
   ▫️ `/auto on|off`
   ▫️ `/auto add <ثانیه> <متن>`
   ▫️ `/auto list` | `/auto del <شماره>`
🎯 **کلیکر هوشمند:**
   ▫️ `/click on|off`
   ▫️ `/click add <متن دقیق دکمه>`
   ▫️ `/click list` | `/click del <شماره>`
📩 **لاگرها:**
   ▫️ `/pmlog on|off` (ادیت و حذف پی‌وی)
   ▫️ `/banlog on|off` (گزارش اخراج و بن)
💰 **قیمت در بیو:** `/price on|off`
🕐 **ساعت در نام:** `/clock on|off`
⚙️ **سیستم:** `/status` | `/ping`''', parse_mode='md')

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

async def main():
    global BASE_LAST, ME_ID, ME_USER
    if WIPE:
        for p in (SESSION_PATH + '.session', SESSION_PATH + '.hash'):
            try: os.remove(p)
            except Exception: pass
    _original_ack = client.send_read_acknowledge
    async def _ghost_ack(*args, **kwargs):
        if GHOST_MODE: return None
        return await _original_ack(*args, **kwargs)
    client.send_read_acknowledge = _ghost_ack
    if GEN: await gen_mode(); return
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print('[FATAL] سشن سلف‌بات معتبر نیست.', flush=True); return
    except Exception as e:
        print(f'[FATAL] خطای اتصال: {e}', flush=True); return

    load_autos(); load_clicks(); load_owners(); load_watch(); load_custom_fonts(); load_names()
    me = await client.get_me()
    ME_ID = me.id
    ME_USER = me.username
    BASE_LAST = safe_name_part(CLOCK_RE.sub('', me.last_name or '').strip())
    await normalize_stored()

    asyncio.create_task(clock_loop())
    asyncio.create_task(auto_loop())
    asyncio.create_task(probe_loop())
    asyncio.create_task(click_loop())
    if PRICE_ON: asyncio.create_task(price_loop())

    print(f'🚀 سلف‌بات {BOT_VERSION} با موفقیت آنلاین شد!', flush=True)
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
