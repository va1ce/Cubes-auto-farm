import os
from data import config
from pyrogram import Client
from loguru import logger


class Accounts:
    def __init__(self):
        self.workdir = config.WORKDIR

    def pars_sessions(self):
        sessions = []
        for file in os.listdir(self.workdir):
            if file.endswith(".session"):
                sessions.append(file.replace(".session", ""))

        logger.info(f"Найдено сессий: {len(sessions)}!")
        return sessions

    async def check_valid_sessions(self, sessions: list):
        logger.info(f"Проверяю сессии на валидность!")

        valid_sessions = []
        for session in sessions:
            try:
                client = Client(name=session, workdir=self.workdir)

                if await client.connect():
                    valid_sessions.append(session)

                await client.disconnect()
            except: pass

        logger.success(f"Валидных сессий: {len(valid_sessions)}; Невалидных: {len(sessions)-len(valid_sessions)}")
        return valid_sessions

    async def get_accounts(self):
        sessions = self.pars_sessions()
        accounts = await self.check_valid_sessions(sessions)

        if not accounts:
            raise ValueError("Нет валидных сессий")
        else:
            return accounts
