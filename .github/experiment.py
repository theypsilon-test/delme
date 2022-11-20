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

@dataclass
class Repo:
    name: str
    url: str
    path: str
    branch: str
    result: int = None
    process: Popen = None
    files = None

def main():

    start = time.time()

    cores = []
    cores.extend(['https://github.com/MiSTer-devel/Main_MiSTer', 'https://github.com/MiSTer-devel/Menu_MiSTer'])
    cores.extend(['user-content-mra-alternatives', 'https://github.com/MiSTer-devel/MRA-Alternatives_MiSTer'])
    cores.extend(most_cores())
    cores.extend(['user-content-arcade-cores', *arcade_cores()])
    cores.extend(["user-content-fonts", "https://github.com/MiSTer-devel/Fonts_MiSTer"])
    cores.extend(["user-content-folders-Filters|Filters_Audio|Gamma", "https://github.com/MiSTer-devel/Filters_MiSTer"])
    cores.extend(["user-content-folders-Shadow_Masks", "https://github.com/MiSTer-devel/ShadowMasks_MiSTer"])
    cores.extend(["user-content-folders-Presets", "https://github.com/MiSTer-devel/Presets_MiSTer"])
    cores.extend(["user-content-scripts"])
    cores.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/ini_settings.sh"])
    cores.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/samba_on.sh"])
    cores.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/other_authors/fast_USB_polling_on.sh"])
    cores.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/other_authors/fast_USB_polling_off.sh"])
    cores.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/other_authors/wifi.sh"])
    cores.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/rtc.sh"])
    cores.extend(["https://raw.githubusercontent.com/MiSTer-devel/Scripts_MiSTer/master/timezone.sh"])
    cores.extend(["user-content-linux-binary", "https://github.com/MiSTer-devel/PDFViewer_MiSTer"])
    cores.extend(["user-content-empty-folder", "games/TGFX16-CD"])
    cores.extend(["user-content-gamecontrollerdb", "https://raw.githubusercontent.com/MiSTer-devel/Gamecontrollerdb_MiSTer/main/gamecontrollerdb.txt"])
    cores.extend(["user-cheats", "https://gamehacking.org/mister/"])

    delme = subprocess.run(['mktemp', '-d'], shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout.decode().strip()
    category = 'main'

    finish_queue = queue.Queue()
    job_count = 0
    
    threads = []
    repos = []
    cache = set()
    for core in cores:
        if core.startswith('user-') or 'tree' in core:
            category = categorize(core)
            continue

        if core in cache:
            continue
        cache.add(core)

        thread = Thread(target=thread_worker, args=(core, category, delme, finish_queue))
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

def thread_worker(core, category, delme, finish_queue):
    msg = ''
    try:
        msg = job(core, category, delme)
    except Exception as e:
        msg = Exception(f'Exception {type(e).__name__}({e}): {core} {category}')
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

def categorize(url):
    if url == "user-content-computers---classic": return "_Computer"
    elif url == "user-content-computers---classic": return "_Computer"
    elif url == "user-content-arcade-cores": return "_Arcade"
    elif url == "user-content-consoles---classic": return "_Console"
    elif url == "user-content-other-systems": return "_Other"
    elif url == "user-content-service-cores": return "_Utility"
    elif url == "user-content-linux-binary": return url
    elif url == "user-content-zip-release": return url
    elif url == "user-content-scripts": return url
    elif url == "user-cheats": return url
    elif url == "user-content-empty-folder": return url
    elif url == "user-content-gamecontrollerdb": return url
    elif url.startswith("user-content-folders-"): return url
    elif url == "user-content-mra-alternatives": return url
    elif url == "user-content-mra-alternatives-under-releases": return url
    elif url == "user-content-fonts": return url
    else: return ""

def process_url(core, category, delme):
    if not core.startswith('https://github.com/MiSTer-devel/'):
        return core

    name = path_tail('https://github.com/MiSTer-devel', core)
    url = f'{core}.git'
    path = f'{delme}/{name}'
    branch = ''

    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)

    run(['git', 'init', '-q'], cwd=path)
    run(['git', 'remote', 'add', 'origin', url], cwd=path)
    run(['git', '-c', 'protocol.version=2', 'fetch', '--depth=1', '-q', '--no-tags', '--prune', '--no-recurse-submodules', 'origin', branch], cwd=path)
    run(['git', 'checkout', '-qF', 'FETCH_HEAD'], cwd=path)
    
    files = {}
    list_repository_files(files, path)
    for folder in files:
        for f in files[folder]:
            path_tail(path, f)

    return url

def run(command, path):
    result = subprocess.run(command, cwd=path, shell=False, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        raise Exception(f'returncode {result.returncode}')

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
