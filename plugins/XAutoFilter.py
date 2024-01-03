import asyncio
import re
import ast
import math
import random
import imdb
import html
lock = asyncio.Lock()
import regex 

from Script import script
import pyrogram
from info import ADMINS,VTIME, AUTH_CHANNEL, NO_RES_CNL,SUPPORT_CHAT_ID, CUSTOM_FILE_CAPTION, MSG_ALRT, SUP_LNK, CHNL_LNK, IS_VERIFY, HOW_TO_VERIFY, DLT
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, temp, get_settings, send_all, check_verification, get_token
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details,search_db
from fuzzywuzzy import fuzz, process
import imdb
ia = imdb.IMDb()

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}

@Client.on_message((filters.group) & filters.text & filters.incoming)
async def give_filter(client, message):

    if message.chat.id == SUPPORT_CHAT_ID:
        return
    
    if message.text is None:
        await asyncio.sleep(DLT)
        await message.delete()
        return

    if message.text.startswith("/"):
        return 

    await auto_filter(client, message)

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, offset,search = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return

    files, n_offset, total_pages = await search_db(search, offset)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    btn = await result_btn(files,req,search)
    query.text = search
    btn = await navigation_buttons(btn,query, total_pages, n_offset)

    cap = f"<b>Hᴇʏ There,\n\nI Fᴏᴜɴᴅ Sᴏᴍᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ Yᴏᴜʀ Qᴜᴇʀʏ: {search}\n\n</b>"
    try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    await query.answer()

async def navigation_buttons(btn,message, total_pages, offset):
    req = message.from_user.id if message.from_user else 0
    search = message.text
    offset = int(offset)
    if total_pages == 1 :
        btn.append([
            InlineKeyboardButton(text=f"⟸",callback_data="pages"),
            InlineKeyboardButton(text=f" 1 / {total_pages}",callback_data="pages"),
            InlineKeyboardButton(text="⟹",callback_data="pages")]
        )
    elif offset == 10 :
        btn.append([
            InlineKeyboardButton(text=f"⟸",callback_data="pages"),
            InlineKeyboardButton(text=f" 1 / {total_pages}",callback_data="pages"),
            InlineKeyboardButton(text="⟹",callback_data=f"next_{req}_{offset}_{search}")]
        )
    else:
        btn.append([
            InlineKeyboardButton(text="⟸",callback_data=f"next_{req}_{offset-20}_{search}"),
            InlineKeyboardButton(text=f"{math.ceil(int(offset)/10)} / {total_pages}",callback_data="pages"),
            InlineKeyboardButton(text="⟹",callback_data=f"next_{req}_{offset}_{search}") ]
        )
        
    return btn

@Client.on_callback_query(filters.regex(r"^filterx"))
async def filtering_results(bot, query):
    _, userid, the_filter,search= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    movie = search
    if the_filter == "close":
        k =  await query.edit_message_text(
        text='.......',
        reply_markup=None
    )
        await asyncio.sleep(1)
        await k.delete()
        return 
    if the_filter == "dual":
        the_filter = "hindi english"
    elif the_filter == "multi":
        the_filter = "english hindi tamil telugu"
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if the_filter != "home" and the_filter != "all":
        movie = f"{movie} {the_filter}"
    movie = await process_text(movie)
    files, offset, total_pages = await search_db(movie, offset=0)
    query.text = movie
    if files:
        try:
            btn = await result_btn(files,query.from_user.id,search)
            btn = await navigation_buttons(btn,query, total_pages, offset)
            try:
                cap = f"<b>Hey {query.from_user.mention},\n\nResults For: </b>{movie}"
                await query.edit_message_text(
                    text=cap,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except MessageNotModified:
                pass
        except:
            btn = await result_btn(files,query.from_user.id,search,True)
            btn = await navigation_buttons(btn,query, total_pages, offset)
            try:
                cap = f"<b>Hey {query.from_user.mention},\n\nResults For: </b>{movie}"
                await query.edit_message_text(
                    text=cap,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except MessageNotModified:
                pass
        await query.answer()
    else:
        await bot.send_message(chat_id=NO_RES_CNL, text=f"{movie}")
        return await query.answer(f"Sᴏʀʀʏ, Nᴏ ғɪʟᴇs ғᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ", show_alert=True)

@Client.on_callback_query(filters.regex(r"^select_lang"))
async def select_language(bot, query):
    _, userid,search= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("Eɴɢʟɪꜱʜ", callback_data=f"filterx#{userid}#english#{search}"),
        InlineKeyboardButton("Hɪɴᴅɪ", callback_data=f"filterx#{userid}#hindi#{search}")
    ],[
        InlineKeyboardButton("Tᴀᴍɪʟ", callback_data=f"filterx#{userid}#tamil#{search}"),
        InlineKeyboardButton("Tᴇʟᴜɢᴜ", callback_data=f"filterx#{userid}#telugu#{search}")
    ],[
        InlineKeyboardButton("Mᴀʀᴀᴛʜɪ", callback_data=f"filterx#{userid}#mar#{search}"),
        InlineKeyboardButton("Mᴀʟᴀʏᴀʟᴀᴍ", callback_data=f"filterx#{userid}#mal#{search}")
    ],[
        InlineKeyboardButton("Kᴀɴɴᴀᴅᴀ", callback_data=f"filterx#{userid}#kan#{search}"),
        InlineKeyboardButton("Dᴜᴀʟ Aᴜᴅɪᴏ", callback_data=f"filterx#{userid}#dual#{search}")
    ],[
        InlineKeyboardButton("Mᴜʟᴛɪ Aᴜᴅɪᴏ", callback_data=f"filterx#{userid}#multi#{search}"),
        InlineKeyboardButton("⟸", callback_data=f"filterx#{userid}#home#{search}")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()
    
@Client.on_callback_query(filters.regex(r"^select_season"))
async def select_season(bot, query):
    _, userid,search= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("Season 01", callback_data=f"filterx#{userid}#s01#{search}"),
        InlineKeyboardButton("Season 02", callback_data=f"filterx#{userid}#s02#{search}")
    ],[
        InlineKeyboardButton("Season 03", callback_data=f"filterx#{userid}#s03#{search}"), 
        InlineKeyboardButton("Season 04", callback_data=f"filterx#{userid}#s04#{search}")
    ],[
        InlineKeyboardButton("Season 05", callback_data=f"filterx#{userid}#s05#{search}"),
        InlineKeyboardButton("Season 06", callback_data=f"filterx#{userid}#s06#{search}")
    ],[
        InlineKeyboardButton("Season 07", callback_data=f"filterx#{userid}#s07#{search}"), 
        InlineKeyboardButton("Season 08", callback_data=f"filterx#{userid}#s08#{search}")
    ],[
        InlineKeyboardButton("Season 09", callback_data=f"filterx#{userid}#s09#{search}"),
        InlineKeyboardButton("Season 10", callback_data=f"filterx#{userid}#s10#{search}")
    ],[
        InlineKeyboardButton("Season 11", callback_data=f"filterx#{userid}#s11#{search}"), 
        InlineKeyboardButton("⟸", callback_data=f"filterx#{userid}#home#{search}")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^select_qual"))
async def select_quality(bot, query):
    _, userid,search= query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("180p", callback_data=f"filterx#{userid}#180p#{search}"),
        InlineKeyboardButton("480p", callback_data=f"filterx#{userid}#480p#{search}")
    ],[
        InlineKeyboardButton("720p", callback_data=f"filterx#{userid}#720p#{search}"),
        InlineKeyboardButton("1080p", callback_data=f"filterx#{userid}#1080p#{search}")
    ],[
        InlineKeyboardButton("4k", callback_data=f"filterx#{userid}#2160p#{search}"),
        InlineKeyboardButton("⟸", callback_data=f"filterx#{userid}#home#{search}")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "gfiltersdeleteallcancel": 
        await query.message.reply_to_message.delete()
        await query.message.delete()
        await query.answer("Pʀᴏᴄᴇss Cᴀɴᴄᴇʟʟᴇᴅ !")
        return
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Tʜᴀᴛ's ɴᴏᴛ ғᴏʀ ʏᴏᴜ!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Gʀᴏᴜᴘ Nᴀᴍᴇ : **{title}**\nGʀᴏᴜᴘ ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await None, None, None, None
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.message.reply_to_message.from_user.id
        except:
            typed = query.from_user.id
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            elif settings['botpm']:
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            else:
                if clicked == typed:
                    if IS_VERIFY and not await check_verification(client, query.from_user.id):
                        m = await client.reply_text("Please Wait . .")
                        await asyncio.sleep(VTIME)
                        await m.delete()
                        btn = [[
                            InlineKeyboardButton("Vᴇʀɪғʏ", url=await get_token(client, query.from_user.id, f"https://telegram.me/{temp.U_NAME}?start=", file_id)),
                            InlineKeyboardButton("Hᴏᴡ Tᴏ Vᴇʀɪғʏ", url=HOW_TO_VERIFY)
                        ]]
                        
                        await client.send_message(
                            chat_id=query.from_user.id,
                            text="<b>Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ!\nKɪɴᴅʟʏ ᴠᴇʀɪғʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ Sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ ᴀᴄᴄᴇss ᴛᴏ ᴜɴʟɪᴍɪᴛᴇᴅ ᴍᴏᴠɪᴇs ᴜɴᴛɪʟ 24 ʜᴏᴜʀs ғʀᴏᴍ ɴᴏᴡ !\n\nआप verified नहीं हैं ! \nकृपया जारी रखने के लिए verify करें ताकि आप अब से 16 घंटे तक unlimited फिल्मों  प्राप्त कर सकें</b>",
                            protect_content=True if ident == 'checksubp' else False,
                            disable_web_page_preview=True,
                            parse_mode=enums.ParseMode.HTML,
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        return await query.answer("Hᴇʏ, Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ. Yᴏᴜ ʜᴀᴠᴇ ᴛᴏ ᴠᴇʀɪғʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ. Cʜᴇᴄᴋ ᴍʏ PM ᴛᴏ ᴠᴇʀɪғʏ ᴀɴᴅ ɢᴇᴛ ғɪʟᴇs !", show_alert=True)
                    else:
                        await client.send_cached_media(
                            chat_id=query.from_user.id,
                            file_id=file_id,
                            caption=f_caption,
                            protect_content=True if ident == "filep" else False,
                            reply_markup=InlineKeyboardMarkup(
                                [[
                                InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=SUP_LNK),
                                InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                            ]]
                            )
                        )
                        return await query.answer('Cʜᴇᴄᴋ PM, I ʜᴀᴠᴇ sᴇɴᴛ ғɪʟᴇs ɪɴ PM', show_alert=True)
                else:
                    return await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("Jᴏɪɴ ᴏᴜʀ Bᴀᴄᴋ-ᴜᴘ ᴄʜᴀɴɴᴇʟ ᴍᴀʜɴ! 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        if file_id == "send_all":
            send_files = temp.SEND_ALL_TEMP.get(query.from_user.id)
            is_over = await send_all(client, query.from_user.id, send_files, ident)
            if is_over == 'done':
                return await query.answer(f"Hᴇʏ {query.from_user.first_name}, Aʟʟ ғɪʟᴇs ᴏɴ ᴛʜɪs ᴘᴀɢᴇ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴏ ʏᴏᴜʀ PM !", show_alert=True)
            elif is_over == 'fsub':
                return await query.answer("Hᴇʏ, Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ɪɴ ᴍʏ ʙᴀᴄᴋ ᴜᴘ ᴄʜᴀɴɴᴇʟ. Cʜᴇᴄᴋ ᴍʏ PM ᴛᴏ ᴊᴏɪɴ ᴀɴᴅ ɢᴇᴛ ғɪʟᴇs !", show_alert=True)
            elif is_over == 'verify':
                return await query.answer("Hᴇʏ, Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ. Yᴏᴜ ʜᴀᴠᴇ ᴛᴏ ᴠᴇʀɪғʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ. Cʜᴇᴄᴋ ᴍʏ PM ᴛᴏ ᴠᴇʀɪғʏ ᴀɴᴅ ɢᴇᴛ ғɪʟᴇs !", show_alert=True)
            else:
                return await query.answer(f"Eʀʀᴏʀ: {is_over}", show_alert=True)
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        if IS_VERIFY and not await check_verification(client, query.from_user.id):
            m = await client.reply_text("Please Wait . .")
            await asyncio.sleep(VTIME)
            await m.delete()
            
            btn = [[
                InlineKeyboardButton("Vᴇʀɪғʏ", url=await get_token(client, query.from_user.id, f"https://telegram.me/{temp.U_NAME}?start=", file_id)),
                InlineKeyboardButton("Hᴏᴡ Tᴏ Vᴇʀɪғʏ", url=HOW_TO_VERIFY)
            ]]
            
            await client.send_message(
                chat_id=query.from_user.id,
                text="<b>Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ!\nKɪɴᴅʟʏ ᴠᴇʀɪғʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ Sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ ᴀᴄᴄᴇss ᴛᴏ ᴜɴʟɪᴍɪᴛᴇᴅ ᴍᴏᴠɪᴇs ᴜɴᴛɪʟ 16 ʜᴏᴜʀs ғʀᴏᴍ ɴᴏᴡ !\n\nआप verified नहीं हैं ! \nकृपया जारी रखने के लिए verify करें ताकि आप अब से 16 घंटे तक unlimited फिल्मों  प्राप्त कर सकें</b>",
                protect_content=True if ident == 'checksubp' else False,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False,
            reply_markup=InlineKeyboardMarkup(
                [[
                  InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=SUP_LNK),
                  InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
               ]]
            )
        )
    elif query.data == "pages":
        await query.answer()

    elif query.data.startswith("send_fall"):
        temp_var, ident, offset, userid = query.data.split("#")
        if int(userid) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        files = temp.SEND_ALL_TEMP.get(query.from_user.id)
        is_over = await send_all(client, query.from_user.id, files, ident)
        if is_over == 'done':
            return await query.answer(f"Hᴇʏ {query.from_user.first_name}, Aʟʟ ғɪʟᴇs ᴏɴ ᴛʜɪs ᴘᴀɢᴇ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴏ ʏᴏᴜʀ PM !", show_alert=True)
        elif is_over == 'fsub':
            return await query.answer("Hᴇʏ, Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ɪɴ ᴍʏ ʙᴀᴄᴋ ᴜᴘ ᴄʜᴀɴɴᴇʟ. Cʜᴇᴄᴋ ᴍʏ PM ᴛᴏ ᴊᴏɪɴ ᴀɴᴅ ɢᴇᴛ ғɪʟᴇs !", show_alert=True)
        elif is_over == 'verify':
            return await query.answer("Hᴇʏ, Yᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ. Yᴏᴜ ʜᴀᴠᴇ ᴛᴏ ᴠᴇʀɪғʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ. Cʜᴇᴄᴋ ᴍʏ PM ᴛᴏ ᴠᴇʀɪғʏ ᴀɴᴅ ɢᴇᴛ ғɪʟᴇs !", show_alert=True)
        else:
            return await query.answer(f"Eʀʀᴏʀ: {is_over}", show_alert=True)

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fᴇᴛᴄʜɪɴɢ Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} ᴏɴ DB... Pʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        files, total = await search_db(keyword)
        await query.message.edit_text(f"<b>Fᴏᴜɴᴅ {total} Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nFɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇss ᴡɪʟʟ sᴛᴀʀᴛ ɪɴ 5 sᴇᴄᴏɴᴅs!</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'Fɪʟᴇ Fᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}! Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>Pʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ ғᴏʀ ᴅᴇʟᴇᴛɪɴɢ ғɪʟᴇs ғʀᴏᴍ DB. Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nPʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                logger.exception(e)
                await query.message.edit_text(f'Eʀʀᴏʀ: {e}')
            else:
                await query.message.edit_text(f"<b>Pʀᴏᴄᴇss Cᴏᴍᴘʟᴇᴛᴇᴅ ғᴏʀ ғɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ !\n\nSᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}.</b>")

    elif query.data == "reqinfo":
        await query.answer(text=script.REQINFO, show_alert=True)

    elif query.data == "minfo":
        await query.answer(text=script.MINFO, show_alert=True)

    elif query.data == "sinfo":
        await query.answer(text=script.SINFO, show_alert=True)

    else: return

async def process_text(text):
    text_caption = text
    text_caption = text_caption.lower()

    # Remove emojis using regex module
    text_caption = regex.sub(r'\p{So}', '', text_caption)

    # Replace certain characters with spaces
    text_caption = re.sub(r"[@!$ _\-.+:*#⁓]", " ", text_caption)

    # Insert space between 's' and 'e' in patterns like 's01e04'
    text_caption = re.sub(r's(\d+)e(\d+)', r's\1 e\2', text_caption, flags=re.IGNORECASE)

    # Insert space between 's' and 'e' in patterns like 's1e4'
    text_caption = re.sub(r's(\d+)e', r's\1 e', text_caption, flags=re.IGNORECASE)

    # Convert 'ep' followed by a number to 'e' followed by that number
    text_caption = re.sub(r'\bep(\d+)\b', r'e\1', text_caption, flags=re.IGNORECASE)

        # Convert single-digit 'e' to two-digit 'e'
    text_caption = re.sub(r'\be(\d)\b', r'e0\1', text_caption, flags=re.IGNORECASE)

    # Convert single-digit 's' to two-digit 's'
    text_caption = re.sub(r'\bs(\d)\b', r's0\1', text_caption, flags=re.IGNORECASE)

    # Formatting for season and episode numbers (padding with zeros)
    text_caption = re.sub(r'\bseason (\d+)\b', lambda x: f's{x.group(1).zfill(2)}', text_caption, flags=re.IGNORECASE)
    text_caption = re.sub(r'\bepisode (\d+)\b', lambda x: f'e{x.group(1).zfill(2)}', text_caption, flags=re.IGNORECASE)

    words_to_remove = ["full","video","videos","movie", "movies","series","dubbed","hd","4k","send","file","audio","language","quality","qua","aud","give","files","in"]

    # Create a regular expression pattern with all words to remove
    pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words_to_remove) + r')\b'

    # Remove the specified words in a case-insensitive manner
    text_caption = re.sub(pattern, '', text_caption, flags=re.IGNORECASE)

    # Remove extra spaces between words
    text_caption = re.sub(r'\s+', ' ', text_caption)
    # Replace language abbreviations using a dictionary
    language_abbreviations = {"hin": "hindi", "eng": "english", "tam": "tamil", "tel": "telugu"}
    text_caption = re.sub(
        r"\b(?:hin|eng|tam|tel)\b",
        lambda match: language_abbreviations.get(match.group(0), match.group(0)),
        text_caption
    )
    if len(text_caption) > 35:
        text_caption = text_caption[:35]

    return text_caption

async def adv_process_text(msg):
    words_to_remove = ["480p","1080p","720p","hindi","english","tamil","telugu"]
    try:
        pattern = r'\b(?:' + '|'.join(map(re.escape, words_to_remove)) + r')\b'
        msg.text = re.sub(pattern, '', msg.text)
        query = msg.text
        year_pattern = re.compile(r'\b\d{4}\b')
        year_match = year_pattern.search(query)
        if year_match:
            year = year_match.group(0)
            query = year_pattern.sub('', query)
            words = query.split()
            sorted_words = sorted(words, key=len, reverse=True)
            twow = ' '.join(sorted_words[:1])
            result_string = f"{twow} {year}"
            return result_string
        else:
            query = year_pattern.sub('', query)
            words = query.split()
            sorted_words = sorted(words, key=len, reverse=True)
            result_string = ' '.join(sorted_words[:2])
            return result_string

    except Exception as e:
            pass
        
async def no_resultx(msg,client,text="<i>No Results Found Please Provide Correct Title.</i>"):
    k = await msg.reply_text(f"{text}")
    await client.send_message(chat_id=NO_RES_CNL, text=f"{msg.text}")
    await asyncio.sleep(7)
    await k.delete()
    return

async def result_btn(files, user_id,search,calldatalrg=False):
    inline_buttons = [
    [
        InlineKeyboardButton(
            text=f"{get_size(file.file_size)} › {html.unescape(file.caption[:30].strip())}",
            url=f"https://telegram.dog/{temp.U_NAME}?start=BotFusion_{file.file_id}"
        ),
    ]
    for file in files
]
    if not calldatalrg:
        if IS_VERIFY:
            inline_buttons.insert(0, [
                InlineKeyboardButton('Hᴏᴡ Tᴏ Vᴇʀɪғʏ & Dᴏᴡɴʟᴏᴀᴅ ?', url=HOW_TO_VERIFY)
            ])
        inline_buttons.insert(0, [
            InlineKeyboardButton("Lᴀɴɢᴜᴀɢᴇ", callback_data=f"select_lang#{user_id}#{search}"),
            InlineKeyboardButton("Rᴇsᴏʟᴜᴛɪᴏɴ", callback_data=f"select_qual#{user_id}#{search}"),
            InlineKeyboardButton("Sᴇᴀꜱᴏɴ", callback_data=f"select_season#{user_id}#{search}")
        ])
    else:
        if IS_VERIFY:
            inline_buttons.insert(0, [
                InlineKeyboardButton('Hᴏᴡ Tᴏ Vᴇʀɪғʏ & Dᴏᴡɴʟᴏᴀᴅ ?', url=HOW_TO_VERIFY)
            ])
    return inline_buttons

def imdb_btn(results,user_id):
    keyboard = []
    for i, movie in enumerate(results):
        button = InlineKeyboardButton(f"{movie}", callback_data=f"filterx#{user_id}#all#{movie}")
        keyboard.append([button])
    keyboard.append([
        InlineKeyboardButton(text="⟸",callback_data=f"filterx#{user_id}#close#{movie}")])
    return keyboard

def search_movie(query):
    query_words = query.split()

    if not query_words:
        return []

    unique_movies = set()  # Use a set to store unique movies
    for word in query_words:
        try:
            movies = ia.search_movie(word)
            if movies:
                for movie in movies:
                    title = movie['title']
                    year = movie.get('year', '')
                    result_string = f"{title}"
                    unique_movies.add(result_string)
        except:
            return []

    return list(unique_movies)

def find_matching_movies(input_name, movie_list):
    try:
        matches = process.extract(input_name, movie_list, scorer=fuzz.token_sort_ratio, limit=6)
        threshold = 60
        filtered_matches = [name for name, score in matches if score >= threshold]
        return filtered_matches
    except :
        return []

async def auto_filter(client, msg):
    orgmsg = msg.text

    #s1 process text
    msg.text = await process_text(msg.text)

    #s2 invalid msg
    if len(msg.text) < 2: 
        await no_resultx(msg,client)
        return
    if re.match(r'^\s*$', msg.text): 
        await no_resultx(msg,client)
        return 
    if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", msg.text):
        await no_resultx(msg,client)
        return
    if len(msg.text) > 100:
        await no_resultx(msg,client)
        return
    
    message = msg
    search = message.text
    imdb_seach = False
    #s3 getting results
    files, offset, total_pages = await search_db(search.lower(), offset=0)

    if not files:
        search = await adv_process_text(msg)
        if search != False:
            files, offset, total_pages = await search_db(search.lower(), offset=0)
    if not files:
        s=await message.reply_text("Searching on IMDb...")  
        imdb_seach = True
        search_text = msg.text
        words_to_remove = ["480p","1080p","720p","hindi","english","tamil","telugu"]
        pattern = r'\b(?:' + '|'.join(map(re.escape, words_to_remove)) + r')\b'
        search_text = re.sub(pattern, '', msg.text)
        imdb_results = search_movie(search_text)
        if not imdb_results:
            await s.delete()
            await no_resultx(msg,client,text="<i>No Results Found on IMDb</i>")
            return
        score_results = find_matching_movies(search_text, imdb_results)
        if not score_results:
            await s.delete()
            await no_resultx(msg,client,text="<i>No Results Found on IMDb</i>")
            return
        await s.delete()
        btn = imdb_btn(score_results,msg.from_user.id)
        cap = f"<b>Hᴇʏ{message.from_user.mention},</b>\n\n <i>Did You Mean Any Of This...</i>"

    message.text = search
    if not imdb_seach:
            
        #primary btns
        btn = await result_btn(files,message.from_user.id,search)

        # Navigation buttons
        btn = await navigation_buttons(btn,message, total_pages, offset)

        cap = f"<b>Hᴇʏ {message.from_user.mention},\n\nSearch:</b> {search}"

    result_msg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))

    await asyncio.sleep(DLT)
    await result_msg.delete()
