import logging
from datetime import datetime
from typing import Dict, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

hotel_rooms = {
    101: {"type": "Одноместный", "price": 2500, "available": True, "description": "Уютный номер с одной кроватью"},
    102: {"type": "Одноместный", "price": 2500, "available": True, "description": "Номер с видом на город"},
    103: {"type": "Двухместный", "price": 4000, "available": True, "description": "Номер для двоих с большой кроватью"},
    104: {"type": "Двухместный", "price": 4000, "available": False,
          "description": "Номер с двумя отдельными кроватями"},
    105: {"type": "Люкс", "price": 8000, "available": True, "description": "Просторный номер с гостиной зоной"},
    106: {"type": "Люкс", "price": 8000, "available": True, "description": "Президентский люкс с джакузи"},
}

user_data = {}
bookings = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = (
        f" Добро пожаловать, {user.first_name}!\n"
        f"Я бот для бронирования номеров в отеле.\n\n"
        f" Доступные команды:\n"
        f"/start - Начало работы\n"
        f"/rooms - Показать доступные номера\n"
        f"/book - Забронировать номер\n"
        f"/mybookings - Мои бронирования\n"
        f"/cancel - Отменить бронирование\n"
        f"/help - Помощь\n"
    )
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        " Как пользоваться ботом:\n\n"
        "1.  /rooms - посмотреть доступные номера\n"
        "2.  /book - начать процесс бронирования\n"
        "3.  /mybookings - посмотреть ваши бронирования\n"
        "4.  /cancel - отменить бронирование\n"
        "5.  Просто пишите вопросы в чат!\n\n"
        "Для бронирования вам понадобится:\n"
        "- Выбрать номер\n"
        "- Указать даты заезда и выезда\n"
        "- Указать ваше имя\n"
    )
    await update.message.reply_text(help_text)


async def show_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать доступные номера"""
    available_rooms = {num: info for num, info in hotel_rooms.items() if info["available"]}

    if not available_rooms:
        await update.message.reply_text(" К сожалению, все номера заняты.")
        return

    response = " *Доступные номера:*\n\n"
    for room_num, info in available_rooms.items():
        status = " Свободен" if info["available"] else " Занят"
        response += (
            f"*Номер {room_num}*\n"
            f"Тип: {info['type']}\n"
            f"Цена: {info['price']} руб./ночь\n"
            f"Статус: {status}\n"
            f"Описание: {info['description']}\n\n"
        )

    await update.message.reply_text(response, parse_mode='Markdown')


async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать процесс бронирования"""
    user_id = update.effective_user.id

    available_rooms = {num: info for num, info in hotel_rooms.items() if info["available"]}

    if not available_rooms:
        await update.message.reply_text(" К сожалению, все номера заняты.")
        return

    keyboard = []
    for room_num in available_rooms.keys():
        room_info = hotel_rooms[room_num]
        keyboard.append([InlineKeyboardButton(
            f"Номер {room_num} - {room_info['type']} ({room_info['price']} руб.)",
            callback_data=f"select_room_{room_num}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        " Выберите номер для бронирования:",
        reply_markup=reply_markup
    )


async def select_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора номера"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    room_num = int(query.data.split('_')[-1])

    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['selected_room'] = room_num

    await query.edit_message_text(
        f" Вы выбрали номер {room_num}\n"
        f" Теперь укажите дату заезда в формате ДД.ММ.ГГГГ\n"
        f"Например: 25.12.2024"
    )


async def handle_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода дат"""
    user_id = update.effective_user.id

    if user_id not in user_data or 'selected_room' not in user_data[user_id]:
        await update.message.reply_text(" Пожалуйста, начните бронирование с команды /book")
        return

    text = update.message.text

    try:
        check_in_date = datetime.strptime(text, "%d.%m.%Y").date()

        if check_in_date < datetime.now().date():
            await update.message.reply_text(" Дата заезда не может быть в прошлом!")
            return

        user_data[user_id]['check_in'] = text

        await update.message.reply_text(
            f" Дата заезда: {text}\n"
            f" Теперь укажите дату выезда в формате ДД.ММ.ГГГГ"
        )

    except ValueError:
        await update.message.reply_text(
            " Неверный формат даты!\n"
            "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 25.12.2024"
        )
        return

async def handle_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода даты выезда"""
    user_id = update.effective_user.id

    if user_id not in user_data or 'check_in' not in user_data[user_id]:
        await update.message.reply_text(" Пожалуйста, сначала укажите дату заезда")
        return

    text = update.message.text

    try:
        check_in_str = user_data[user_id]['check_in']
        check_in_date = datetime.strptime(check_in_str, "%d.%m.%Y").date()
        check_out_date = datetime.strptime(text, "%d.%m.%Y").date()

        if check_out_date <= check_in_date:
            await update.message.reply_text(" Дата выезда должна быть позже даты заезда!")
            return

        user_data[user_id]['check_out'] = text

        nights = (check_out_date - check_in_date).days

        await update.message.reply_text(
            f" Дата выезда: {text}\n"
            f" Количество ночей: {nights}\n"
            f" Теперь укажите ваше имя и фамилию:"
        )

    except ValueError:
        await update.message.reply_text(
            " Неверный формат даты!\n"
            "Пожалуйста, введите дату в формате ДД.ММ.ГГГГ"
        )


async def handle_name_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершение бронирования"""
    user_id = update.effective_user.id

    if user_id not in user_data or 'check_out' not in user_data[user_id]:
        await update.message.reply_text(" Пожалуйста, сначала укажите все необходимые данные")
        return

    guest_name = update.message.text.strip()

    if not guest_name or len(guest_name) < 2:
        await update.message.reply_text(" Пожалуйста, введите корректное имя")
        return

    room_num = user_data[user_id]['selected_room']
    check_in = user_data[user_id]['check_in']
    check_out = user_data[user_id]['check_out']

    check_in_date = datetime.strptime(check_in, "%d.%m.%Y").date()
    check_out_date = datetime.strptime(check_out, "%d.%m.%Y").date()
    nights = (check_out_date - check_in_date).days
    price_per_night = hotel_rooms[room_num]['price']
    total_price = price_per_night * nights

    booking_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    booking_data = {
        'user_id': user_id,
        'room_number': room_num,
        'guest_name': guest_name,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'total_price': total_price,
        'booking_id': booking_id
    }

    if user_id not in bookings:
        bookings[user_id] = []
    bookings[user_id].append(booking_data)

    hotel_rooms[room_num]['available'] = False

    confirmation_text = (
        f" *Бронирование подтверждено!*\n\n"
        f" *Детали бронирования:*\n"
        f" ID бронирования: {booking_id}\n"
        f" Гость: {guest_name}\n"
        f" Номер: {room_num}\n"
        f" Заезд: {check_in}\n"
        f" Выезд: {check_out}\n"
        f" Ночей: {nights}\n"
        f" Стоимость за ночь: {price_per_night} руб.\n"
        f" Общая стоимость: *{total_price} руб.*\n\n"
        f"Спасибо за выбор нашего отеля! "
    )

    await update.message.reply_text(confirmation_text, parse_mode='Markdown')

    if user_id in user_data:
        del user_data[user_id]


async def show_my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать бронирования пользователя"""
    user_id = update.effective_user.id

    if user_id not in bookings or not bookings[user_id]:
        await update.message.reply_text("У вас нет активных бронирований.")
        return

    response = " *Ваши бронирования:*\n\n"

    for i, booking in enumerate(bookings[user_id], 1):
        response += (
            f"*Бронирование #{i}*\n"
            f" ID: {booking['booking_id']}\n"
            f" Номер: {booking['room_number']}\n"
            f" Имя: {booking['guest_name']}\n"
            f" Заезд: {booking['check_in']}\n"
            f" Выезд: {booking['check_out']}\n"
            f" Ночей: {booking['nights']}\n"
            f" Стоимость: {booking['total_price']} руб.\n\n"
        )

    keyboard = [[InlineKeyboardButton("Отменить бронирование", callback_data="cancel_booking_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)


async def cancel_booking_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню отмены бронирования"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in bookings or not bookings[user_id]:
        await query.edit_message_text(" У вас нет активных бронирований.")
        return

    keyboard = []
    for i, booking in enumerate(bookings[user_id], 1):
        keyboard.append([InlineKeyboardButton(
            f"Бронирование #{i} - Номер {booking['room_number']} ({booking['check_in']})",
            callback_data=f"cancel_{booking['booking_id']}"
        )])

    keyboard.append([InlineKeyboardButton("↩ Назад", callback_data="back_to_bookings")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        " Выберите бронирование для отмены:",
        reply_markup=reply_markup
    )


async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отмена бронирования"""
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_bookings":
        user_id = query.from_user.id
        if user_id not in bookings or not bookings[user_id]:
            await query.edit_message_text(" У вас нет активных бронирований.")
            return

        response = " *Ваши бронирования:*\n\n"

        for i, booking in enumerate(bookings[user_id], 1):
            response += (
                f"*Бронирование #{i}*\n"
                f" ID: {booking['booking_id']}\n"
                f" Номер: {booking['room_number']}\n"
                f" Имя: {booking['guest_name']}\n"
                f" Заезд: {booking['check_in']}\n"
                f" Выезд: {booking['check_out']}\n"
                f" Ночей: {booking['nights']}\n"
                f" Стоимость: {booking['total_price']} руб.\n\n"
            )

        keyboard = [[InlineKeyboardButton("Отменить бронирование", callback_data="cancel_booking_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
        return

    booking_id = query.data.split('_')[1]
    user_id = query.from_user.id

    booking_to_cancel = None
    for user_bookings in bookings.values():
        for booking in user_bookings:
            if booking['booking_id'] == booking_id and booking['user_id'] == user_id:
                booking_to_cancel = booking
                break

    if not booking_to_cancel:
        await query.edit_message_text(" Бронирование не найдено.")
        return

    room_num = booking_to_cancel['room_number']
    hotel_rooms[room_num]['available'] = True

    bookings[user_id] = [b for b in bookings[user_id] if b['booking_id'] != booking_id]

    await query.edit_message_text(
        f" Бронирование #{booking_id} успешно отменено.\n"
        f"Номер {room_num} теперь доступен для бронирования."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_data:
        if 'selected_room' in user_data[user_id] and 'check_in' not in user_data[user_id]:
            await handle_dates(update, context)
        elif 'check_in' in user_data[user_id] and 'check_out' not in user_data[user_id]:
            await handle_checkout(update, context)
        elif 'check_out' in user_data[user_id]:
            await handle_name_and_finish(update, context)
        else:
            await update.message.reply_text("Пожалуйста, используйте команды из меню /start")
    else:
        await update.message.reply_text(
            " Я не понял ваше сообщение.\n"
            "Используйте команды из меню или /help для справки."
        )


def main() -> None:
    """Запуск бота"""
    BOT_TOKEN = "7822233362:AAHv2uSZdAk2UasHgT58rtpuQ3nuGoHnOFQ"

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rooms", show_rooms))
    application.add_handler(CommandHandler("book", start_booking))
    application.add_handler(CommandHandler("mybookings", show_my_bookings))
    application.add_handler(CommandHandler("cancel", start_booking))

    application.add_handler(CallbackQueryHandler(select_room, pattern="^select_room_"))
    application.add_handler(CallbackQueryHandler(cancel_booking_menu, pattern="^cancel_booking_menu$"))
    application.add_handler(CallbackQueryHandler(cancel_booking, pattern="^cancel_"))
    application.add_handler(CallbackQueryHandler(cancel_booking, pattern="^back_to_bookings$"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print(" Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()