import random

from django.http import JsonResponse
import enum
import inspect
import sys
from abc import ABC, abstractmethod
from typing import Optional
import json

import app.intents
from app.request_helpers import Request
from app.response_helpers import (
    button,
    image_gallery,
)
from app.state import STATE_REQUEST_KEY, STATE_RESPONSE_KEY, STATE_USER_UPDATE_KEY
import app.intents as intents

import logging
from project.settings import LOGGING_LEVEL

logging.basicConfig(level=LOGGING_LEVEL)

class Prof(enum.Enum):
    UNKNOWN = 1
    ANALYST = 2
    TESTER = 3
    # состояния ниже и их обработка  введены для возможности получения помощи и перехода в начало теста
    WELCOMETEST = 4
    HELPME = 5

    @classmethod
    def from_request(cls, request: Request, intent_name: str):
        slots = request.intents
        slot = request.intents.get(intent_name, {})
        logging.info(f'СЛОТЫ Тип: {type(slots)}, Значение: {slots}, Один слот: {slot} ')
        if slot != {}:
            slot = request.intents[intent_name]['slots']['prof']['value']
        elif intents.START_TOUR_TEST in request.intents:
            return cls.WELCOMETEST
        elif intents.HELP_ME in request.intents:
            return cls.HELPME
        if slot == 'analyst':
            return cls.ANALYST
        elif slot == 'tester':
            return cls.TESTER
        else:
            return cls.UNKNOWN


def move_to_prof_scene(request: Request, intent_name: str):
    prof = Prof.from_request(request, intent_name)
    if prof == Prof.ANALYST:
        return Analyst()
    elif prof == Prof.TESTER:
        return Tester()
    elif prof == Prof.WELCOMETEST:
        return WelcomeTest()
    elif prof == Prof.HELPME:
        return HelpMe()
    else:
        return UnknownProf()


class Scene(ABC):

    @classmethod
    def id(cls):
        return cls.__name__

    """Генерация ответа сцены"""

    @abstractmethod
    def reply(self, request):
        raise NotImplementedError()

    """Проверка перехода к новой сцене"""

    def move(self, request: Request):
        next_scene = self.handle_local_intents(request)
        if next_scene is None:
            next_scene = self.handle_global_intents(request)
        return next_scene

    @abstractmethod
    def handle_global_intents(self):
        raise NotImplementedError()

    @abstractmethod
    def handle_local_intents(self, request: Request) -> Optional[str]:
        raise NotImplementedError()

    def fallback(self, request: Request):
        term_1 = random.choice([
            "Похоже сегодня магнитные бури. Давайте по проще.",
            "У меня сегодня  болит голова. Давайте по проще.",
            "Вчера была вечеринка и я туго соображаю. Давайте по проще.",
            "Банальности. С ними скучно и без них не обойтись. Давайте попроще.",
            "Говорят: Будь проще, и люди к тебе потянутся.",
            "Слово — что камень: коли метнёт его рука, то уж потом назад не воротишь. Но мне непонятно что за камень.",
            "Ой. Я немного замечталась. И жду.",
            "Глухой и тишины не услышит, вот и я не услышала ваш ответ",
            "Если ты хочешь что-то изменить, перестаньте хотеть и начинайте менять. Поменяйте ответ.",
        ])

        term_2 = f'Извините, я вас не поняла. Пожалуйста, попробуйте переформулировать.'
        term_3 = f'Ответьте на вопрос Да или Нет?'

        if "Query" in self.__class__.__name__:
            text = f'{term_1} {term_3}'
        else:
            text = f'{term_1} {term_2}'
        # text = ('Извините, я вас не поняла. Пожалуйста, попробуйте переформулировать.')
        # state=request.state
        # events=make_events(str(whoami()), event),
        return self.make_response(
            text,
            # state,
        )

    def make_response(self, text, tts=None, card=None, state=None, buttons=None, directives=None,
                      state_user_update=None, end_session=False):
        response = {
            'text': text,
            'tts': tts if tts is not None else text,
        }
        if card is not None:
            response['card'] = card
        if buttons is not None:
            response['buttons'] = buttons
        if directives is not None:
            response['directives'] = directives
        webhook_response = {
            'response': response,
            'version': '1.0',
            STATE_RESPONSE_KEY: {
                'scene': self.id(),
            },
        }
        if state is not None:
            webhook_response[STATE_RESPONSE_KEY].update(state)
        if state_user_update is not None:
            webhook_response[STATE_USER_UPDATE_KEY] = state_user_update
        if end_session:
            response['end_session'] = end_session
        return JsonResponse(webhook_response)


class TestTourScene(Scene):
    '''Main class for all scenario's branch'''

    def handle_global_intents(self, request):
        if intents.START_TOUR_TEST in request.intents:
            return WelcomeTest()
        # elif intents.START_TOUR in request.intents:
        #     return StartTour()
        elif intents.HELP_ME in request.intents:
            return HelpMe()
        elif intents.U_STOP in request.intents:
            return ExitSkill()


class HelpMe(TestTourScene):
    def reply(self, request: Request):
        text = ('Я могу помочь Вам определиться с профессией при помощи короткого и занимательного '
                'теста. Или, если Вы уже работаете в АйТи - найти другие свои сильные стороны. '
                'Если хотите начать всё сначала, скажите "Начни с начала"; '
                'Если появились дела по-важнее? скажите: "Стоп"; '
                'Если хотите вернуться к предыдущему вопросу скажите: "Назад"; '
                'Прослушали вопрос? Скажите "Повтори".')
        # state=request.state
        logging.info(f'ПОМОЩЬ: {request.state}')
        add_state = {'prev_scene': request.state}
        return self.make_response(
            text,
            state=add_state,
        )

    def handle_local_intents(self, request: Request):
        if intents.WILL_CONTINUE in request.intents:
            logging.info(f'ОБРАБОТКА ПОМОЩИ: {request.prev_state}')
            next_scene = SCENES.get(request.prev_state, DEFAULT_SCENE)()
            logging.info(f'ОБРАБОТКА ПОМОЩИ СЛЕД СЦЕНА: {next_scene}')
            return next_scene
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()
        # по умолчанию если не условие то уйдет в fallback

class UnderConstraction(TestTourScene):
    ''' Class for developing and testing. Need to delete on production.'''
    def reply(self, request: Request):
        text = ('Ветка дальше на реконструкиции. Чтобы начать сначала, скажите "Продолжить"')
        # state=request.state
        logging.info(f'ПОМОЩЬ: {request.state}')
        add_state = {'prev_scene': request.state}
        return self.make_response(
            text,
            buttons=[
                button('Продолжить', hide=True),
            ],
            state=add_state,
        )

    def handle_local_intents(self, request: Request):
        if intents.WILL_CONTINUE in request.intents:
            logging.info(f'ПОШЛИ НА НОВЫЙ КРУГ ТЕСТИРОВАНИЯ')
            return WelcomeTest()
        # по умолчанию если не условие то уйдет в fallback



class ExitSkill(TestTourScene):
    def reply(self, request: Request):
        text = ('Надеюсь Вам понравился мой тест. Если захотите пообщаться снова - обращайтесь.  До скорого!')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Начни с начала', hide=True),
                button('Пока', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.START_TOUR_TEST in request.intents:
            return WelcomeTest()
        elif intents.U_STOP in request.intents:
            return self.make_response(text="", end_session=True)
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()
        elif intents.HELP_ME in request.intents:
            return HelpMe()


class WelcomeTest(TestTourScene):
    def reply(self, request: Request):
        # scenes = str(SCENES)
        text = ('Привет, дорогой друг! ' 
                'Я могу помочь Вам определиться с профессией при помощи короткого '
                'и занимательного теста. Или, если Вы уже работаете в АйТи - найти '
                'другие свои сильные стороны. Кстати, сама я в АйТи не работаю, '
                'поэтому не обижайся, если профессию подберу неправильно. '
                'Ну что, хотите пройти небольшой тест?')
        # тестирование сохранения параметров пользователя между сессиями
        # state_user_update = {'value': '42'} - записать
        # state_user_update={'value': None} - стереть
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
            # state_user_update = state_user_update, # добавлен параметр в функцию
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Query_1()
        elif intents.U_NOT in request.intents:
            return ReOffer()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()
        # по умолчанию если не условия выше, то переходим в fallback
        # по глобальному условию также есть ExitSkill и HelpMe

    def fallback(self, request: Request):
        text = ('Извините, я вас не поняла. Мы таки идем в тест? ')
        # state=request.state
        # events=make_events(str(whoami()), event),
        return self.make_response(
            text,
            # state=state,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )


class ReOffer(TestTourScene):
    def reply(self, request: Request):
        text = ('Поиск себя-это не страшно, а очень даже нужно. Может все-таки попробуем?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Query_1()
        elif intents.U_NOT in request.intents:
            return ExitSkill()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()

    def fallback(self, request: Request):
        text = ('Извините, я вас не поняла. Все таки Да или Нет? ')
        # state=request.state
        # events=make_events(str(whoami()), event),
        return self.make_response(
            text,
            # state=state,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )


class Query_1(TestTourScene):
    def reply(self, request: Request):
        text = (' Отлично! Следуйте за мной, я во всем помогу! Итак, первый вопрос: '
                ' Любили ли Вы математику в школе, даже несмотря на математичку?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return UnderConstraction()
        elif intents.U_NOT in request.intents:
            return Query1_2()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query1_2(TestTourScene):
    def reply(self, request: Request):
        text = ('Входят ли гигантские шахматы в олимпийские игры?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Query1_3()
        elif intents.U_NOT in request.intents:
            return Query1_3()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query1_3(TestTourScene):
    def reply(self, request: Request):
        text = ('Нравится ли Вам организовывать рабочий процесс и руководить людьми, как дирижер оркестром?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return UnderConstraction()
        elif intents.U_NOT in request.intents:
            return Query1_4()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query1_4(TestTourScene):
    def reply(self, request: Request):
        text = ('Хлопья с молоком - это суп?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Query1_5()
        elif intents.U_NOT in request.intents:
            return Query1_5()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query1_5(TestTourScene):
    def reply(self, request: Request):
        text = ('Вас раздаражает беспорядок?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Query1_6()
        elif intents.U_NOT in request.intents:
            return Query1_6()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query1_6(TestTourScene):
    def reply(self, request: Request):
        text = ('Любите ли Вы замечать прекрасное вокруг и создавать новое, как Леонардо Да Винчи?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Designer()
        elif intents.U_NOT in request.intents:
            return Query2()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Designer(TestTourScene):
    def reply(self, request: Request):
        text = ('По моим подсчётам Вам подходит профессия: '
                'Дизайнер — специалист, который создает облик различных объектов, воплощая '
                'в жизнь визуальные задумки, будь то чайник на Вашей кухне,  спутник в '
                'космосе, или приложение на смартфоне. Хотели бы Вы обучиться этой профессии?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return DesignerOffer()
        elif intents.U_NOT in request.intents:
            return Query1_7()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()

    def fallback(self, request: Request):
        text = ('Извините, я вас не поняла. Все таки Да или Нет? ')
        # state=request.state
        # events=make_events(str(whoami()), event),
        return self.make_response(
            text,
            # state=state,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )


class DesignerOffer(TestTourScene):
    def reply(self, request: Request):
        text = ('Чтобы войти в профессию, Вы можете окончить один из курсов по '
                'дизайну онлайн школы Contented, а по моему секретному промокоду '
                '"ЛеоДаВинчи" получить скидку 10% на любой выбранный Вами курс! '
                'Ну что, готовы к новым знаниям?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return ExitSkill()
        elif intents.U_NOT in request.intents:
            return Query1_7()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()

    def fallback(self, request: Request):
        text = ('Извините, я вас не поняла. Все таки Да или Нет? ')
        # state=request.state
        # events=make_events(str(whoami()), event),
        return self.make_response(
            text,
            # state=state,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )


class Query1_7(TestTourScene):
    def reply(self, request: Request):
        text = ('Если Вам не подошел результат теста - не расстраивайтесь, '
                'ведь даже Мерилин Монро говорила: "Всегда верь в себя, потому '
                'что если ты не поверишь, то кто другой поверит?" '
                'Ну что, пройдем тест еще раз?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return WelcomeTest()
        elif intents.U_NOT in request.intents:
            return ExitSkill()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query2(TestTourScene):
    def reply(self, request: Request):
        text = ('А правда, что Вы не представляете свой день без соц. сетей?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Query2_1()
        elif intents.U_NOT in request.intents:
            return UnderConstraction()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query2_1(TestTourScene):
    def reply(self, request: Request):
        text = ('Хотели бы вы настраивать рекламу и продвигать бизнес?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return InternetMarketer()
        elif intents.U_NOT in request.intents:
            return UnderConstraction()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class InternetMarketer(TestTourScene):
    def reply(self, request: Request):
        text = ('По моим подсчётам Вам подходит профессия: Интернет-маркетолог '
                ' — ещё говорят digital-маркетолог — отвечает за продвижение '
                'бизнеса в интернете. Этот специалист предлагает руководителям '
                'компании идеи. Только он знает как продавать больше и привлекать '
                'клиентов дешевле и вывести компанию в рейтинг крупнейших брендов мира.')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return Query2_2()
        elif intents.U_NOT in request.intents:
            return Query2_3()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()

    def fallback(self, request: Request):
        text = ('Извините, я вас не поняла. Все таки Да или Нет? ')
        # state=request.state
        # events=make_events(str(whoami()), event),
        return self.make_response(
            text,
            # state=state,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )


class Query2_2(TestTourScene):
    def reply(self, request: Request):
        text = ('Чтобы войти в профессию, Вы можете окончить один из курсов по '
                'Интернет маркетингу онлайн школы Skill Factory, а по моему '
                'секретному промокоду "ЛеоДаВинчи" получить скидку 10% на '
                'любой выбранный Вами курс!Ну что, готовы к новым знаниям?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return ExitSkill()
        elif intents.U_NOT in request.intents:
            return Query2_3()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class Query2_3(TestTourScene):
    def reply(self, request: Request):
        text = ('Если Вам не подошел результат теста - не расстраивайтесь, '
                'ведь даже Марк Твен говорил: «Секрет успеха в том, чтобы '
                'сделать первый шаг». Ну что, пройдем тест еще раз?')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return WelcomeTest()
        elif intents.U_NOT in request.intents:
            return ExitSkill()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()


class NextQ(TestTourScene):
    ''' Class for developing and testing. Need to delete on production.'''
    def reply(self, request: Request):
        text = ('Тут будет следующий вопрос')
        # тестирование сохранения параметров пользователя между сессиями
        return self.make_response(
            text,
            buttons=[
                button('Да', hide=True),
                button('Нет', hide=True),
            ],
        )

    def handle_local_intents(self, request: Request):
        if intents.U_YES in request.intents:
            return UnderConstraction()
        elif intents.U_NOT in request.intents:
            return NextQ()
        elif intents.REPEAT_ME in request.intents:
            return self.__class__()



class StartTour(TestTourScene):
    def reply(self, request: Request):
        text = 'Отлично! Давайте поговорим о профессиях? О какой бы Вы хотели?'
        return self.make_response(
            text,
            state={
                'screen': 'start_tour'
            },
            buttons=[
                button('Аналитик'),
                button('Тестировщик'),
            ]
        )

    def handle_local_intents(self, request: Request):
        if intents.START_TOUR_WITH_PROF_SHORT:
            return move_to_prof_scene(request, intents.START_TOUR_WITH_PROF_SHORT)


class Analyst(TestTourScene):
    def reply(self, request: Request):
        return self.make_response(
            text='В будущем здесь появится рассказ об Аналитике. О ком еще рассказать?',
            state={
                'screen': 'start_tour'
            },
            buttons=[
                button('Аналитик'),
                button('Тестировщик'),
            ]
        )

    def handle_local_intents(self, request: Request):
        if intents.START_TOUR_WITH_PROF_SHORT:
            return move_to_prof_scene(request, intents.START_TOUR_WITH_PROF_SHORT)


class Tester(TestTourScene):
    def reply(self, request: Request):
        return self.make_response(
            text='В будущем здесь появится рассказ об Тестеровщике. О ком еще рассказать?',
            state={
                'screen': 'start_tour'
            },
            buttons=[
                button('Аналитик'),
                button('Тестировщик'),
            ]
        )

    def handle_local_intents(self, request: Request):
        if intents.START_TOUR_WITH_PROF_SHORT:
            return move_to_prof_scene(request, intents.START_TOUR_WITH_PROF_SHORT)


class UnknownProf(TestTourScene):
    def reply(self, request: Request):
        return self.make_response(
            text='Я такой профессии не знаю. О ком еще рассказать?',
            state={
                'screen': 'start_tour'
            },
            buttons=[
                button('Аналитик'),
                button('Тестировщик'),
            ]
        )

    def handle_local_intents(self, request: Request):
        if intents.START_TOUR_WITH_PROF_SHORT:
            return move_to_prof_scene(request, intents.START_TOUR_WITH_PROF_SHORT)


def _list_scenes():
    current_module = sys.modules[__name__]
    scenes = []
    for name, obj in inspect.getmembers(current_module):
        if inspect.isclass(obj) and issubclass(obj, Scene):
            scenes.append(obj)
    return scenes


SCENES = {
    scene.id(): scene for scene in _list_scenes()
}

DEFAULT_SCENE = WelcomeTest