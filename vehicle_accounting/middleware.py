import time
import datetime
from threading import local

thread_locals = local()


# class RequestTimeMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         thread_locals.path = request.path
#         thread_locals.sql_count = 0
#         thread_locals.sql_total = 0

#         # Засекаем время начала
#         start_time = time.monotonic()
#         timestamp = time.time()

#         # Обрабатываем запрос
#         response = self.get_response(request)

#         # Вычисляем время выполнения в микросекундах
#         request_time_ms = round((time.monotonic() - start_time) * 1000, 3)
#         request_time_us = int(request_time_ms * 1000)

#         # Получаем данные для лога
#         client_ip = self.get_client_ip(request)
#         method = request.method
#         path = request.get_full_path()
#         protocol = request.META.get("SERVER_PROTOCOL", "HTTP/1.1")
#         status_code = response.status_code
#         response_size = (
#             len(response.content) if hasattr(response, "content") else 0
#         )
#         user_agent = request.META.get("HTTP_USER_AGENT", "-")
#         referer = request.META.get("HTTP_REFERER", "-")

#         # Форматируем timestamp в формате Apache
#         dt = datetime.datetime.fromtimestamp(timestamp)
#         formatted_time = dt.strftime("%d/%b/%Y:%H:%M:%S %z")
#         if not formatted_time.endswith(" +0000"):
#             formatted_time = dt.strftime("%d/%b/%Y:%H:%M:%S +0000")

#         log_line = (
#             f"{client_ip} - - [{formatted_time}] "
#             f'"{method} {path} {protocol}" {status_code} {response_size} '
#             f'"{referer}" "{user_agent}" {request_time_us} '
#             f"sql_count:{thread_locals.sql_count} "
#             f"sql_time:{round(thread_locals.sql_total * 1000, 3)}ms"
#         )

#         # Записываем в файл
#         with open("/var/log/elasticsearch/request.log", "a") as f:
#             f.write(log_line + "\n")

#         # Очищаем thread_locals
#         thread_locals.sql_total = 0
#         thread_locals.sql_count = 0
#         thread_locals.path = ""

#         return response

#     def get_client_ip(self, request):
#         """Получает реальный IP клиента с учетом прокси"""
#         x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
#         if x_forwarded_for:
#             ip = x_forwarded_for.split(",")[0].strip()
#         else:
#             ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
#         return ip
