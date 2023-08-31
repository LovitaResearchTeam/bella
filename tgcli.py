import asyncio
import urllib
import requests


class TelegramClient:
    _token: str
    _chatid: int
    def __init__(self, token: str, chatid: int) -> None:
        self._token = token
        self._chatid = chatid

    async def send_message(self, text: str):
        URL = 'https://api.telegram.org/bot{token}/'.format(token=self._token)
        tot = urllib.parse.quote_plus(text)
        url = URL + "sendMessage?text={}&chat_id={}".format(tot, self._chatid)
        loop = asyncio.get_event_loop()
        def get_response():
            return requests.get(url)
        r_fut = loop.run_in_executor(None, get_response)
        r = await r_fut
        if not r.status_code == requests.codes.OK:
            print(r.content)
        else:
            print("tg sent")