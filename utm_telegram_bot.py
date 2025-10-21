import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telebot import apihelper
import requests
import urllib.parse
import logging
import re
from typing import Dict, Any
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Set up more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Starting UTM bot initialization")

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Initialize bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")
logger.info(f"Bot token loaded: {BOT_TOKEN[:5]}...")

bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Bot instance created successfully")

def quote_markdown(text: str) -> str:
    """Экранирует спецсимволы MarkdownV2 одним обратным слешем"""
    text = str(text)
    # Characters that need to be escaped in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    # Escape each special character with a single backslash
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text

# Emoji to custom sticker mapping
EMOJI_STICKER_MAP = {
    '👩‍❤️‍👨': 'stickers/lionthumbsup.webp',
    '✈️': 'stickers/telegram.webp',
    '📷': 'stickers/instagram.webp',
    '🕸': 'stickers/google.webp',
    '💸': 'stickers/yandex_direct.webp',
    '👑': 'stickers/tiktok.webp',
    '📹': 'stickers/youtube.webp',
    '👫': 'stickers/odnoklassniki.webp',
    '💌': 'stickers/email.webp',
    '💬': 'stickers/messanger.webp',
    '📍': 'stickers/offline.webp',
    '🎵': 'stickers/mailru.webp',
    '🎈': 'stickers/rutube.webp'
}

def send_emoji_as_sticker(chat_id, emoji):
    """Send custom sticker corresponding to the emoji"""
    if emoji in EMOJI_STICKER_MAP:
        sticker_path = EMOJI_STICKER_MAP[emoji]
        try:
            if os.path.exists(sticker_path):
                with open(sticker_path, 'rb') as sticker:
                    bot.send_sticker(chat_id, sticker)
            else:
                logger.warning(f"Sticker file not found: {sticker_path}")
        except FileNotFoundError:
            logger.warning(f"Sticker file not found: {sticker_path}")
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Telegram API error sending sticker {sticker_path}: {e}")
        except Exception as e:
            logger.error(f"Error sending sticker {sticker_path}: {e}")


class States:
    START = "start"
    COLLECTING_URL = "collecting_url"
    COLLECTING_SOURCE = "collecting_source"
    COLLECTING_MEDIUM = "collecting_medium"
    COLLECTING_CAMPAIGN = "collecting_campaign"
    COLLECTING_TERM = "collecting_term"
    READY_TO_GENERATE = "ready_to_generate"

user_data = {}

def get_user_data(user_id: int) -> Dict[str, Any]:
    if user_id not in user_data:
        user_data[user_id] = {
            'state': States.START,
            'utm_data': {
                'url': '',
                'utm_source': '',
                'utm_medium': '',
                'utm_campaign': '',
                'utm_term': ''
            }
        }
    return user_data[user_id]

def set_user_state(user_id: int, state: str):
    data = get_user_data(user_id)
    data['state'] = state

def get_user_state(user_id: int) -> str:
    return get_user_data(user_id)['state']

UTM_OPTIONS = {
    'source': {
        'yandex_direct': 'Яндекс.Директ',
        'vk': 'ВКонтакте', 
        'telegram': 'Telegram',
        'instagram': 'Instagram',
        'google': 'Google',
        'facebook': 'Facebook',
        'tiktok': 'TikTok',
        'youtube': 'YouTube',
        'custom': '📝 Ввести свой'
    },
    'medium': {
        'cpc': 'CPC (контекстная реклама)',
        'social': 'Социальные сети',
        'email': 'Email рассылка',
        'referral': 'Партнерская программа',
        'organic': 'Органический трафик',
        'display': 'Медийная реклама',
        'video': 'Видеореклама',
        'custom': '📝 Ввести свой'
    },
    'campaign': {
        'summer_sale': 'Летняя распродажа',
        'launch': 'Запуск продукта',
        'retargeting': 'Ретаргетинг',
        'brand': 'Брендинговая кампания',
        'black_friday': 'Черная пятница',
        'new_year': 'Новогодняя акция',
        'custom': '📝 Ввести свой'
    },
    'term': {
        'brand_keywords': 'Брендовые запросы',
        'product_keywords': 'Продуктовые запросы',
        'competitor': 'Конкуренты',
        'broad_match': 'Широкое соответствие',
        'exact_match': 'Точное соответствие',
        'custom': '📝 Ввести свой'
    }
}

def create_utm_keyboard(param_type: str, show_back: bool = False) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for key, value in UTM_OPTIONS[param_type].items():
        callback_data = f"{param_type}_{key}"
        keyboard.add(InlineKeyboardButton(value, callback_data=callback_data))
    
    # Add back button if requested
    if show_back:
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_{param_type}"))
    
    return keyboard

def create_progress_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔄 Заново", callback_data="restart"),
        InlineKeyboardButton("✅ Укоротить", callback_data="generate")
    )
    return keyboard

def create_restart_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("🔄 Создать новую ссылку", callback_data="restart"))
    return keyboard

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    set_user_state(user_id, States.COLLECTING_URL)
    # Send the share image
    with open('stickers/share.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    welcome_text = (
        "Отправь URL, к которому нужно добавить UTM метки.\n\n"
        "Пример: https://pride34.ru/pride-relax/"
    )
    bot.send_message(message.chat.id, quote_markdown(welcome_text), parse_mode='MarkdownV2')

@bot.message_handler(commands=['stats'])
def stats_handler(message):
    """Handler for /stats command to show top 15 links by clicks"""
    # UTM source to emoji mapping
    utm_emoji_map = {
        'vk': '👩‍❤️‍👨',
        'telegram': '✈️',
        'instagram': '📷',
        'google': '🕸',
        'yandex_direct': '💸',
        'tiktok': '👑',
        'youtube': '📹',
        'odnoklassniki': '👫',
        'email': '💌',
        'messanger': '💬',
        'offline': '📍',
        'mailru': '🎵',
        'rutube': '🎈'
    }
    
    try:
        bot.send_message(message.chat.id, "📊 Получаю статистику... Подождите немного")

        # Get stats from YOURLS API
        top_links = get_stats_from_yourls()

        if not top_links:
            bot.send_message(message.chat.id, "❌ Не удалось получить статистику. Сервер недоступен или нет данных для отображения. Попробуйте позже.")
            return

        # Format the stats message
        if top_links:
            stats_message = "*🏆 Топ 15 популярных ссылок по переходам:*\n\n"

            # Collect UTM source data for statistics
            utm_source_stats = {}

            # Send emoji stickers before the stats message
            processed_sources = set()

            for i, link in enumerate(top_links, 1):
                url = link.get('url', 'N/A')
                short_url = link.get('shorturl', 'N/A')
                clicks = int(link.get('clicks', 0))
                title = link.get('title', 'Без названия')

                # Get UTM parameters from URL
                utm_params = []
                parsed_url = urlparse(url)
                query_params = urllib.parse.parse_qs(parsed_url.query)

                utm_source = query_params.get('utm_source', [''])[0]
                utm_medium = query_params.get('utm_medium', [''])[0]
                utm_campaign = query_params.get('utm_campaign', [''])[0]
                utm_term = query_params.get('utm_term', [''])[0]

                # Collect UTM source statistics
                if utm_source:
                    if utm_source in utm_source_stats:
                        utm_source_stats[utm_source] += clicks
                    else:
                        utm_source_stats[utm_source] = clicks

                # Send sticker for this source if not already sent
                if utm_source in utm_emoji_map and utm_source not in processed_sources:
                    send_emoji_as_sticker(message.chat.id, utm_emoji_map[utm_source])
                    processed_sources.add(utm_source)

                # Replace UTM source with emoji if available
                display_utm_source = utm_emoji_map.get(utm_source, utm_source) if utm_source else ''

                if display_utm_source:
                    utm_params.append(display_utm_source)
                if utm_medium:
                    utm_params.append(utm_medium)
                if utm_campaign:
                    utm_params.append(utm_campaign)
                if utm_term:
                    utm_params.append(utm_term)

                utm_string = ' / '.join(utm_params) if utm_params else 'Нет UTM'

                # Truncate long URLs for better display
                if len(short_url) > 30:
                    display_url = short_url[:27] + "..."
                else:
                    display_url = short_url

                # Remove backslashes from title for proper display
                display_title = title.replace('\\', '')

                # New format: Title on first line, short URL on second line
                stats_message += f"{i}. {display_title}\n"
                stats_message += f"   {short_url}\n"
                stats_message += f"   {utm_string}\n"
                stats_message += f"   👁 {clicks} переходов\n\n"

            # Add top UTM sources statistics with emojis
            if utm_source_stats:
                stats_message += "*📈 ТОП источников:*\n"
                # Sort by clicks in descending order and take top 3
                sorted_sources = sorted(utm_source_stats.items(), key=lambda x: x[1], reverse=True)[:3]
                for source, clicks in sorted_sources:
                    emoji = utm_emoji_map.get(source, '')
                    display_source = f"{emoji} {source}" if emoji else source
                    stats_message += f"{quote_markdown(display_source)} — {clicks} кликов\n"

                    # Send sticker for this source if not already sent
                    if source in utm_emoji_map and source not in processed_sources:
                        send_emoji_as_sticker(message.chat.id, utm_emoji_map[source])
                        processed_sources.add(source)

            stats_message += "\n[📊 Аналитика в админке](https://i.pride34.ru/admin/)"
            stats_message += "\n\n_Данные обновляются в реальном времени_"

            # Try sending with Markdown first
            try:
                bot.send_message(
                    message.chat.id, 
                    stats_message, 
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as send_error:
                logger.error(f"Ошибка отправки сообщения со статистикой (Markdown): {send_error}")
                # Try sending without markdown formatting as fallback
                # Create a simplified version without markdown
                simple_stats = "🏆 Топ 15 популярных ссылок по переходам:\n\n"
                for i, link in enumerate(top_links[:15], 1):
                    url = link.get('url', 'N/A')
                    short_url = link.get('shorturl', 'N/A')
                    clicks = int(link.get('clicks', 0))
                    title = link.get('title', 'Без названия')

                    simple_stats += f"{i}. {title}\n"
                    simple_stats += f"   {short_url}\n"
                    simple_stats += f"   {clicks} переходов\n\n"

                bot.send_message(message.chat.id, simple_stats)
        else:
            bot.send_message(message.chat.id, "📭 Пока нет данных для отображения статистики.")

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при получении статистики. Попробуйте позже.")

@bot.message_handler(commands=['help'])
def help_handler(message):
    """Handler for /help command"""
    help_text = """
🔗 *Генератор UTM-ссылок*

*Команды:*
/start - Начать создание UTM-ссылки
/stats - Показать топ 15 популярных ссылок по переходам
/help - Показать это сообщение

*Как использовать:*
1. Отправь команду /start
2. Введи URL для отслеживания
3. Выбери параметры UTM из предложенных или введи свои
4. Получи готовую сокращенную ссылку

*UTM параметры:*
• *utm\\_source* - источник трафика (например: google, facebook)
• *utm\\_medium* - способ привлечения (например: cpc, email)
• *utm\\_campaign* - название кампании
• *utm\\_term* - ключевые слова

Бот автоматически создаст UTM-ссылку и сократит её через ваш сервер.
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == States.COLLECTING_URL)
def collect_url_handler(message):
    user_id = message.from_user.id
    url = message.text.strip()

    # Более строгая проверка URL
    if not url:
        bot.reply_to(message, "URL не может быть пустым. Пожалуйста, введи правильный URL.")
        return

    if not (url.startswith('http://') or url.startswith('https://')):
        bot.reply_to(message, "Пожалуйста, введи правильный URL, который начинается с http:// или https://")
        return

    # Проверка валидности URL
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            bot.reply_to(message, "Некорректный формат URL. Пожалуйста, проверь и попробуй снова.")
            return
    except Exception:
        bot.reply_to(message, "Некорректный формат URL. Пожалуйста, проверь и попробуй снова.")
        return

    # Clean the URL by removing query parameters but keeping fragments
    clean_url_value = clean_url(url)

    data = get_user_data(user_id)
    data['utm_data']['url'] = clean_url_value
    set_user_state(user_id, States.COLLECTING_SOURCE)
    # No back button for the first step (source selection)
    keyboard = create_utm_keyboard('source', show_back=False)
    msg = f"💾 URL сохранен:\n```\n{clean_url_value}\n```\n\nИсточник трафика:"
    bot.send_message(
        message.chat.id,
        msg,
        parse_mode='MarkdownV2',
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call: CallbackQuery):
    user_id = call.from_user.id
    get_user_data(user_id)
    try:
        if call.data == "restart":
            restart_bot(call.message, user_id)
            return
        if call.data == "generate":
            generate_utm_link(call.message, user_id)
            return

        # Check if it's a back button callback
        if call.data.startswith("back_"):
            current_param = call.data.split('_', 1)[1]
            handle_back_button(call, current_param)
            bot.answer_callback_query(call.id)
            return

        # Validate callback data format
        if '_' not in call.data:
            logger.error(f"Invalid callback data format: {call.data}")
            bot.answer_callback_query(call.id, "❌ Invalid request")
            return
            
        param_type, param_value = call.data.split('_', 1)

        if param_value == 'custom':
            handle_custom_input(call, param_type)
        elif param_value == 'skip':
            skip_param(call, param_type)
        elif param_value == 'use_url':
            use_url_for_term(call, param_type)
        else:
            handle_predefined_choice(call, param_type, param_value)
            
        # Send corresponding sticker for the selected option
        emoji_map = {
            'vk': '👩‍❤️‍👨',
            'telegram': '✈️',
            'instagram': '📷',
            'yandex_direct': '💸',
            'google': '🕸',
            'tiktok': '👑',
            'youtube': '📹',
            'odnoklassniki': '👫',
            'email': '💌',
            'messanger': '💬',
            'offline': '📍',
            'mailru': '🎵',
            'rutube': '🎈'
        }
        
        if param_type == 'source' and param_value in emoji_map:
            send_emoji_as_sticker(call.message.chat.id, emoji_map[param_value])
            
        bot.answer_callback_query(call.id)
    except KeyError as e:
        logger.error(f"❌ KeyError in callback handler: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Data not found, try again")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"❌ Ошибка в callback handler: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Произошла ошибка, попробуйте еще раз")
        except Exception:
            pass  # Игнорируем, если callback уже истек

def handle_predefined_choice(call: CallbackQuery, param_type: str, param_value: str):
    user_id = call.from_user.id
    data = get_user_data(user_id)
    if param_value == 'skip':
        data['utm_data'][f'utm_{param_type}'] = ''
    else:
        data['utm_data'][f'utm_{param_type}'] = param_value
    next_step = get_next_step(param_type)
    if next_step:
        set_user_state(user_id, f"collecting_{next_step}")
        # Show back button for all steps except the first one
        show_back = param_type != 'source'
        keyboard = create_utm_keyboard(next_step, show_back)
        progress_text = get_progress_text(data['utm_data'])
        param_names = {
            'medium': quote_markdown('Канал'),
            'campaign': quote_markdown('Название кампании'),
            'term': quote_markdown('Ключевое слово')
        }
        message_text = f"{quote_markdown(progress_text)}\n\n{param_names.get(next_step, next_step)}:"
        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id,
                              reply_markup=keyboard, parse_mode='MarkdownV2')
    else:
        set_user_state(user_id, States.READY_TO_GENERATE)
        show_final_summary(call.message, user_id)

def use_url_for_term(call: CallbackQuery, param_type: str):
    user_id = call.from_user.id
    data = get_user_data(user_id)
    url = data['utm_data'].get('url', '')

    if url:
        path = urlparse(url).path
        last_segment = path.rstrip('/').split('/')[-1]
    else:
        last_segment = ''

    data['utm_data'][f'utm_{param_type}'] = last_segment

    next_step = get_next_step(param_type)
    if next_step:
        set_user_state(user_id, f"collecting_{next_step}")
        # Show back button for all steps except the first one
        show_back = param_type != 'source'
        keyboard = create_utm_keyboard(next_step, show_back)
        progress_text = get_progress_text(data['utm_data'])
        param_names = {
            'medium': quote_markdown('Канал'),
            'campaign': quote_markdown('Название кампании'),
            'term': quote_markdown('Ключевое слово')
        }
        message_text = f"{quote_markdown(progress_text)}\n\n{param_names.get(next_step, next_step)}:"
        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id,
                              reply_markup=keyboard, parse_mode='MarkdownV2')
    else:
        set_user_state(user_id, States.READY_TO_GENERATE)
        show_final_summary(call.message, user_id)

def skip_param(call: CallbackQuery, param_type: str):
    user_id = call.from_user.id
    data = get_user_data(user_id)
    data['utm_data'][f'utm_{param_type}'] = ''
    next_step = get_next_step(param_type)
    if next_step:
        set_user_state(user_id, f"collecting_{next_step}")
        # Show back button for all steps except the first one
        show_back = param_type != 'source'
        keyboard = create_utm_keyboard(next_step, show_back)
        progress_text = get_progress_text(data['utm_data'])
        param_names = {
            'medium': quote_markdown('Канал'),
            'campaign': quote_markdown('Кампания'),
            'term': quote_markdown('Ключевое слово')
        }
        message_text = f"{quote_markdown(progress_text)}\n\n{param_names.get(next_step, next_step)}:"
        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id,
                              reply_markup=keyboard, parse_mode='MarkdownV2')
    else:
        set_user_state(user_id, States.READY_TO_GENERATE)
        show_final_summary(call.message, user_id)

def handle_custom_input(call: CallbackQuery, param_type: str):
    user_id = call.from_user.id
    set_user_state(user_id, f"custom_{param_type}")
    param_names = {
        'source': 'Источник',
        'medium': 'Канал',
        'campaign': 'Кампания',
        'term': 'Ключевое слово'
    }
    bot.edit_message_text(
        f"Введи свое значение для {param_names.get(param_type, param_type)}:",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: get_user_state(message.from_user.id).startswith('custom_'))
def custom_input_handler(message):
    user_id = message.from_user.id
    state = get_user_state(user_id)
    param_type = state.replace('custom_', '')
    custom_value = message.text.strip()
    data = get_user_data(user_id)
    data['utm_data'][f'utm_{param_type}'] = custom_value
    next_step = get_next_step(param_type)
    if next_step:
        set_user_state(user_id, f"collecting_{next_step}")
        # Show back button for all steps except the first one
        show_back = param_type != 'source'
        keyboard = create_utm_keyboard(next_step, show_back)
        progress_text = get_progress_text(data['utm_data'])
        param_names = {
            'medium': quote_markdown('Канал'),
            'campaign': quote_markdown('Кампания'),
            'term': quote_markdown('Ключевое слово')
        }
        message_text = f"💾 Сохранено: {quote_markdown(custom_value)}\n\n{quote_markdown(progress_text)}\n\nТеперь выбери {param_names.get(next_step, next_step)}:"
        bot.send_message(message.chat.id, message_text, reply_markup=keyboard, parse_mode='MarkdownV2')
    else:
        set_user_state(user_id, States.READY_TO_GENERATE)
        bot.reply_to(message, f"💾 Сохранено: {quote_markdown(custom_value)}", parse_mode="MarkdownV2")
        show_final_summary(message, user_id)

def get_next_step(current_param: str) -> str:
    steps = ['source', 'medium', 'campaign', 'term']
    try:
        current_index = steps.index(current_param)
        if current_index + 1 < len(steps):
            return steps[current_index + 1]
        else:
            return None  # Return None when there's no next step
    except ValueError:
        return None  # Return None if current_param is not in steps

def get_progress_text(utm_data: Dict[str, str]) -> str:
    progress = []
    if utm_data.get('url'):
        progress.append(f"URL: {utm_data['url']}")
    utm_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term']
    param_names = {
        'utm_source': 'Источник',
        'utm_medium': 'Канал',
        'utm_campaign': 'Кампания',
        'utm_term': 'Ключевое слово'
    }
    for param in utm_params:
        value = utm_data.get(param, '')
        if value:
            progress.append(f"{param_names[param]}: {value}")
    return "\n".join(progress)

def show_final_summary(message, user_id: int):
    data = get_user_data(user_id)
    utm_data = data['utm_data']
    summary = (
        "📋 Все UTM параметры собраны!\n\n"
        f"{get_progress_text(utm_data)}\n\n"
        "🧲 Готов к укорочиванию ссылки"
    )
    summary = quote_markdown(summary)
    keyboard = create_progress_keyboard()
    bot.send_message(message.chat.id, summary, reply_markup=keyboard, parse_mode='MarkdownV2')

def generate_utm_link(message, user_id: int):
    data = get_user_data(user_id)
    utm_data = data['utm_data']
    try:
        base_url = utm_data['url']
        params = {
            'utm_source': utm_data.get('utm_source', ''),
            'utm_medium': utm_data.get('utm_medium', ''),
            'utm_campaign': utm_data.get('utm_campaign', ''),
            'utm_term': utm_data.get('utm_term', '')
        }
        params = {k: v for k, v in params.items() if v}
        utm_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        loading_msg = bot.send_message(message.chat.id, "⌛️ Генерирую и сокращаю ссылку", parse_mode='MarkdownV2')
        shortened_url = shorten_url(utm_url)
        
        # Extract page title from URL
        parsed_url = urlparse(base_url)
        path = parsed_url.path.rstrip('/')
        page_title = path.split('/')[-1] if path else "Страница"
        
        # Format the message with the new structure
        result_message = (
            f"*Страница:* {page_title}\n"
            f"*✅ Полная UTM ссылка:*\n"
            f"{utm_url}\n\n"
            f"*✅ Короткая ссылка:*\n"
            f"{shortened_url}\n"
        )
        result_message = quote_markdown(result_message)
        keyboard = create_restart_keyboard()
        bot.delete_message(message.chat.id, loading_msg.message_id)
        # Send the lion thumbs up sticker before the final message
        with open('stickers/lionthumbsup.webp', 'rb') as sticker:
            bot.send_sticker(message.chat.id, sticker)
        bot.edit_message_text(result_message, message.chat.id, message.message_id,
                              reply_markup=keyboard, parse_mode='MarkdownV2')
        set_user_state(user_id, States.START)
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации ссылки: {e}")
        bot.send_message(message.chat.id,
                         "❌ Произошла ошибка при генерации ссылки\nПопробуй еще раз",
                         parse_mode='MarkdownV2')

def shorten_url(long_url: str) -> str:
    try:
        api_url = os.getenv('URL_SHORTENER_API', 'http://i.pride34.ru/yourls-api.php')
        signature = os.getenv('URL_SHORTENER_SIGNATURE', 'def05e4247')
        params = {
            'signature': signature,
            'action': 'shorturl',
            'format': 'json',
            'url': long_url
        }
        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'shorturl' in data:
                return data['shorturl']
            else:
                logger.error(f"Ошибка в ответе YOURLS API: {data}")
                return long_url
        else:
            logger.error(f"Ошибка сокращения URL: HTTP {response.status_code}")
            return long_url
    except Exception as e:
        logger.error(f"Ошибка при сокращении URL: {e}")
        return long_url

def get_stats_from_yourls() -> list:
    """Fetch top URLs statistics from YOURLS API"""
    try:
        api_url = os.getenv('URL_SHORTENER_API', 'http://i.pride34.ru/yourls-api.php')
        signature = os.getenv('URL_SHORTENER_SIGNATURE', 'def05e4247')

        # Get links with sorting by clicks
        params = {
            'signature': signature,
            'action': 'stats',
            'format': 'json',
            'limit': 50  # Get more links to ensure we have enough data
        }

        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            stats_data = response.json()
            if 'statusCode' in stats_data and str(stats_data['statusCode']) == '200':
                if 'links' in stats_data:
                    # The links are in a nested structure, extract them
                    links_dict = stats_data['links']
                    if isinstance(links_dict, dict):
                        # Convert dict to list and sort by clicks
                        links_list = list(links_dict.values())
                        # Sort by clicks in descending order
                        links_list.sort(key=lambda x: int(x.get('clicks', 0)), reverse=True)
                        return links_list[:15]  # Top 15 links
                    elif isinstance(links_dict, list):
                        # If links is already a list
                        links_list = links_dict
                        links_list.sort(key=lambda x: int(x.get('clicks', 0)), reverse=True)
                        return links_list[:15]  # Top 15 links
                    else:
                        return []
                else:
                    logger.error(f"Нет ключа 'links' в ответе YOURLS API: {stats_data}")
                    return []
            else:
                logger.error(f"Ошибка в ответе YOURLS API: {stats_data}")
                return []
        else:
            logger.error(f"Ошибка получения статистики из YOURLS API: HTTP {response.status_code}")
            return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Ошибка подключения к YOURLS API: {e}")
        return []
    except requests.exceptions.Timeout as e:
        logger.error(f"Таймаут при подключении к YOURLS API: {e}")
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        return []

def restart_bot(message, user_id: int):
    try:
        if user_id in user_data:
            del user_data[user_id]
    except KeyError:
        pass  # Пользовательские данные уже удалены
    set_user_state(user_id, States.COLLECTING_URL)
    bot.edit_message_text("Начинаем заново!\n\nОтправь URL, к которому нужно добавить UTM метки:",
                          message.chat.id,
                          message.message_id,
                          parse_mode='MarkdownV2')

def handle_back_button(call: CallbackQuery, current_param: str):
    """Handle back button navigation between UTM parameter steps"""
    user_id = call.from_user.id
    data = get_user_data(user_id)
    
    # Determine the previous step
    steps = ['source', 'medium', 'campaign', 'term']
    try:
        current_index = steps.index(current_param)
        if current_index > 0:
            # Go back to the previous step
            prev_step = steps[current_index - 1]
            set_user_state(user_id, f"collecting_{prev_step}")
            
            # Show back button for all steps except the first one
            show_back = prev_step != 'source'
            keyboard = create_utm_keyboard(prev_step, show_back)
            
            # Update the message with the previous step
            progress_text = get_progress_text(data['utm_data'])
            param_names = {
                'source': quote_markdown('Источник трафика'),
                'medium': quote_markdown('Канал'),
                'campaign': quote_markdown('Название кампании'),
                'term': quote_markdown('Ключевое слово')
            }
            message_text = f"{quote_markdown(progress_text)}\n\n{param_names.get(prev_step, prev_step)}:"
            bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id,
                                  reply_markup=keyboard, parse_mode='MarkdownV2')
        else:
            # Already at the first step, go back to URL input
            set_user_state(user_id, States.COLLECTING_URL)
            # Clear the URL from data
            data['utm_data']['url'] = ''
            welcome_text = (
                "Отправь URL, к которому нужно добавить UTM метки.\n\n"
                "Пример: https://pride34.ru/pride-relax/"
            )
            bot.edit_message_text(quote_markdown(welcome_text), call.message.chat.id, call.message.message_id,
                                  parse_mode='MarkdownV2')
    except ValueError:
        # If current_param is not in steps, go back to start
        set_user_state(user_id, States.COLLECTING_URL)
        welcome_text = (
            "Отправь URL, к которому нужно добавить UTM метки.\n\n"
            "Пример: https://pride34.ru/pride-relax/"
        )
        bot.edit_message_text(quote_markdown(welcome_text), call.message.chat.id, call.message.message_id,
                              parse_mode='MarkdownV2')

def clean_url(url: str) -> str:
    """Remove query parameters from URL, keeping the base URL and fragments"""
    try:
        parsed = urlparse(url)
        # Reconstruct URL with scheme, netloc, path, and fragment, but without query parameters
        if parsed.fragment:
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}#{parsed.fragment}"
        else:
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return clean_url
    except Exception:
        # If parsing fails, return the original URL
        return url

if __name__ == "__main__":
    try:
        logger.info("Запуск UTM бота")
        logger.info(f"Используется токен: {BOT_TOKEN[:5]}...")
        logger.info("Начинаем polling...")
        bot.polling(none_stop=True, interval=0, timeout=20)
        logger.info("Polling завершен")
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except telebot.apihelper.ApiTelegramException as e:
        if '409' in str(e):
            logger.error("Ошибка 409: Бот уже запущен в другом процессе. Убедитесь, что только один экземпляр бота запущен.")
        else:
            logger.error(f"Ошибка Telegram API: {e}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        import traceback
        logger.error(f"Полный traceback: {traceback.format_exc()}")
        raise
