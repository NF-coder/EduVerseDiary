from api.settings import TELEGRAM_TOKEN, LAST_NAMES
from api.school33api import School33Api
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.markdown import hbold, hunderline
import aioschedule
import asyncio
import copy
import datetime
from aiogram.utils.exceptions import ChatNotFound

bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)
api = School33Api()
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.answer(f'Привет, {message.from_user.first_name}. Ты уже прочитал описание и знаешь, чем я могу тебе помочь.\n' 
    + 'Если вдруг ты не прочитал описание, то я твой электронный дневник, но только в телеграмме и более крутой. \n\n ' +
    "📍 " + hbold(' Что я могу?') + '\n'
    + '🚩 Присылать твои оценки в данном триместре по запросу (но актуальные, в отличие от официального дневника)' + '\n' +
    '🚩 Присылать тебе новые оценки в тот момент, когда ты их получаешь.\n' + 
    '🚩 Отправлять тебе расписание звонков на текущий день.\n' + 
    'С помощью меня ты сможешь понять, что у тебя получается лучше,  а что хуже.\n\n'
    '🆘\nСправка: /help', parse_mode='HTML'
    )

@dp.message_handler(commands=['help'])
async def help_user(message: types.Message):
    await message.answer("""Вот команды, которые доступны нашему боту.
    /get_marks - узнать о твоих текущих оценках в этом триместре
    /get_schedule - узнать расписание звонков на текущий день""")

@dp.message_handler(commands=['get_marks'])
async def send_marks(message: types.Message):
    last_name = LAST_NAMES[str(message.from_id)]
    for st in api.students:
        if st.name.split(' ')[1] == last_name:
            await message.answer('Твои оценки:')
            for subject in st.subjects:
                if subject.marks != []:
                    await message.answer(f'{subject.name} {subject.average_mark} {subject.marks}')

@dp.message_handler(commands=['get_schedule'])
async def send_schedule(message: types.Message):
    await message.answer("""Расписание звонков сегодня:""")
    if datetime.date.isoweekday == 1 or datetime.date.isoweekday == 6:
        await message.answer("1. 8.00-8.40\n2. 8.45-9.25\n3. 9.35-10.15\n4. 10.30-11.10\n5. 11.25-12.05\n6. 12.20-13.00\n7. 13.10-13.50")
    else:
        await message.answer("1. 8.30-9.15\n2. 9.25-10.10\n3. 10.25-11.10\n4. 11.25-12.10\n5. 12.25-13.10\n6. 13.20-14.05\n7. 14.15-14.55")

async def send_if_new_marks():
    students = copy.deepcopy(api.students)
    api.update_marks()
    for i in range(len(api.students)):
        if students[i].subjects != api.students[i].subjects:
            last_name = students[i].name.split(' ')[1]
            id = list(LAST_NAMES.keys())[list(LAST_NAMES.values()).index(last_name)]
            for j in range(len(students[i].subjects), len(api.students[i].subjects)):
                if api.students[i].subjects[j].marks != []:
                    try:
                        await bot.send_message(id, f"У тебя новые оценки по предмету {api.students[i].subjects[j].name}: {api.students[i].subjects[j].marks}")
                    except ChatNotFound:
                        print(f"Can't send to {id} {last_name}")
                        break
        for j in range(len(students[i].subjects)):
            if students[i].subjects[j].marks != api.students[i].subjects[j].marks:
                last_name = students[i].name.split(' ')[1]
                id = list(LAST_NAMES.keys())[list(LAST_NAMES.values()).index(last_name)]
                try:
                    await bot.send_message(id, f"У тебя новые оценки по предмету {api.students[i].subjects[j].name}: {api.students[i].subjects[j].marks[len(students[i].subjects[j].marks):len(api.students[i].subjects[j].marks)]}")
                except ChatNotFound:
                    print(f"Can't send to {id} {last_name}")
                    break

async def scheduler():
    aioschedule.every(10).minutes.do(send_if_new_marks)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
