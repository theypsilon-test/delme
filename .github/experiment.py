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
    cores.extend(most_cores())
    cores.extend(arcade_cores())
    
    delme = subprocess.run(['mktemp', '-d'], shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout.decode().strip()
    category = ''

    finish_queue = queue.Queue()
    job_count = 0
    
    threads = []
    repos = []
    for core in cores:
        if core.startswith('user-content-') or 'tree' in core:
            continue

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
        msg = Exception(f'Exception {type(e).__name__}: {core}')
    finish_queue.put(msg, False)

def job(core, category, delme):
    error = None
    for _ in range(5):
        try:
            return process(core, category, delme)
        except Exception as e:
            error = e
            time.sleep(0.5)
    raise error

def process(core, category, delme):
    name = path_tail('https://github.com/MiSTer-devel', core)
    url = f'{core}.git'
    path = f'{delme}/{name}'
    branch = ''

    result = subprocess.run(['bash', '.github/download_repository.sh', path, url, branch], shell=False, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise Exception(f'returncode {result.returncode}')
    
    files = {}
    list_repository_files(files, path)
    for folder in files:
        for f in files[folder]:
            path_tail(path, f)

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
