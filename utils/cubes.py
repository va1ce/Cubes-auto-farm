import random
from better_proxy import Proxy
from loguru import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView
import asyncio
from urllib.parse import unquote
from data import config
import aiohttp
from fake_useragent import UserAgent
from aiohttp_proxy import ProxyConnector


class Start:
    def __init__(self, thread: int, session_name: str, session_proxy: str | None = None):
        self.thread = thread
        self.session_name = session_name
        self.session_headers = {'User-Agent': UserAgent(os='android').random}
        self.session_proxy = session_proxy
        self.token = None
        if session_proxy:
            proxy = Proxy.from_str(session_proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None
        self.client = Client(name=session_name,
                             workdir=config.WORKDIR,
                             proxy=proxy_dict
                             )

    async def main(self):
        proxy_conn = ProxyConnector().from_url(
            self.session_proxy) if self.session_proxy else None
        async with aiohttp.ClientSession(headers=self.session_headers, connector=proxy_conn) as http_client:
            if self.session_proxy:
                await self.check_proxy(http_client=http_client, proxy=self.session_proxy)

            while True:
                try:
                    await asyncio.sleep(random.uniform(config.ACC_DELAY[0], config.ACC_DELAY[1]))

                    tg_web_data = await self.get_tg_web_data()
                    balance, energy = await self.login(tg_web_data, http_client=http_client)

                    while True:
                        if energy > 150:
                            balance, energy, boxes, block = await self.mining(http_client=http_client)

                            logger.success(
                                f"Поток {self.thread} | Сломал блок {block}! Баланс: {balance}; Энергия: {energy}; Боксы: {boxes}")
                            await asyncio.sleep(random.uniform(config.MINING_DELAY[0], config.MINING_DELAY[1]))

                        elif energy <= 150 and balance >= 50:
                            balance, energy, energy_buy = await self.buy_energy(balance, http_client=http_client)
                            logger.success(
                                f"Поток {self.thread} | Купил {energy_buy} энергии!")

                        else:
                            logger.warning(
                                f"Поток {self.thread} | Кол-во энергии меньше 150, поток спит!")
                            await asyncio.sleep(random.uniform(config.MINING_DELAY[0], config.MINING_DELAY[1]))
                            balance, energy = await self.login(tg_web_data, http_client=http_client)

                except Exception as e:
                    logger.error(f"Поток {self.thread} | Ошибка: {e}")

    async def get_tg_web_data(self):
        await self.client.connect()

        await self.client.send_message(chat_id="cubesonthewater_bot", text="/start NDg4MDA4NTM4==")
        await asyncio.sleep(random.uniform(config.MINING_DELAY[0], config.MINING_DELAY[1]))

        web_view = await self.client.invoke(RequestWebView(
            peer=await self.client.resolve_peer('cubesonthewater_bot'),
            bot=await self.client.resolve_peer('cubesonthewater_bot'),
            platform='android',
            from_bot_menu=False,
            url='https://www.thecubes.xyz'
        ))
        auth_url = web_view.url
        await self.client.disconnect()
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))

    async def login(self, tg_web_data, http_client: aiohttp.ClientSession):
        json_data = {"initData": tg_web_data}
        resp = await http_client.post("https://server.questioncube.xyz/auth", json=json_data)

        resp_json = await resp.json()
        self.token = resp_json.get("token")

        return int(resp_json.get("drops_amount")), int(resp_json.get("energy"))

    async def mining(self, http_client: aiohttp.ClientSession):
        while True:
            resp = await http_client.post("https://server.questioncube.xyz/game/mined", json={"token": self.token})
            try:
                resp_json = await resp.json()
                return int(resp_json.get("drops_amount")), int(resp_json.get("energy")), int(resp_json.get("boxes_amount")), int(resp_json.get("mined_count"))

            except:
                await asyncio.sleep(random.uniform(config.MINING_DELAY[0]+5, config.MINING_DELAY[1]+5))

    async def buy_energy(self, balance: int, http_client: aiohttp.ClientSession):
        if balance >= 250:
            proposal_id = 3
            energy_buy = 500
        elif 250 > balance >= 125:
            proposal_id = 2
            energy_buy = 250
        elif 125 > balance >= 50:
            proposal_id = 1
            energy_buy = 100

        json_data = {"proposal_id": proposal_id, "token": self.token}

        resp = await http_client.post("https://server.questioncube.xyz/game/rest-proposal/buy", json=json_data)
        resp_json = await resp.json()
        return int(resp_json.get("drops_amount")), int(resp_json.get("energy")), energy_buy

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as e:
            logger.error(f"Ошибка при проверке прокси: {e}")
