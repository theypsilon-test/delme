#!/usr/bin/env python3

from github import Github, UnknownObjectException
from git import Repo
from threading import Thread
import os
import time
import queue
import tempfile

g = Github(os.environ['GITHUB_TOKEN'], pool_size=100)

def main():

    start = time.time()

    result_queue = queue.Queue()
    job_queue = queue.Queue()

    
    repo_count = 0
    for repo in g.get_user('MiSTer-devel').get_repos():
        repo_path = '%s/%s' % (tempfile.gettempdir(), repo.name)
        print(repo_path)
        job_queue.put([repo_path, repo.git_url], False)
        repo_count += 1

    threads = [Thread(target=thread_worker, args=(job_queue, result_queue)) for _ in range(30)]
    for thread in threads:
        thread.start()

    ongoing_count = 0

    while ongoing_count < repo_count:
        while not result_queue.empty():
            result = result_queue.get(False)
            result_queue.task_done()

            if is_error(result):
                raise result['error']

            if result is None:
                ongoing_count += 1
                continue
            
            folder, path, url = result
            print(url)

    result_queue.join()

    for thread in threads:
        thread.join()


    print("Time:")
    end = time.time()
    print(end - start)
    print()

def thread_worker(job_queue, result_queue):
    try:
        while not job_queue.empty():
            repo_path, repo_git_url = job_queue.get(False)
            for folder, path, url in list_repository_files(repo_path, repo_git_url):
                result_queue.put([folder, path, url], False)
            job_queue.task_done()
    except Exception as e:
        result_queue.put(error(e))
        return

    result_queue.put(None, False)

def error(e):
    return {'error': e}

def is_error(e):
    return isinstance(e, dict) and e.get('error') is not None

def list_repository_files(repo_path, repo_git_url):
    repo = git.Repo.clone_from(repo_git_url, repo_path)
    return []

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
            files.append([content_folder, file_content.path, file_content.download_url])
    return files

if __name__ == '__main__':
    main()
