import os
import sys
import json
import shutil
import logging
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装 requests：pip install requests", flush=True)
    sys.exit(1)

BASE_DIR = Path(__file__).parent.resolve()
SETTINGS_FILE = BASE_DIR / "settings.json"
CATEGORIES_FILE = BASE_DIR / "categories.json"
LOG_FILE = BASE_DIR / "organize_desktop.log"

# 日志设置：同时输出到文件和控制台
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(file_handler)
logger.addHandler(console_handler)

DEFAULT_SETTINGS = {
    "api_base": "YOUR_API_BASE_HERE",
    "api_key": "YOUR_API_KEY_HERE",
    "api_model": "gpt-4o-mini",
    "max_ai_size": 1 * 1024 * 1024
}

DEFAULT_CATEGORIES = {
    "subjects": ["数学", "语文", "英语", "物理", "化学", "生物"],
    "custom_categories": [],
    "ext_map": {
        ".jpg": "图片", ".jpeg": "图片", ".png": "图片",
        ".gif": "图片", ".bmp": "图片",
        ".doc": "文档", ".docx": "文档", ".pdf": "文档", ".txt": "文档",
        ".mp4": "视频", ".avi": "视频",
        ".mp3": "音频", ".wav": "音频",
        ".zip": "压缩包", ".rar": "压缩包"
    },
    "default_folder": "其他"
}

def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return default.copy()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"无法解析 {path}，请检查 JSON。错误: {e}")
        sys.exit(1)

settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
cats_conf = load_json(CATEGORIES_FILE, DEFAULT_CATEGORIES)

API_BASE = settings["api_base"]
API_KEY = settings["api_key"]
API_MODEL = settings["api_model"]
MAX_AI_SIZE = settings["max_ai_size"]

SUBJECTS = cats_conf["subjects"]
CUSTOM_CATEGORIES = cats_conf["custom_categories"]
EXT_MAP = cats_conf["ext_map"]
DEFAULT_FOLDER = cats_conf["default_folder"]
KNOWN_FOLDERS = set(SUBJECTS) | set(CUSTOM_CATEGORIES) | set(EXT_MAP.values()) | {DEFAULT_FOLDER}

def ai_request(prompt: str, max_tokens: int = 100) -> str | None:
    url = f"{API_BASE}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    body = {
        "model": API_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"[AI] 请求失败：{e}")
        return None

def classify_with_ai(text: str, candidates: list[str], use_content: bool = False) -> str | None:
    if use_content:
        prompt = (
            f"请根据以下文件内容将其归类到一个分类，选项有：{candidates}。\n"
            "只输出分类名称，不要多余文字。\n"
            f"文件内容：{text}"
        )
    else:
        prompt = (
            f"请将下面的文件名归类到一个分类，选项有：{candidates}。\n"
            "只输出分类名称，不要多余文字。\n"
            f"文件名：{text}"
        )
    out = ai_request(prompt, max_tokens=50)
    if not out:
        return None
    for c in candidates:
        if c in out:
            logger.info(f"[AI] {'内容' if use_content else '名称'}分类 → {c}")
            return c
    return None

def remove_empty_folders(path: Path):
    for folder in path.iterdir():
        if folder.is_dir():
            remove_empty_folders(folder)
            if not any(folder.iterdir()):
                try:
                    folder.rmdir()
                    logger.info(f"删除空文件夹: {folder}")
                except OSError as e:
                    logger.error(f"删除空文件夹失败: {folder}, 错误: {e}")

def organize_desktop():
    desktop = Path.home() / "Desktop"
    moved = skipped = 0
    all_categories = SUBJECTS + CUSTOM_CATEGORIES

    for f in desktop.iterdir():
        if f.is_dir() and f.name in KNOWN_FOLDERS:
            continue
        if not f.is_file():
            continue

        name = f.name
        target = next((c for c in SUBJECTS if c in name), None)
        if not target:
            target = next((c for c in CUSTOM_CATEGORIES if c in name), None)

        if not target:
            size = f.stat().st_size
            if size <= MAX_AI_SIZE:
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    content = None
                target = classify_with_ai(content or name, SUBJECTS, use_content=bool(content))
                if not target:
                    target = classify_with_ai(content or name, all_categories, use_content=bool(content))
            else:
                target = classify_with_ai(name, SUBJECTS, use_content=False)
                if not target:
                    target = classify_with_ai(name, all_categories, use_content=False)

        if not target:
            target = EXT_MAP.get(f.suffix.lower(), DEFAULT_FOLDER)

        dest_dir = desktop / target
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / name
        if dest.exists():
            stem, suf, i = f.stem, f.suffix, 1
            while (dest_dir / f"{stem}_{i}{suf}").exists():
                i += 1
            dest = dest_dir / f"{stem}_{i}{suf}"

        try:
            shutil.move(str(f), str(dest))
            moved += 1
            logger.info(f"Moved: {name} → {target}/{dest.name}")
        except Exception as e:
            skipped += 1
            logger.error(f"Fail: {name} => {e}")

    print(f"\n整理完成！成功移动 {moved} 个文件，跳过 {skipped} 个文件。", flush=True)
    input("按回车继续...")

def delete_empty_folders_menu():
    desktop = Path.home() / "Desktop"
    remove_empty_folders(desktop)
    print("删除空文件夹完成！", flush=True)
    input("按回车继续...")

def create_custom_categories():
    desktop = Path.home() / "Desktop"
    all_cats = SUBJECTS + CUSTOM_CATEGORIES
    uncategorized = [f.name for f in desktop.iterdir() if f.is_file() and not any(c in f.name for c in all_cats)]
    if not uncategorized:
        print("没有未分类的文件。", flush=True)
        input("按回车继续...")
        return

    prompt = (
        "请将以下文件名列表按「类似学科」的方式分成若干分类。\n"
        "输出纯 JSON，格式：\n"
        "{\n"
        "  \"categories\": [\"分类A\",\"分类B\",…],\n"
        "  \"mapping\": { \"文件1.txt\":\"分类A\", … }\n"
        "}\n"
        f"文件列表：{uncategorized}"
    )
    out = ai_request(prompt, max_tokens=300)
    if not out:
        print("AI 请求失败！", flush=True)
        input("按回车继续...")
        return

    cleaned = out.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    m = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1)

    try:
        j = json.loads(cleaned)
        cats = j["categories"]
        mapping = j["mapping"]
    except Exception:
        print("解析 AI 返回失败，请检查原始返回。", flush=True)
        input("按回车继续...")
        return

    print("\nAI 建议的分类：", cats, flush=True)
    print("文件归属示例：", flush=True)
    for fn, ct in mapping.items():
        print(f"  {fn} → {ct}", flush=True)

    ans = input("\n是否将以上分类追加到 custom_categories？(y/n) ")
    if ans.lower().startswith("y"):
        for c in cats:
            if c not in CUSTOM_CATEGORIES and c not in SUBJECTS:
                CUSTOM_CATEGORIES.append(c)
                new_folder = desktop / c
                if not new_folder.exists():
                    new_folder.mkdir()
        cats_conf["custom_categories"] = CUSTOM_CATEGORIES
        CATEGORIES_FILE.write_text(
            json.dumps(cats_conf, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print("分类已更新！", flush=True)
    input("按回车继续...")

def main_menu():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("==== 桌面整理工具 ====", flush=True)
        print("1) 整理桌面", flush=True)
        print("2) 创建自定义分类", flush=True)
        print("3) 删除空文件夹", flush=True)
        print("0) 退出", flush=True)
        c = input("请选择: ").strip()
        if c == "1":
            organize_desktop()
        elif c == "2":
            create_custom_categories()
        elif c == "3":
            delete_empty_folders_menu()
        elif c == "0":
            break

if __name__ == "__main__":
    main_menu()
