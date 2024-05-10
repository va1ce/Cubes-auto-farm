from json import loads
from utils.telegram import Accounts
import asyncio
from os import listdir
from os import mkdir
from os.path import exists
from os.path import isdir
from sys import stderr

from loguru import logger

from utils.cubes import Start
from database import on_startup_database
from database import actions as db_actions
from core import create_sessions

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    await on_startup_database()

    match user_action:
        case 1:
            await create_sessions()

            logger.success('Сессии успешно добавлены')

        case 2:
            accounts = await Accounts().get_accounts()

            tasks = []
            for thread, account in enumerate(accounts):
                session_proxy: str = await db_actions.get_session_proxy_by_name(session_name=account)

                tasks.append(asyncio.create_task(
                    Start(session_name=account, thread=thread, session_proxy=session_proxy).main()))

            await asyncio.gather(*tasks)

        case _:
            logger.error('Действие выбрано некорректно')


if __name__ == '__main__':
    print('AnusSoft: https://t.me/cryptolamik')
    if not exists(path='sessions'):
        mkdir(path='sessions')

    session_files: list[str] = [current_file[:-8] if current_file.endswith('.session')
                                else current_file for current_file in listdir(path='sessions')
                                if current_file.endswith('.session') or isdir(s=f'sessions/{current_file}')]

    logger.info(f'Обнаружено {len(session_files)} сессий')

    user_action: int = int(input('\n1. Создать сессию'
                                 '\n2. Запустить бота с существующих сессий'
                                 '\nВыберите ваше действие: '))
    print()
    asyncio.get_event_loop().run_until_complete(main())
