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
import json
from random import random

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
    core_categories = classify_core_categories(core_urls)

    print('Categories:')
    print(json.dumps(core_categories))
    print()

    process_all(core_categories)

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
            elif current_core_category not in core_categories[url]:
                print(f'Already processed {url} as {core_categories[url][0]}. Tried to be processed again as {current_core_category}.')

    return core_categories

def process_all(core_categories):
    delme = subprocess.run(['mktemp', '-d'], shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout.decode().strip()

    finish_queue = queue.Queue()
    job_count = 0
    
    for url in core_categories:
        for category in core_categories[url]:
            thread = Thread(target=thread_worker, args=(url, category, delme, finish_queue))
            thread.start()
            job_count += 1
            job_count = wait_jobs(finish_queue, job_count, 30)

    wait_jobs(finish_queue, job_count, 0)

def process_url(core, category, delme):
    print(f'{core} {category}')
    url = f'{core}.git'
    target = '.'

    if category in early_install:
        return early_install[category](url, target) or core

    name = path_tail('https://github.com/MiSTer-devel', core)
    name, branch = get_branch(name)

    path = f'{delme}/{name}'

    if category[0] == '_':
        path = path + category
    
    if len(branch) > 0:
        path = path + branch

    download_repository(path, url, branch)

    installer = None
    if category in late_install:
        installer = late_install[category]
    elif category.startswith('user-content-folders-'):
        installer = install_folders
    else:
        installer = install_other_core

    installer(path, target, category, url)

def install_arcade_core(path, target, category, url):
    files = {}
    list_repository_files(files, path)
    for folder in files:
        for f in files[folder]:
            path_tail(path, f)

def install_console_core(path, target, category, url):
    pass

def install_computer_core(path, target, category, url):
    pass

def install_other_core(path, target, category, url):
    pass

def install_main_binary(path, target, category, url):
    pass

def install_zip_release(path, target, category, url):
    pass

def install_linux_binary(path, target, category, url):
    pass

def install_fonts(path, target, category, url):
    pass

def install_mra_alternatives(path, target, category, url):
    pass

def install_mra_alternatives_under_releases(path, target, category, url):
    pass

def install_folders(path, target, category, url):
    pass

def install_atari800(path, target, category, url):
    pass


late_install = {
    "_Arcade": install_arcade_core,
    "_Computer": install_computer_core,
    "_Console": install_console_core,
    "main": install_main_binary,
    "user-content-zip-release": install_zip_release,
    "user-content-linux-binary": install_linux_binary,
    "user-content-fonts": install_fonts,
    "user-content-mra-alternatives": install_mra_alternatives,
    "user-content-mra-alternatives-under-releases": install_mra_alternatives_under_releases,
}

def install_script(url, target):
    pass

def install_empty_folder(url, target):
    pass

def install_gamecontrollerdb(url, target):
    pass

def install_cheats(url, target):
    pass

early_install = {
    'user-content-scripts': install_script,
    'user-content-empty-folder': install_empty_folder,
    'user-cheats': install_cheats,
    'user-content-gamecontrollerdb': install_gamecontrollerdb,
}

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

class Error:
    def __init__(self, e):
        self.e = e

def thread_worker(core, category, delme, finish_queue):
    error = None
    try:
        job(core, category, delme)
    except BaseException as e:
        error = Error(e)
    except:
        error = Error(SystemError("Unknown"))

    finish_queue.put(error, False)

def job(core, category, delme):
    error = None
    for i in range(10):
        try:
            process_url(core, category, delme)
        except Exception as e:
            print(f'WARNING! {core}:{category} failed {i}')
            error = e
            time.sleep(0.5 + random() * 5)
    raise error

def wait_jobs(finish_queue, job_count, limit):
    while job_count > limit:
        while not finish_queue.empty():
            error = finish_queue.get(False)
            finish_queue.task_done()
            job_count -= 1
            if error is not None:
                raise error.e

    return job_count

def download_repository(path, url, branch):
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)

    url = url.replace(f'/tree/{branch}', '')

    run('git init -q', path)
    run('git remote add origin ' + url, path)
    run('git -c protocol.version=2 fetch --depth=1 -q --no-tags --prune --no-recurse-submodules origin ' + branch, path)
    run('git checkout -qf FETCH_HEAD', path)

def run(command, path):
    result = subprocess.run(shlex.split(command), cwd=path, shell=False, stderr=subprocess.DEVNULL)
    if result.returncode == -2:
        raise KeyboardInterrupt()
    elif result.returncode != 0:
        print(f'returncode {result.returncode} from: {command}')
        raise Exception(f'returncode {result.returncode} from: {command}')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        exit(1)
