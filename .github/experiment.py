#!/usr/bin/env python3

from github import Github, UnknownObjectException
from git import Repo
from threading import Thread
import os
import time
import queue
import tempfile
import shutil
import subprocess
import shlex

g = Github(os.environ['GITHUB_TOKEN'], pool_size=100)

def main():

    start = time.time()

    result_queue = queue.Queue()
    job_queue = queue.Queue()

    processes = []
    
    repo_count = 0
    for repo in g.get_user('MiSTer-devel').get_repos():
        repo_path = 'asdf/dist_repo_%s' % repo.name
        lower_name = repo.name.lower()
        if lower_name in ('distribution_mister', 'downloader_mister') or not lower_name.endswith('mister') or 'linux' in lower_name or 'sd-install' in lower_name:
            continue

        branch=''
        repo_url = repo.ssh_url.replace('git@github.com:', 'https://github.com/')
        print(repo_path)
        processes.append(subprocess.Popen(f'\
    rm -rf {repo_path} || true ;\
    mkdir -p {repo_path} ;\
    pushd {repo_path} > /dev/null 2>&1 ;\
    git init -q ;\
    git remote add origin {repo_url} ;\
    git -c protocol.version=2 fetch --depth=1 -q --no-tags --prune --no-recurse-submodules origin {branch} ;\
    git checkout -qf FETCH_HEAD ;\
    popd > /dev/null 2>&1 ;\
        ', shell=True, stderr=subprocess.STDOUT))

    count = 0
    while count < len(processes):
        for p in processes:
            result = p.poll()
            if result is not None:
                count += 1
                print(result)

    print("Time:")
    end = time.time()
    print(end - start)
    print()

def thread_worker(i, job_queue, result_queue):
    print('Thread %s started!' % i)
    try:
        while not job_queue.empty():
            repo_path, repo_https_url = job_queue.get(False)
            for result in list_repository_files(repo_path, repo_https_url):
                result_queue.put(result, False)
            job_queue.task_done()
    except Exception as e:
        result_queue.put(error(e))
        return

    result_queue.put(None, False)

def error(e):
    return {'error': e}

def is_error(e):
    return isinstance(e, dict) and e.get('error') is not None

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
