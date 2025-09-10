from django.shortcuts import render


def custom_handler403(request, exception):

    return render(
        request=request,
        template_name="errors/error_page.html",
        status=403,
        context={
            "title": "Ошибка доступа: 403",
            "error_message": "Доступ к этой странице ограничен",
        },
    )


def custom_handler401(request, exception):

    return render(
        request=request,
        template_name="errors/error_page.html",
        status=401,
        context={
            "title": "Ошибка доступа: 401",
            "error_message": "Страница доступна только авторизированным пользователям",
        },
    )
