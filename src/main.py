from aiogram import Bot, executor, Dispatcher, types

import keyboards as kb
import tools


config = tools.load_config("config.yml")
bot = Bot(config.Token)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start"])
async def start_command(msg: types.Message):
    await msg.answer(text=config.StartMessage, reply_markup=kb.get_main_keyboard())

@dp.message_handler(text="Модули курса")
async def module_list(msg: types.Message):
    """Просим показать список модулей"""
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    await bot.send_message(chat_id=msg.chat.id, text="Модули:", reply_markup=kb.get_module_list())

@dp.callback_query_handler(text="back_to_module_list")
async def back_to_module_list(call: types.CallbackQuery):
    """Просим показать список модулей"""
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await bot.send_message(chat_id=call.message.chat.id, text="Модули:", reply_markup=kb.get_module_list())

@dp.callback_query_handler(text_contains="module")
async def select_module(call: types.CallbackQuery):
    """Попадаем сюда после того, как выбрали модуль из списка модулей курса"""
    modules = tools.get_modules()
    selected_module_index = int(call.data.replace("module_", ""))
    module = modules[selected_module_index]

    tools.update_user_history(user_id=call.from_user.id, key="selected_module_id", value=selected_module_index)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await bot.send_message(chat_id=call.message.chat.id, text="Содержимое модуля:", reply_markup=kb.get_module_videos(module))


@dp.callback_query_handler(text_contains="video_")
async def select_video(call: types.CallbackQuery):
    """Попадаем сюда после того, как выбрали видео из списка видосов конкретного модуля"""
    current_video_id = int(call.data.replace("video_", ""))
    selected_module_id = tools.get_selected_user_module_id(call.from_user.id)
    await send_lesson(current_video_id, selected_module_id, call.message.chat.id, call.message.message_id, call.from_user.id)    

@dp.callback_query_handler(text="next_video")
async def get_next_video(call: types.CallbackQuery):
    """
    Инлайн-кнопка, которая находится под каждым видео. Предназначена для того, чтобы перейти к следующему в очереди видео
    """
    # Получаем данные для того, чтобы выбрать актуальное видео
    modules = tools.get_modules()
    current_module_id = tools.get_current_user_module_id(call.from_user.id)
    current_video_id = tools.get_current_user_video_id(call.from_user.id)
    tools.add_video_to_progress(str(call.from_user.id), str(current_module_id), str(current_video_id))
    current_video_id += 1 # Увеличиваем счетчик видео на один, тк нам нужно получить новое видео

    # Проверяем есть ли еще видео в модуле
    if len(modules[current_module_id].Videos) <= current_video_id:
        # Переходим на новый модуль
        current_module_id += 1
        current_video_id = 0
    
        # Проверяем остались ли модули
        if len(modules) <= current_module_id:
            await check_course_is_over(call.from_user.id, call.message.chat.id)
            return
        else:
            await bot.send_message(chat_id=call.message.chat.id, text=f"Открылся новый модуль: {modules[current_module_id].Title}\nПродолжай в том же духе!\n\n")


    await send_lesson(current_video_id, current_module_id, call.message.chat.id, call.message.message_id, call.from_user.id)    

@dp.message_handler(text="Продолжить обучение")
async def continue_learning(msg: types.Message):
    """Показываем текущее видео, здесь не надо увеличивать счетчик и не надо обновлять инфу в кэше"""
    current_module_id = tools.get_current_user_module_id(msg.from_user.id)
    current_video_id = tools.get_current_user_video_id(msg.from_user.id)    
    await send_lesson(current_video_id, current_module_id, msg.chat.id, msg.message_id, msg.from_user.id)    

@dp.message_handler(text="Мой прогресс")
async def my_progress(msg: types.Message):
    text = tools.show_my_progress(str(msg.from_user.id))
    if text:
        await bot.send_message(chat_id=msg.chat.id, text=text, reply_markup=kb.reload_progress())
    else:
        
        await bot.send_message(chat_id=msg.chat.id, text=config.ZeroProgressMessage)

@dp.callback_query_handler(text="reload_progress")
async def reload_progress(call: types.CallbackQuery):
    tools.remove_progress(str(call.from_user.id))
    
    current_module_id = 0
    current_video_id = 0
    await send_lesson(current_video_id, current_module_id, call.message.chat.id, call.message.message_id, call.message.from_user.id)    

    tools.update_user_history(user_id=str(call.from_user.id), key="current_module_id", value=current_module_id)
    tools.update_user_history(user_id=str(call.from_user.id), key="current_video_id", value=current_video_id)

async def send_lesson(current_video_id: int, current_module_id: int, chat_id: int, message_id: int, user_id: int):
    modules = tools.get_modules()
    video = modules[current_module_id].Videos[current_video_id]
    answer_text = "\n".join((
        f"📕Модуль {current_module_id+1}: «{modules[current_module_id].Title}»",
        f"📓Урок: {current_video_id+1}/{len(modules[current_module_id].Videos)} - {video.Title}",
        f"🔗Ссылка на видео: {video.Path}"
    ))

    await bot.delete_message(chat_id=chat_id, message_id=message_id)
    await bot.send_message(chat_id=chat_id, text=answer_text, reply_markup=kb.get_next_video()) 

    # Обновляем информацию о прогрессе в кэше
    tools.update_user_history(user_id=user_id, key="current_module_id", value=current_module_id)
    tools.update_user_history(user_id=user_id, key="current_video_id", value=current_video_id)


# Пока заморозили, тк нужно добавить к каждому видосу конспекты вручную
@dp.callback_query_handler(text="konspect")
async def get_video_text(call: types.CallbackQuery):
    d = open("dofamine.pdf", "rb")
    await bot.send_document(chat_id=call.message.chat.id, document=d) 
    d.close()


@dp.callback_query_handler(text="materials")
async def get_materials(call: types.CallbackQuery):
    current_video = tools.get_current_video(str(call.from_user.id))
    if current_video.Materials:
        materials = "\n".join(f"{i}. <a href='{item.Url}'>{item.Title}</a>" 
                        for i, item in enumerate(current_video.Materials, start=1))
        await bot.send_message(chat_id=call.message.chat.id, text=materials, parse_mode=types.ParseMode.HTML)
    else:
        await bot.send_message(chat_id=call.message.chat.id, text="Исследований по данному уроку нет")


async def check_course_is_over(user_id: int, chat_id: int):
    if tools.course_is_done(str(user_id)):
        await bot.send_message(chat_id=chat_id, text=config.FinishMessage)
        img = open("data/план-итог.jpg", mode="rb")
        await bot.send_photo(chat_id=chat_id , photo=img)
        img.close()
    else:
        await bot.send_message(chat_id=chat_id, text=config.CourseNotCompletedMessage)
        

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)