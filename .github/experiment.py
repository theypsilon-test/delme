#!/usr/bin/env python3

from github import Github, UnknownObjectException
from threading import Thread
import os
import time
import queue
import tempfile
import shutil
import subprocess
import shlex
from dataclasses import dataclass
from typing import Any, List
from subprocess import Popen, run
from pathlib import Path

@dataclass
class Repo:
    name: str
    url: str
    path: str
    branch: str
    result: int = None
    process: Popen = None
    files = {}

def main():

    start = time.time()

    repos = []
    
    repo_count = 0
    for repo in Github(os.environ['GITHUB_TOKEN']).get_user('MiSTer-devel').get_repos():
        repo_path = 'asdf/dist_repo_%s' % repo.name
        lower_name = repo.name.lower()
        if lower_name in ('distribution_mister', 'downloader_mister') or not lower_name.endswith('mister') or 'linux' in lower_name or 'sd-install' in lower_name:
            continue

        branch = ''
        repo_url = repo.ssh_url.replace('git@github.com:', 'https://github.com/')

        repos.append(Repo(name=repo.name, path=repo_path, url=repo_url, branch=branch))

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
        list_repository_files(repo.files, repo_path)

    for repo in repos:
        print(repo.name)
        print(repo.files)

    print()
    print("Time:")
    end = time.time()
    print(end - start)
    print()

def process_repos(all_repos: List[Repo]):
    repos = [repo for repo in all_repos if repo.result != 0]
    for repo in repos:
        print(repo.name)
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
                print('%s: %s' % (result, repo.url))

def repos_downloaded(repos: List[Repo]):
    for repo in repos:
        if repo.result != 0:
            print('Repo %s didnt download!!!' % repo.name)
            return False

    return True

def list_repository_files(files, path):

    contents = []
    for content_folder in ['releases', 'palette', 'palettes', 'docs']:
        folder = '%s/%s' % (path, content_folder)
        if not Path(folder).exists():
            continue
        contents.append([folder, content_folder])

    while contents:
        file_content, content_folder = contents.pop(0)
        print(file_content)
        if Path(file_content).is_dir():
            contents = [*contents, *[[content, content_folder] for content in os.walk(file_content)]]
        else:
            files[content_folder] = files.get(content_folder, [])
            files[content_folder].append(file_content)

if __name__ == '__main__':
    main()
