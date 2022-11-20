#!/usr/bin/env python3

from github import Github
import os
import time
import subprocess
from dataclasses import dataclass
from typing import List
from subprocess import Popen
from pathlib import Path
import requests
import re

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
    mister_devel = Github(os.environ['GITHUB_TOKEN']).get_user('MiSTer-devel')
    
    repos = []
    processes = {}
    
    for core in cores:
        if core.startswith('user-content-') or 'tree' in core:
            continue
        core = path_tail('https://github.com/MiSTer-devel', core)
        print(core)

        grepo = mister_devel.get_repo(core)
        lower_name = grepo.name.lower()
        if lower_name in ('distribution_mister', 'downloader_mister') or not lower_name.endswith('mister') or 'linux' in lower_name or 'sd-install' in lower_name:
            continue

        repo = Repo(
            name=grepo.name,
            path=f'{delme}/{grepo.name}',
            url=grepo.ssh_url.replace('git@github.com:', 'https://github.com/'),
            branch=''
        )
        repo.process = Popen(['bash', '.github/download_repository.sh', repo.path, repo.url, repo.branch], shell=False, stderr=subprocess.STDOUT)
        repos.append(repo)
        processes[grepo.name] = repo
        
        while len(processes) > 100:
            for p in list(processes):
                repo = processes[p]
                result = repo.process.poll()
                if result is not None:
                    repo.result = result
                    repo.process = None
                    processes.pop(p)
                    print('%s: %s' % (result, repo.url), flush=True)
            
            time.sleep(1)

    wait_jobs(repos)

    for repo in repos:
        repo.files = {}
        list_repository_files(repo.files, repo.path)

    for repo in repos:
        print(repo.name)
        for folder in repo.files:
            print(f'{folder}:')
            for f in repo.files[folder]:
                print(path_tail(folder, f))

    print()
    print("Time:")
    end = time.time()
    print(end - start)
    print()

def wait_jobs(repos):
    for i in range(5):
        if i > 0:
            if repos_downloaded(repos):
                break
            print()
            print('Trying failed ones...')
            print()

        process_repos(repos)
    
    if not repos_downloaded(repos):
        raise Exception('Some repos didnt download!')

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
    
def process_repos(repos: List[Repo]):
    count = 0
    for repo in repos:
        if repo.process is not None:
            count += 1

    while count < len(repos):
        for repo in repos:
            result = repo.process.poll()
            if result is not None:
                count += 1
                repo.result = result
                repo.process = None
                print('%s: %s' % (result, repo.url), flush=True)

def repos_downloaded(repos: List[Repo]):
    for repo in repos:
        if repo.result != 0:
            print('Repo %s didnt download!!!' % repo.name, flush=True)
            return False

    return True

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
