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

class Repo:
    name: str
    url: str
    path: str
    branch: str
    result: int = None
    process: Popen[bytes] = None


g = Github(os.environ['GITHUB_TOKEN'], pool_size=100)

def main():

    start = time.time()

    repos = []
    
    repo_count = 0
    for repo in g.get_user('MiSTer-devel').get_repos():
        repo_path = 'asdf/dist_repo_%s' % repo.name
        lower_name = repo.name.lower()
        if lower_name in ('distribution_mister', 'downloader_mister') or not lower_name.endswith('mister') or 'linux' in lower_name or 'sd-install' in lower_name:
            continue

        branch = ''
        repo_url = repo.ssh_url.replace('git@github.com:', 'https://github.com/')

        repos.append(Repo(name=repo.name, path=repo_path, url=repo_url, branch=branch))

    for _ in enumerate(5):
        process_repos(repos)
        if repos_downloaded(repos):
            break
    
    if not repos_downloaded(repos):
        raise Exception('Some repos didnt download.')

    print("Time:")
    end = time.time()
    print(end - start)
    print()

def process_repos(all_repos: List[Repo]):
    repos = {repo for repo in all_repos if repo.result != 0}
    for repo in repos:
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

def repos_downloaded(repos: List[Repo]):
    for repo in repos:
        if repo.result != 0:
            print('Repo %s didnt download' % repo.name)
            return False
    
    return True

def list_repository_files(repo_path, repo_https_url):
    shutil.rmtree(repo_path, ignore_errors=True)
    error = None
    for retry in range(5):
        try:
            repo = Repo.clone_from(repo_https_url, repo_path, depth=1)
            error = None
            break
        except Exception as e:
            print('Retry! %s' % retry)
            error = e
            time.sleep(1)

    if error is not None:
        raise error

    return [(repo_https_url, repo_https_url, repo_https_url)]

    files = []
    contents = []
    for content_folder in ['releases', 'Palette', 'Palettes', 'palette', 'palettes']:
        try:
            contents = [*contents, *[[content, content_folder.lower()] for content in repo.get_contents(content_folder)]]
        except UnknownObjectException:
            pass

    while contents:
        file_content, content_folder = contents.pop(0)
        if file_content.type == "dir":
            contents = [*contents, *[[content, content_folder] for content in repo.get_contents(file_content.path)]]
        else:
            files.append([content_folder, file_contentgo.path, file_content.download_url])
    return files

if __name__ == '__main__':
    main()
