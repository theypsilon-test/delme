#!/usr/bin/env python3

import os
import time
import subprocess
from dataclasses import dataclass
from typing import List
from subprocess import Popen
from pathlib import Path
import requests
import re
from threading import Thread
import queue
import shutil
import shlex

@dataclass
class Repo:
    name: str
    url: str
    path: str
    branch: str
    result: int = None
    process: Popen = None
    files = None


def is_standard_core(category):
    return category in ["_Computer", "_Arcade", "_Console", "_Other", "_Utility"]

def main():

    start = time.time()

    core_urls = fetch_core_urls()

    print()
    print('CORE URLs:')
    for url in core_urls:
        print(url)
    print()

    core_categories = classify_core_categories(core_urls)

    delme = subprocess.run(['mktemp', '-d'], shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout.decode().strip()
    category = 'main'

    finish_queue = queue.Queue()
    job_count = 0
    
    threads = []

    for url in core_urls:
        for category in core_categories[url]:
            print(f'url: {url} category: {category}')
            thread = Thread(target=thread_worker, args=(url, category, delme, finish_queue))
            thread.start()
            threads.append(thread)
            job_count += 1
            job_count = wait_jobs(finish_queue, job_count, 30)

    wait_jobs(finish_queue, job_count, 0)

    print()
    print("Time:")
    end = time.time()
    print(end - start)
    print()

def fetch_core_urls():
    core_urls = []
    core_urls.extend(['https://github.com/MiSTer-devel/Main_MiSTer', 'https://github.com/MiSTer-devel/Menu_MiSTer'])
    core_urls.extend(['user-content-mra-alternatives', 'https://github.com/MiSTer-devel/MRA-Alternatives_MiSTer'])
    core_urls.extend(most_cores())
    core_urls.extend(['user-content-arcade-cores', *arcade_cores()])
    core_urls.extend(["user-content-fonts", "https://github.com/MiSTer-devel/Fonts_MiSTer"])
    core_urls.extend(["user-content-folders-Filters|Filters_Audio|Gamma", "https://github.com/MiSTer-devel/Filters_MiSTer"])
    core_urls.extend(["user-content-folders-Shadow_Masks", "https://github.com/MiSTer-devel/ShadowMasks_MiSTer"])
    core_urls.extend(["user-content-folders-Presets", "https://github.com/MiSTer-devel/Presets_MiSTer"])
    core_urls.extend(["user-content-scripts"])
    core_urls.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/ini_settings.sh"])
    core_urls.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/samba_on.sh"])
    core_urls.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/other_authors/fast_USB_polling_on.sh"])
    core_urls.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/other_authors/fast_USB_polling_off.sh"])
    core_urls.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/other_authors/wifi.sh"])
    core_urls.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/rtc.sh"])
    core_urls.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/timezone.sh"])
    core_urls.extend(["user-content-linux-binary", "https://github.com/MiSTer-devel/PDFViewer_MiSTer"])
    core_urls.extend(["user-content-empty-folder", "games/TGFX16-CD"])
    core_urls.extend(["user-content-gamecontrollerdb", "https://raw.githubusercontent.com/MiSTer-devel/Gamecontrollerdb_MiSTer/main/gamecontrollerdb.txt"])
    core_urls.extend(["user-cheats", "https://gamehacking.org/mister/"])
    return core_urls

def classify_core_categories(core_urls):
    current_core_category = 'main'
    core_categories = {}
    for url in core_urls:
        if url == "user-content-computers---classic": current_core_category = "_Computer"
        elif url == "user-content-arcade-cores": current_core_category = "_Arcade"
        elif url == "user-content-consoles---classic": current_core_category = "_Console"
        elif url == "user-content-other-systems": current_core_category = "_Other"
        elif url == "user-content-service-cores": current_core_category = "_Utility"
        elif url == "user-content-linux-binary": current_core_category = url
        elif url == "user-content-zip-release": current_core_category = url
        elif url == "user-content-scripts": current_core_category = url
        elif url == "user-cheats": current_core_category = url
        elif url == "user-content-empty-folder": current_core_category = url
        elif url == "user-content-gamecontrollerdb": current_core_category = url
        elif url.startswith("user-content-folders-"): current_core_category = url
        elif url == "user-content-mra-alternatives": current_core_category = url
        elif url == "user-content-mra-alternatives-under-releases": current_core_category = url
        elif url == "user-content-fonts": current_core_category = url
        elif url in ["user-content-fpga-cores", "user-content-development", ""]: pass
        else:
            if url not in core_categories:
                core_categories[url] = [current_core_category]
            elif is_standard_core(core_categories[url][0]) and is_standard_core(current_core_category):
                core_categories[url].append(current_core_category)
                #print(f'lets break here {core_categories[url]}:{current_core_category}')
                #raise ValueError(f'lets break here {core_categories[url]}:{current_core_category}')
            elif current_core_category not in core_categories[url]:
                print(f'Already processed {url} as {core_categories[url][0]}. Tried to be processed again as {current_core_category}.')

    return core_categories

def thread_worker(core, category, delme, finish_queue):
    msg = ''
    try:
        msg = job(core, category, delme)
    except Exception as e:
        msg = Exception(f'{type(e).__name__}({e}): {core} {category}')
    finish_queue.put(msg, False)

def job(core, category, delme):
    error = None
    for _ in range(5):
        try:
            return process_url(core, category, delme)
        except Exception as e:
            error = e
            time.sleep(0.5)
    raise error


early_install = {
    'user-content-scripts': lambda _1, _2: None,
    'user-content-empty-folder': lambda _1, _2: None,
    'user-cheats': lambda _1, _2: None,
    'user-content-gamecontrollerdb': lambda _1, _2: None,
}

late_install = {
    "_Arcade": lambda _1, _2, _3, _4: None,
    "_Computer": lambda _1, _2, _3, _4: None,
    "_Console": lambda _1, _2, _3, _4: None,
    "main": lambda _1, _2, _3, _4: None,
    "user-content-zip-release": lambda _1, _2, _3, _4: None,
    "user-content-linux-binary": lambda _1, _2, _3, _4: None,
    "user-content-fonts": lambda _1, _2, _3, _4: None,
    "user-content-mra-alternatives": lambda _1, _2, _3, _4: None,
    "user-content-mra-alternatives-under-releases": lambda _1, _2, _3, _4: None,
}

repo_regex = re.compile(r'^([a-zA-Z]+://)?github.com(:[0-9]+)?/([a-zA-Z0-9_-]*)/([a-zA-Z0-9_-]*)(/tree/([a-zA-Z0-9_-]+))?$')

def process_url(core, category, delme):
    url = f'{core}.git'
    target = '.'

    if category in early_install:
        return early_install[cateogory](url, target) or core

    name = path_tail('https://github.com/MiSTer-devel', core)
    name, branch = get_branch(name)
    print(f'name: {name} branch: {branch}')
    path = f'{delme}/{name}'

    download_repository(path, url, branch)

    installer = None
    if category in late_install:
        installer = late_install[category]
    elif category.startswith('user-content-folders-'):
        installer = lambda _1, _2, _3, _4: None
    else:
        installer = lambda _1, _2, _3, _4: None

    installer(path, target, category, url)

    files = {}
    list_repository_files(files, path)
    for folder in files:
        for f in files[folder]:
            path_tail(path, f)

    return url

def download_repository(path, url, branch):
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
    run('git init -q', path)
    run('git remote add origin ' + url, path)
    run('git -c protocol.version=2 fetch --depth=1 -q --no-tags --prune --no-recurse-submodules origin ' + branch, path)
    run('git checkout -qf FETCH_HEAD', path)

def run(command, path):
    result = subprocess.run(shlex.split(command), cwd=path, shell=False, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        raise Exception(f'returncode {result.returncode} from: {command}')

def wait_jobs(finish_queue, job_count, limit):
    while job_count > limit:
        while not finish_queue.empty():
            message = finish_queue.get(False)
            finish_queue.task_done()
            job_count -= 1
            print(message, flush=True)
            if isinstance(message, Exception):
                raise message

    return job_count

def most_cores():
    text = fetch_text('https://raw.githubusercontent.com/wiki/MiSTer-devel/Wiki_MiSTer/_Sidebar.md')
    regex = re.compile(r'https://github.com/MiSTer-devel/[a-zA-Z0-9._-]*[_-]MiSTer(/tree/[a-zA-Z0-9-]+)?', re.I)
    reading = False
    cores = []
    for line in text.splitlines():
        match = regex.search(line)
        line = line.strip().lower()
        if 'fpga cores' in line or 'service cores' in line:
            reading = True
        if reading is False:
            continue
        if line.startswith('###'):
            if 'development' in line[4:] or 'arcade cores' in line[4:]:
                reading = False
            else:
                cores.append('user-content-%s' % line[4:].replace(' ', '-'))
        elif match is not None:
            core = match.group(0)
            if 'menu_mister' not in core.lower():
                cores.append(core)
    return cores

def arcade_cores():
    text = fetch_text('https://raw.githubusercontent.com/wiki/MiSTer-devel/Wiki_MiSTer/Arcade-Cores-List.md')
    cores = []
    regex = re.compile(r'https://github.com/MiSTer-devel/[a-zA-Z0-9._-]*[_-]MiSTer[^\/]', re.I)
    for line in text.splitlines():
        match = regex.search(line)
        if match is not None:
            cores.append(match.group(0)[0:-1])
    return cores

def fetch_text(url):
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f'Request to {url} failed')
    
    return r.text
        
def path_tail(folder, f):
    pos = f.find(folder)
    return f[pos + len(folder) + 1:]

def get_branch(name):
    pos = name.find('/tree/')
    if pos == -1:
        return name, ""
    return name[0:pos], name[pos + len('/tree/'):]

def list_repository_files(files, path):
    for content_folder in ['releases', 'Palette', 'Palettes', 'palettes']:
        folder = '%s/%s' % (path, content_folder)
        if not Path(folder).exists():
            continue

        files[content_folder] = list(list_files(folder))

def list_files(directory):
    for f in os.scandir(directory):
        if f.is_dir():
            yield from list_files(f.path)
        elif f.is_file():
            yield f.path

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        exit(1)
