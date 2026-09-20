import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
STRING_SESSION = os.getenv('STRING_SESSION', '')
GHOST_MODE = False

if STRING_SESSION:
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
else:
    client = TelegramClient('selfbot_session', API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'^/ping$', chats='me'))
async def ping(event):
    await event.edit('🏓 پونگ! سلف‌بات زنده است.')

@client.on(events.NewMessage(pattern=r'^/save$', chats='me'))
async def save(event):
    if event.is_reply:
        msg = await event.get_reply_message()
        await msg.forward_to('me')
        await event.edit('✅ پیام در Saved ذخیره شد.')
    else:
        await event.edit('⚠️ روی یک پیام reply کن و /save بزن.')

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
    await event.edit(
        '🤖 <b>راهنما</b>\n/ping - تست\n/save - ذخیره پیام\n/del - پاک کردن\n/ghost on|off - حالت روح',
        parse_mode='html'
    )

async def main():
    await client.start()
    print('🚀 سلف‌بات فعال شد!', flush=True)
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
