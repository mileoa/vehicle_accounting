import logging
import aiohttp
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

DJANGO_API_URL = "http://localhost:8081/api/"
authorized_users_jwt = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in authorized_users_jwt:
        await update.message.reply_text("Вы уже авторизованы!")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Для начала работы вызовите команду "/login [логин] [пароль]"',
    )


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if authorized_users_jwt.get(user_id):
        await update.message.reply_text("Вы уже авторизованы!")
        return

    message_words = update.message.text.split()
    if len(message_words) != 3:
        await update.message.reply_text(
            'Неправильный формат. Используйте команду: "/login [логин] [пароль]"'
        )
        return

    username = message_words[1]
    password = message_words[2]
    auth_result = await set_jwt_token(username, password, user_id)
    if not auth_result["success"]:
        await update.message.reply_text(auth_result["error"])
        return

    await update.message.reply_text("Вы успешно авторизованы!")


async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await logout(user_id)
    await update.message.reply_text(
        'Вы разлогинены. Для повторного входа используйте команду: "/login [логин] [пароль]"'
    )


async def get_vehicle_millage_by_period_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    message_words = update.message.text.split()
    if len(message_words) != 5:
        await update.message.reply_text(
            "Необходимо указать следующие параметры: [id автомобиля] [период: day, week, month, year] [дата начала в формате YYYY-MM-DD] [дата окончания в формате YYYY-MM-DD]"
        )
        return
    vehicle_id = message_words[1]
    period = message_words[2]
    start_date = message_words[3]
    end_date = message_words[4]

    request_url = f"{DJANGO_API_URL}vehicle_mileage_report/?vehicle_id={vehicle_id}&period={period}&start_date={start_date}&end_date={end_date}"
    result = await make_request_with_jwt(update, request_url)
    if not result["success"]:
        await update.message.reply_text(str(result["error"]))
        return
    formatted_message = await format_mileage_report(result["data"])
    await update.message.reply_text(formatted_message, parse_mode="Markdown")


async def format_mileage_report(json):

    # Форматирование отчета
    message = f"🚗 *{json['title']}*\n\n"

    for vehicle_id, vehicle_data in json["data"].items():
        message += f"🚙 *{vehicle_data['name']}*\n"
        message += "📊 По периодам:\n"

        for period_id, period_data in vehicle_data["periods"].items():
            km = period_data["value"]
            message += f"  • {period_data['label']}: {km:.2f} км\n"

        message += (
            f"\n📈 *Итого по автомобилю:* {vehicle_data['total']:.2f} км\n\n"
        )

    message += f"🏁 *Общий пробег:* {json['totals']['mileage_km']:.2f} км"

    return message


async def logout(user_id):
    if authorized_users_jwt.get(user_id):
        authorized_users_jwt.pop(user_id)
    return


async def set_jwt_token(username, password, user_id):
    url = f"{DJANGO_API_URL}token/"
    auth_data = {"username": username, "password": password}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                json=auth_data,
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status != 200:
                    return {
                        "success": False,
                        "error": "Неверные учетные данные",
                    }

                data = await response.json()
                if not authorized_users_jwt.get(user_id):
                    authorized_users_jwt[user_id] = {}
                authorized_users_jwt[user_id]["token"] = data.get("access")
                authorized_users_jwt[user_id]["refresh_token"] = data.get(
                    "refresh"
                )
                return {
                    "success": True,
                }

        except Exception:
            return {"success": False, "error": "Неверные учетные данные"}


async def refresh_jwt_token(user_id):
    url = f"{DJANGO_API_URL}token/refresh/"
    refresh_token = authorized_users_jwt[user_id]["refresh_token"]
    auth_data = {"refresh": refresh_token}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                json=auth_data,
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    authorized_users_jwt[user_id]["token"] = data.get("access")
                    return {
                        "success": True,
                    }
            await logout(user_id)
            return {
                "success": False,
                "error": "Время жизни refresh токена закончилось.",
            }

        except Exception:
            return {
                "success": False,
                "error": "Время жизни refresh токена закончилось.",
            }


async def make_request_with_jwt(update: Update, url, attempts_remains=2):
    if attempts_remains == 0:
        return {
            "success": False,
            "error": "Не удалось выполнить запрос",
        }
    user_id = update.effective_user.id
    if not authorized_users_jwt.get(user_id):
        return {
            "success": False,
            "error": 'Вы не вошли в систему. Для входа используйте команду: "/login [логин] [пароль]"',
        }
    token = authorized_users_jwt[user_id]["token"]
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "data": data,
                    }

                data = await response.json()
                if isinstance(data, list):
                    return {
                        "success": False,
                        "error": data[0],
                    }

                # Обработка обновления истекшего jwt токена
                refresh_jwt_result = False
                data = await response.json()
                if data.get("code") == "token_not_valid":
                    refresh_jwt_result = await refresh_jwt_token(user_id)
                elif (
                    data.get("detail")
                    and "cannot connect to host"
                    not in data.get("detail").lower()
                ):
                    return {
                        "success": False,
                        "error": data.get("detail"),
                    }
                else:
                    return {
                        "success": False,
                        "error": "Непредвиденная ошибка",
                    }
                if not refresh_jwt_result:
                    await logout(user_id)
                    return {
                        "success": False,
                        "error": 'Вы разлогинены. Для повторного входа используйте команду: "/login [логин] [пароль]"',
                    }
                return await make_request_with_jwt(
                    update, url, attempts_remains - 1
                )

        except Exception as e:
            return {
                "success": False,
                "error": e,
            }


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
    login_handler = CommandHandler("login", login_command)
    logout_handler = CommandHandler("logout", logout_command)
    start_handler = CommandHandler("start", start_command)
    vehicle_millage_handler = CommandHandler(
        "vehicle_mill", get_vehicle_millage_by_period_command
    )
    application.add_handler(start_handler)
    application.add_handler(login_handler)
    application.add_handler(logout_handler)
    application.add_handler(vehicle_millage_handler)

    application.run_polling()
