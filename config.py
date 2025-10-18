"""
Конфигурация для UTM Telegram бота
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Токен бота (получить у @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# URL вашего сервиса сокращения ссылок
URL_SHORTENER_API = os.getenv('URL_SHORTENER_API', 'http://i.pride34.ru/yourls-api.php')
URL_SHORTENER_SIGNATURE = os.getenv('URL_SHORTENER_SIGNATURE', 'def05e4247')

# Настройки базы данных (если используете)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///utm_bot.db')

# Настройки Redis (если используете для хранения состояний)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Максимальная длина UTM параметра
MAX_UTM_PARAM_LENGTH = int(os.getenv('MAX_UTM_PARAM_LENGTH', '100'))

# Таймаут для HTTP запросов
HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', '10'))

# Предустановленные опции для UTM параметров
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

# Сообщения бота
MESSAGES = {
    'welcome': """
🔗 **Генератор UTM-ссылок**

Привет! Я помогу тебе создать ссылку с UTM-метками для отслеживания эффективности рекламных кампаний.

📝 Для начала, отправь мне URL, к которому нужно добавить UTM-метки.

Пример: https://example.com/product
    """,

    'url_saved': "✅ URL сохранен: {url}\n\n📊 Теперь выбери источник трафика (utm_source):",

    'invalid_url': "❌ Пожалуйста, введи корректный URL, начинающийся с http:// или https://",

    'processing': "🔄 Генерирую и сокращаю ссылку...",

    'success': """
✅ **Ссылка готова!**

🔗 **Полная UTM-ссылка:**
`{full_url}`

🎯 **Сокращенная ссылка:**
`{short_url}`

📊 **UTM параметры:**
{utm_params}

Для создания новой ссылки отправь /start
    """,

    'error': "❌ Произошла ошибка при генерации ссылки. Попробуй еще раз.",

    'help': """
🔗 **Генератор UTM-ссылок**

**Команды:**
/start - Начать создание UTM-ссылки
/stats - Показать топ 15 популярных ссылок по переходам
/help - Показать это сообщение

**Как использовать:**
1. Отправь команду /start
2. Введи URL для отслеживания
3. Выбери параметры UTM из предложенных или введи свои
4. Получи готовую сокращенную ссылку

**UTM параметры:**
• utm_source - источник трафика (например: google, facebook)
• utm_medium - способ привлечения (например: cpc, email)  
• utm_campaign - название кампании
• utm_term - ключевые слова

Бот автоматически создаст UTM-ссылку и сократит её через ваш сервер.
    """
}