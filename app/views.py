from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json

import logging

from django.views.decorators.csrf import csrf_exempt

logging.basicConfig(level=logging.DEBUG)


@csrf_exempt
def handler(request):
    """
    Entry-point for Django server.
    : param request: request payload.
    : return: response to be serialized as JsonResponse .
    """
    try:
        event = json.loads(request.body.decode())
    except ValueError:
        return JsonResponse({
            'error': 'Ошибка преобразования тела запроса в json для обработки в приложении  Django',
        })

    logging.info(event)
    logging.info(type(event))

    response = {
        "version": event["version"],
        "session": event["session"],
        "response": {
            "end_session": False
        }
    }

    if event["session"]["new"]:
        response["response"]["text"] = "Привет! Как твои дела? Как отметил новый год?"
    else:
        if event["request"]["original_utterance"].lower() in ["хорошо","отлично"]:
            response["response"]["text"] = "Супер! Я за вас рада!"
        elif event["request"]["original_utterance"].lower() in ["плохо", "скучно"]:
            response["response"]["text"] = "Жаль, думаю со мной было бы лучше!"

    return JsonResponse(response)