import json
from typing import NamedTuple
import os
import yaml


VIDEOS_PATH = "../data/videos.json"
USERS_PATH = "../data/users.json"

class Material(NamedTuple):
    Title: str
    Url: str

class Video(NamedTuple):
    Title: str
    Path: str
    Materials: list[Material]

class Module(NamedTuple):
    Title: str
    Videos: list[Video]

class Config(NamedTuple):
    Token: str
    StartMessage: str
    FinishMessage: str
    ZeroProgressMessage: str
    CourseNotCompletedMessage: str


def get_modules() -> list[Module]:
    with open(VIDEOS_PATH, "r") as file:
        data = json.load(file)
    
    modules: list[Module] = []
    for mod in data["modules"]:
        videos: list[Video] = []
        for vid in mod["videos"]:
            materials = []
            if "materials" in vid.keys():
                for mt in vid["materials"]:
                    materials.append(Material(
                        Title=mt["title"],
                        Url=mt["url"]
                    ))

            video = Video(
                Title=vid["title"],
                Path=vid["path"],
                Materials=materials
            )
            videos.append(video)
        
        modules.append(Module(
            Title=mod["title"],
            Videos=videos
        ))
    return modules

def update_user_history(user_id: int, key: str, value: str):
    user_id = str(user_id)
    data = load_users()
    if not "users" in data.keys():
        data["users"] = {}
        
    if user_id in data["users"]:
        data["users"][user_id][key] = value
    else:
        data["users"][user_id] = {key:value}

    save_users(data)


def get_selected_user_module_id(user_id: int) -> int | None:
    """selected_module_id = это номер модуля, который открыл пользователь"""
    return get_user_progress_by_key(user_id, key="selected_module_id")

def get_current_user_module_id(user_id: int) -> int | None:
    """
    current_module_id = это номер модуля, В КОТОРОМ ПОЛЬЗОВАТЕЛЬ ВЫБРАЛ видео
    разница между current_module_id и selected_module_id в том, что мы можем с помощью current_module_id вернуться к текущему видео по кнопке "Продолжить обучение"
    если не разделять эти переменные, то при просмотре содержимого модуля, мы будем менять current_module_id и из-за этого сломается история
    """
    return get_user_progress_by_key(user_id, key="current_module_id")

def get_current_user_video_id(user_id: int) -> int | None:
    return get_user_progress_by_key(user_id, key="current_video_id")
    

def get_user_progress_by_key(user_id: int, key: str) -> int:
    user_id = str(user_id)
    data = load_users()

    if not data or not user_id in data["users"].keys():
        return None
    else:
        return data["users"][user_id][key]


def add_video_to_progress(user_id: str, module_id: str, video_id: str):
    data = load_users()
    user = data["users"][user_id]

    if "progress" in user.keys():
        if module_id in user["progress"].keys():
            if video_id not in user["progress"][module_id]:
                user["progress"][module_id].append(video_id)
        else:
            user["progress"][module_id] = [video_id, ]  
    else:
        user["progress"] = {module_id : [video_id, ]}
    
    data["users"][user_id] = user
    save_users(data)


def show_my_progress(user_id: str) -> str | None:
    data = load_users()
    user = data["users"][user_id]

    if not "progress" in user.keys():
        return None
    
    modules = get_modules()
    text = ""
    for mod, pg_videos in user["progress"].items():
        module = modules[int(mod)]
        text += f"Модуль {int(mod)+1}:'{module.Title}'\n"
        
        for video_id, video in enumerate(module.Videos):
            if str(video_id) in pg_videos:
                text += f"{video_id+1}.✅ {video.Title}\n"
            else:
                text += f"{video_id+1}.⭕️ {video.Title}\n"
        text += "\n"

    return text


def remove_progress(user_id: str):
    data = load_users()
    if not "progress" in data["users"][user_id].keys():
        return

    del data["users"][user_id]["progress"]
    save_users(data)


def course_is_done(user_id: str) -> bool:
    data = load_users()
    if not "progress" in data["users"][user_id].keys():
        return False
    progress = data["users"][user_id]["progress"]
    lessons_count = len([0 for module in get_modules() for video in module.Videos])
    lessons_completed_count = len([i for _, value in progress.items() for i in value])
    if lessons_completed_count == lessons_count:
        return True
    else:
        print(lessons_completed_count, lessons_count)
        return False

def get_current_video(user_id: str) -> Video:
    data = load_users()
    modules = get_modules()

    video_id = data["users"][user_id]["current_video_id"]
    module_id = data["users"][user_id]["current_module_id"]
    return modules[module_id].Videos[video_id]

def load_users() -> dict:
    if os.path.isfile(USERS_PATH):
        with open(USERS_PATH, mode="r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    else:
        return {}

def save_users(data: dict) -> None:
    with open(USERS_PATH, mode="w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_config(path: str) -> Config:
    with open(path, mode="r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return Config(
        Token=data["token"],
        StartMessage=data["MESSAGES"]["START"],
        FinishMessage=data["MESSAGES"]["FINISH"],
        ZeroProgressMessage=data["MESSAGES"]["ZERO_PROGRESS"],
        CourseNotCompletedMessage=data["MESSAGES"]["COURSE_IS_NOT_COMPLETED"],
    )
