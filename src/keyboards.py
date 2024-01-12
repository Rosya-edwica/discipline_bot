from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
import tools
import textwrap

def get_main_keyboard() -> ReplyKeyboardMarkup:
    menu = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    modules_btn = KeyboardButton(text="Модули курса")
    continue_education_btn = KeyboardButton(text="Продолжить обучение")
    my_progress_btn = KeyboardButton(text="Мой прогресс")

    menu.add(modules_btn, continue_education_btn, my_progress_btn)
    return menu


def get_module_list() -> InlineKeyboardMarkup:
    modules = tools.get_modules()
    menu = InlineKeyboardMarkup(row_width=1)
    for i, mod in enumerate(modules):
        btn = InlineKeyboardButton(text=textwrap.fill(mod.Title), callback_data=f"module_{i}")
        menu.insert(btn)
    return menu


def get_module_videos(module: tools.Module) -> InlineKeyboardMarkup:
    menu = InlineKeyboardMarkup(row_width=1)
    for i, video in enumerate(module.Videos):
        btn = InlineKeyboardButton(text=textwrap.fill(video.Title), callback_data=f"video_{i}")
        menu.insert(btn)
    back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_module_list")
    menu.insert(back)
    return menu


def get_next_video() -> InlineKeyboardMarkup:
    menu = InlineKeyboardMarkup(row_width=2)
    btn = InlineKeyboardButton(text="Следующий урок 📋", callback_data="next_video")
    btn_materials = InlineKeyboardButton(text="Список исследований", callback_data="materials")
    # btn_text = InlineKeyboardButton(text="Конспект", callback_data="kons")
    menu.insert(btn)
    menu.insert(btn_materials)
    # menu.insert(btn_text)
    return menu

def reload_progress() -> InlineKeyboardMarkup:
    menu = InlineKeyboardMarkup(row_width=1)
    btn = InlineKeyboardButton(text="Обнулить прогресс", callback_data="reload_progress")
    menu.insert(btn)
    return menu