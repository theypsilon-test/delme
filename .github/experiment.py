#!/usr/bin/env python3

from github import Github
import os
import time
import subprocess
from dataclasses import dataclass
from typing import List
from subprocess import Popen
from pathlib import Path

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

    repos = []
    
    delme = subprocess.run(['mktemp', '-d'], shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout.decode().strip()
    
    for grepo in Github(os.environ['GITHUB_TOKEN']).get_user('MiSTer-devel').get_repos():
        lower_name = grepo.name.lower()
        if lower_name in ('distribution_mister', 'downloader_mister') or not lower_name.endswith('mister') or 'linux' in lower_name or 'sd-install' in lower_name:
            continue

        repos.append(Repo(
            name=grepo.name,
            path=f'{delme}/{grepo.name}',
            url=grepo.ssh_url.replace('git@github.com:', 'https://github.com/'),
            branch=''
        ))

    for repo in repos:
        print(repo.name)
        print(repo.path)

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

    for repo in repos:
        repo.files = {}
        list_repository_files(repo.files, repo.path)

    for repo in repos:
        print(repo.name)
        for folder in repo.files:
            print(f'{folder}:')
            for f in repo.files[folder]:
                try:
                    print(f.split(folder)[1][1:])
                except:
                    print(f'error on: {f}')

    print()
    print("Time:")
    end = time.time()
    print(end - start)
    print()

def process_repos(all_repos: List[Repo]):
    repos = [repo for repo in all_repos if repo.result != 0]
    for repo in repos:
        print(repo.name, flush=True)
        repo.process = Popen(['bash', '.github/download_repository.sh', repo.path, repo.url, repo.branch], shell=False, stderr=subprocess.STDOUT)

    count = 0
    while count < len(repos):
        for repo in repos:
            if repo.process is None:
                continue

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

        files[content_folder.lower()] = list(list_files(folder))

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
