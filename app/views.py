

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json

import logging
from project.settings import LOGGING_LEVEL


from django.views.decorators.csrf import csrf_exempt


from app.state import STATE_REQUEST_KEY, STATE_RESPONSE_KEY
from app.scenes import SCENES, DEFAULT_SCENE
from app.request_helpers import Request


logging.basicConfig(level=LOGGING_LEVEL)

@csrf_exempt
def handler(request):
    """
    Main handler for Alice Skill
    """
    try:
        event = json.loads(request.body.decode())
    except ValueError:
        logging.info('Ошибка преобразования тела запроса в json для обработки в приложении  Django')
        return JsonResponse({
            'error': 'Ошибка преобразования тела запроса в json для обработки в приложении  Django',
        })

    logging.info(event)
    logging.info(type(event))

    req = Request(event)
    current_scene_id = event.get('state', {}).get(STATE_REQUEST_KEY, {}).get('scene')
    logging.info(f'Текущая сцена:  {str(current_scene_id)}')
    if current_scene_id is None:
        return DEFAULT_SCENE().reply(request)
    current_scene = SCENES.get(current_scene_id, DEFAULT_SCENE)()
    next_scene = current_scene.move(req)
    if next_scene is not None:
        logging.info(f'Переход из сцены {current_scene.id()} в {next_scene.id()}')
        return next_scene.reply(req)
    else:
        logging.info(f'Ошибка в разборе пользовательского запроса в сцене {current_scene.id()}')
        return current_scene.fallback(req)


# @csrf_exempt
# def handler(request):
#     """
#     This code need to check communication in the middle of VPS and Alice Dialog
#     Entry-point for Django server.
#     : param request: request payload.
#     : return: response to be serialized as JsonResponse .
#     """
#     try:
#         event = json.loads(request.body.decode())
#     except ValueError:
#         return JsonResponse({
#             'error': 'Ошибка преобразования тела запроса в json для обработки в приложении  Django',
#         })
#
#     logging.info(event)
#     logging.info(type(event))
#
#     response = {
#         "version": event["version"],
#         "session": event["session"],
#         "response": {
#             "end_session": False
#         }
#     }
#
#     if event["session"]["new"]:
#         response["response"]["text"] = "Привет! Как твои дела? Как отметил новый год?"
#     else:
#         if event["request"]["original_utterance"].lower() in ["хорошо","отлично"]:
#             response["response"]["text"] = "Супер! Я за вас рада!"
#         elif event["request"]["original_utterance"].lower() in ["плохо", "скучно"]:
#             response["response"]["text"] = "Жаль, думаю со мной было бы лучше!"
#
#     return JsonResponse(response)