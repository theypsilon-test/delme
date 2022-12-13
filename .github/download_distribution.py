#!/usr/bin/env python3

import os
import time
import subprocess
from pathlib import Path
import requests
import re
from threading import Thread
import queue
import shutil
import shlex
import json
import zipfile
from random import random
import xml.etree.ElementTree as ET
import sys
import traceback

def main():

    start = time.time()

    new_core_urls = new_cores()
    core_urls = fetch_core_urls()
    core_categories = classify_core_categories(core_urls)

    print('New Core URLs:')
    print(json.dumps(new_core_urls))
    print()

    print('Core URLs:')
    print(json.dumps(core_urls))
    print()

    print('Categories:')
    print(json.dumps(core_categories))
    print()

    target = 'delme'
    if len(sys.argv) > 1:
        target = sys.argv[1].strip()

    if 'delme' in target.lower():
        shutil.rmtree(target, ignore_errors=True)
        touch_folder(target)

    process_all(core_categories, new_core_urls, target)

    print()
    print("Time:")
    end = time.time()
    print(end - start)
    print()

# content description

def fetch_core_urls():
    core_urls = []
    core_urls.extend(['https://github.com/MiSTer-devel/Main_MiSTer', 'https://github.com/MiSTer-devel/Menu_MiSTer'])
    core_urls.extend(['user-content-mra-alternatives', 'https://github.com/MiSTer-devel/MRA-Alternatives_MiSTer'])
    core_urls.extend(most_cores())
    core_urls.extend(['user-content-arcade-cores', *arcade_cores()])
    core_urls.extend(["user-cheats"])  # @TODO Modify this mapping whenever there is a new system with cheats
    core_urls.extend(["fds|NES"])
    core_urls.extend(["gb|GameBoy"])
    core_urls.extend(["gba|GBA"])
    core_urls.extend(["gbc|GameBoy"])
    core_urls.extend(["gen|Genesis"])
    core_urls.extend(["gg|SMS"])
    core_urls.extend(["lnx|AtariLynx"])
    core_urls.extend(["nes|NES"])
    core_urls.extend(["pce|TGFX16"])
    core_urls.extend(["pcd|TGFX16-CD"])
    core_urls.extend(["psx|PSX"])
    core_urls.extend(["scd|MegaCD"])
    core_urls.extend(["sms|SMS"])
    core_urls.extend(["snes|SNES"])
    #core_urls.extend(["user-backup-cheats", "https://github.com/MiSTer-devel/Distribution_MiSTer/archive/refs/heads/main.zip"])  # Uncomment if user-cheats breaks (and comment user-cheats instead)
    core_urls.extend(["user-content-fonts", "https://github.com/MiSTer-devel/Fonts_MiSTer"])
    core_urls.extend(["user-content-folders"])
    core_urls.extend(["https://github.com/MiSTer-devel/Filters_MiSTer"])
    core_urls.extend(["https://github.com/MiSTer-devel/ShadowMasks_MiSTer"])
    core_urls.extend(["https://github.com/MiSTer-devel/Presets_MiSTer"])
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

    return core_urls

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

def new_cores():
    text = fetch_text('https://raw.githubusercontent.com/wiki/MiSTer-devel/Wiki_MiSTer/Cores.md')
    link_regex = re.compile(r'\[(.*)\]\((.*)\)')

    reading_cores_list = False
    reading_arcade_cores_list = False
    result = []

    category = None

    for line in text.splitlines():
        line = line.strip()
        lower = line.lower()

        if not reading_cores_list and not reading_arcade_cores_list:
            if '<!-- cores_list_start -->' in lower:
                reading_cores_list = True
            elif '<!-- arcade_cores_list_start -->' in lower:
                reading_arcade_cores_list = True
        elif reading_cores_list:
            if '<!-- cores_list_end -->' in lower:
                reading_cores_list = False
                continue

            if line.startswith('##'):
                header = line.replace('#', '').strip().lower()

                if 'computers' in header:
                    category = '_Computer'
                elif 'consoles' in header:
                    category = '_Console'
                elif 'service' in header or 'utility' in header:
                    category = '_Utility'
                elif 'other' in header:
                    category = '_Other'
                
                continue

            if 'https://github.com/mister-devel/' not in lower:
                continue

            columns = line.split('|')
            matches = link_regex.search(columns[1])
            if not matches:
                continue

            name = matches.group(1).strip()
            url = matches.group(2).strip()
            home = columns[2].strip()
            result.append({'name': name, 'url': url, 'home': home, 'category': category})

        elif reading_arcade_cores_list:
            if '<!-- arcade_cores_list_end -->' in line:
                reading_arcade_cores_list = False
                continue

            if 'https://github.com/mister-devel/' not in lower:
                continue

            columns = line.split('|')
            matches = link_regex.search(columns[1])
            if not matches:
                continue

            name = matches.group(1).strip()
            url = matches.group(2).strip()
            result.append({'name': name, 'url': url, 'category': '_Arcade'})

    return sorted(result, key=lambda element: element['category'].lower() + element['url'].lower())

def arcade_cores():
    text = fetch_text('https://raw.githubusercontent.com/wiki/MiSTer-devel/Wiki_MiSTer/Arcade-Cores-List.md')
    cores = []
    regex = re.compile(r'https://github.com/MiSTer-devel/[a-zA-Z0-9._-]*[_-]MiSTer[^\/]', re.I)
    for line in text.splitlines():
        match = regex.search(line)
        if match is not None:
            cores.append(match.group(0)[0:-1])
    return cores

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
        elif url == "user-backup-cheats": current_core_category = url
        elif url == "user-content-empty-folder": current_core_category = url
        elif url == "user-content-gamecontrollerdb": current_core_category = url
        elif url == "user-content-folders": current_core_category = url
        elif url == "user-content-mra-alternatives": current_core_category = url
        elif url == "user-content-fonts": current_core_category = url
        elif url in ["user-content-fpga-cores", "user-content-development", ""]: print('WARNING! Ignored url: ' + url)
        else:
            if url not in core_categories:
                core_categories[url] = [current_core_category]
            elif is_standard_core(core_categories[url][0]) and is_standard_core(current_core_category):
                core_categories[url].append(current_core_category)
            elif current_core_category not in core_categories[url]:
                print(f'Already processed {url} as {core_categories[url][0]}. Tried to be processed again as {current_core_category}.')

    return core_categories

def is_standard_core(category):
    return category.strip() in ["_Computer", "_Arcade", "_Console", "_Other", "_Utility"]

# processors

def process_all(core_categories, new_core_urls, target):
    delme = subprocess.run(['mktemp', '-d'], shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout.decode().strip()

    finish_queue = queue.Queue()
    job_count = 0

    def process(fn, ctx):
        nonlocal job_count
        thread = Thread(target=thread_worker, args=(fn, ctx, finish_queue))
        thread.start()
        job_count += 1
        job_count = wait_jobs(finish_queue, job_count, 30)

    cache = set()

    print('--- CORES ---')
    print()

    for core in new_core_urls:
        cache.add(core['url'])
        process(lambda: process_core(core, delme, target), core['url'])

    print()
    print('--- EXTRA CONTENT ---')
    print()

    for url in core_categories:
        if url in cache:
            continue

        for category in core_categories[url]:
            process(lambda: process_url(url, category, delme, target), url)

    wait_jobs(finish_queue, job_count, 0)

def process_core(core, delme, target):
    category = core['category']
    url = f'{core["url"]}.git'

    name = path_tail('https://github.com/MiSTer-devel/', core['url'])
    name, branch = get_branch(name)

    path = f'{delme}/{name}'

    if category[0] == '_':
        path = path + category
    
    if len(branch) > 0:
        path = path + branch

    download_repository(path, url, branch)

    if core['url'].lower() == 'https://github.com/mister-devel/atari800_mister':
        return install_atari800(path, target, core)
    
    if category in core_install:
        return core_install[category](path, target, core)

    raise SystemError('Ignored core: ' + core)

def process_url(core, category, delme, target):

    if category in early_install:
        return early_install[category](core, target)

    name = path_tail('https://github.com/MiSTer-devel/', core)
    name, branch = get_branch(name)

    path = f'{delme}/{name}'

    if category[0] == '_':
        path = path + category
    
    if len(branch) > 0:
        path = path + branch

    url = f'{core}.git'
    download_repository(path, url, branch)

    if category in late_install:
        return late_install[category](path, target, category, url)

    if category in core_install:
        print(f'WARNING! Ignored core: {core}')
        return

    raise SystemError(f'Ignored core: {core} {category}')

# installers

def install_arcade_core(path, target_dir, core):
    touch_folder(f'{target_dir}/games/hbmame')
    touch_folder(f'{target_dir}/games/mame')

    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {core["category"]}: {core["url"]}')
        return

    binary_names = uniq_files_with_stripped_date(releases_dir)
    if 'MRA-Alternatives' in binary_names:
        print('Warning! Ignored MRA-Alternatives in arcade: ' + core["url"])
        return

    for bin in binary_names:
        if not is_arcade_core(bin):
            continue  # @TODO this is a change where I ignore arcade_installed

        latest_release = get_latest_release(releases_dir, bin)
        if not is_rbf(latest_release):
            print(f'{core["url"]}: {latest_release} is NOT a RBF file')
            continue

        print('BINARY: ' + bin)
        copy_file(f'{releases_dir}/{latest_release}', f'{target_dir}/_Arcade/cores/{path_tail("Arcade-", latest_release)}')

    for mra in mra_files(releases_dir):
        copy_file(f'{releases_dir}/{mra}', f'{target_dir}/_Arcade/{mra}')

def install_console_core(path, target_dir, core):
    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {core["category"]}: {core["url"]}')
        return

    for bin in uniq_files_with_stripped_date(releases_dir):
        if is_arcade_core(bin):
            continue

        latest_release = get_latest_release(releases_dir, bin)
        if not is_rbf(latest_release):
            print(f'{core["url"]}: {latest_release} is NOT a RBF file')
            continue

        print('BINARY: ' + bin)
        copy_file(f'{releases_dir}/{latest_release}', f'{target_dir}/_Console/{latest_release}')

    for folder in [core['home'], *mgl_folders(releases_dir)]:
        for readme in list_readmes(target_dir):
            copy_file(f"{path}/{readme}", f"{path}/docs/{folder}/{readme}")

        for file in files_with_no_date(releases_dir):
            if is_mra(file):
                continue

            copy_file_according_to_extension(f"{releases_dir}/{file}", target_dir, folder, file, "_Console")

        touch_folder(f'{target_dir}/games/{folder}')

        source_palette_folder = find_palette_folder(path)
        if source_palette_folder is None:
            continue

        target_palette_folder = f'{target_dir}/games/{folder}/Palettes/'
        copy_folder(f'{path}/{source_palette_folder}', target_palette_folder)
        clean_palettes(target_palette_folder)

def install_computer_core(path, target_dir, core):
    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {core["category"]}: {core["url"]}')
        return

    for bin in uniq_files_with_stripped_date(releases_dir):
        if is_arcade_core(bin):
            continue

        latest_release = get_latest_release(releases_dir, bin)
        if not is_rbf(latest_release):
            print(f'{core["url"]}: {latest_release} is NOT a RBF file')
            continue

        print('BINARY: ' + bin)
        copy_file(f'{releases_dir}/{latest_release}', f'{target_dir}/_Computer/{latest_release}')

    for folder in [core['home'], *mgl_folders(releases_dir)]:

        if folder == 'Minimig':
            folder = 'Amiga'
        elif folder == 'SHARP MZ SERIES':
            folder = 'SharpMZ'

        for readme in list_readmes(target_dir):
            copy_file(f"{path}/{readme}", f"{path}/docs/{folder}/{readme}")

        for file in files_with_no_date(releases_dir):
            if is_mra(file):
                continue

            copy_file_according_to_extension(f"{releases_dir}/{file}", target_dir, folder, file, "_Console")

        touch_folder(f'{target_dir}/games/{folder}')

def install_atari800(path, target_dir, core):
    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {core["category"]}: {core["url"]}')
        return

    category = core['category']

    name: str
    if category == '_Computer':
        name = 'Atari800'
    elif category == '_Console':
        name = 'Atari5200'
    else:
        raise SystemError(f"Could not install Atari 800 core. (CATEGORY={category})")

    for bin in [f for f in uniq_files_with_stripped_date(releases_dir) if name in f]:
        if is_arcade_core(bin):
            continue

        latest_release = get_latest_release(releases_dir, bin)
        if not is_rbf(latest_release):
            print(f'{core["url"]}: {latest_release} is NOT a RBF file')
            continue

        print('BINARY: ' + bin)
        copy_file(f'{releases_dir}/{latest_release}', f'{target_dir}/{category}/{latest_release}')

    for folder in ['Atari800', 'Atari5200']:
        if category == '_Computer':
            for file in files_with_no_date(releases_dir):
                copy_file_according_to_extension(f"{releases_dir}/{file}", target_dir, folder, file, category)

        for readme in list_readmes(path):
            copy_file(f'{path}/{readme}', f'{target_dir}/docs/{folder}/{readme}')

        touch_folder(f'{target_dir}/games/{folder}')

def install_other_core(path, target_dir, core):
    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {core["category"]}: {core["url"]}')
        return


    for bin in uniq_files_with_stripped_date(releases_dir):
        if is_arcade_core(bin):
            continue

        latest_release = get_latest_release(releases_dir, bin)
        if not is_rbf(latest_release):
            print(f'{core["url"]}: {latest_release} is NOT a RBF file')
            continue

        print('BINARY: ' + bin)
        copy_file(f'{releases_dir}/{latest_release}', f'{target_dir}/{core["category"]}/{latest_release}')

    for folder in [core['home'], *mgl_folders(releases_dir)]:

        for readme in list_readmes(target_dir):
            copy_file(f"{path}/{readme}", f"{path}/docs/{folder}/{readme}")

        for file in files_with_no_date(releases_dir):
            if is_mra(file):
                continue

            copy_file_according_to_extension(f"{releases_dir}/{file}", target_dir, folder, file, core["category"])

        touch_folder(f'{target_dir}/games/{folder}')

def install_main_binary(path, target_dir, category, url):
    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {category}: {url}')
        return

    for bin in uniq_files_with_stripped_date(releases_dir):
        latest_release = get_latest_release(releases_dir, bin)
        if is_empty_release(latest_release):
            continue

        print('BINARY: ' + bin)
        copy_file(f'{releases_dir}/{latest_release}', f'{target_dir}/{remove_date(latest_release)}')

def install_linux_binary(path, target_dir, category, url):
    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {category}: {url}')
        return

    for bin in uniq_files_with_stripped_date(releases_dir):
        latest_release = get_latest_release(releases_dir, bin)
        if is_empty_release(latest_release):
            continue

        print('BINARY: ' + bin)
        copy_file(f'{releases_dir}/{latest_release}', f'{target_dir}/linux/{remove_date(latest_release)}')

def install_zip_release(path, target_dir, category, url):
    releases_dir = f'{path}/releases'

    if not Path(releases_dir).exists():
        print(f'Warning! Ignored {category}: {url}')
        return
    
    for zip in uniq_files_with_stripped_date(releases_dir):
        latest_release = get_latest_release(releases_dir, zip)
        if is_empty_release(latest_release):
            continue

        unzip(f'{releases_dir}/{latest_release}', target_dir)

def install_mra_alternatives(path, target_dir, category, url):
    print(f'Installing MRA Alternatives {url}')

    touch_folder(f'{target_dir}/_Arcade')
    copy_folder(f'{path}/_alternatives', f'{target_dir}/_Arcade/_alternatives')

def install_fonts(path, target_dir, category, url):
    print(f'Installing Fonts {url}')
    
    touch_folder(f'{target_dir}/font')
    for font in list_fonts(path):
        copy_file(f'{path}/{font}', f'{target_dir}/font/')

def install_folders(path, target_dir, category, url):
    ignore_folders = ['releases', 'matlab', 'samples']
    for folder in list_folders(path):
        if folder.lower() in ignore_folders or folder[0] == '.':
            continue
        
        print(f"Installing Folder '{folder}' from {url}")
        copy_folder(f'{path}/{folder}', f'{target_dir}/{folder}')

late_install = {
    "main": install_main_binary,
    "user-content-zip-release": install_zip_release,
    "user-content-linux-binary": install_linux_binary,
    "user-content-folders": install_folders,
    "user-content-fonts": install_fonts,
    "user-content-mra-alternatives": install_mra_alternatives,
}

core_install = {
    "_Arcade": install_arcade_core,
    "_Computer": install_computer_core,
    "_Console": install_console_core,
    "_Utility": install_other_core,
    "_Other": install_other_core,
}

def install_script(url, target_dir):
    print('Script: ' + url)
    touch_folder(f'{target_dir}/Scripts')
    download_file(url, f'{target_dir}/Scripts/{Path(url).name}')

def install_empty_folder(url, target_dir):
    touch_folder(f'{target_dir}/{url}')

def install_gamecontrollerdb(url, target_dir):
    touch_folder(f'{target_dir}/linux/gamecontrollerdb')
    print(f"SDL Game Controller DB: {url}")
    download_file(url, f'{target_dir}/linux/gamecontrollerdb/{Path(url).name}')

def install_cheats(mapping, target_dir):
    page_url = "https://gamehacking.org/mister"

    parts = mapping.split('|')
    cheat_key = parts[0].strip()
    cheat_platform = parts[1].strip()

    touch_folder(f'{target_dir}/Cheats')
    cheat_zips = collect_cheat_zips(page_url)

    cheat_zip = next(cheat_zip for cheat_zip in cheat_zips if cheat_key in cheat_zip)
    cheat_url = f'{page_url}/{cheat_zip}'
    tmp_zip = f'/tmp/{cheat_key}{cheat_platform}.zip'
    cheat_folder = f'{target_dir}/Cheats/{cheat_platform}'

    if Path(cheat_folder).exists():
        shutil.rmtree(cheat_folder, ignore_errors=True)

    print(f'cheat_keys: {cheat_key}, cheat_platform: {cheat_platform}, cheat_zip: {cheat_zip}, cheat_url: {cheat_url}')

    touch_folder(cheat_folder)
    download_file(cheat_url, tmp_zip)
    unzip(tmp_zip, cheat_folder)

def install_cheats_backup(url, target_dir):
    tmp_zip = '/tmp/old_main.zip'
    download_file(url, tmp_zip)
    touch_folder(f'{target_dir}/Cheats')
    unzip(tmp_zip, f'{target_dir}/Cheats/')

early_install = {
    'user-content-scripts': install_script,
    'user-content-empty-folder': install_empty_folder,
    'user-cheats': install_cheats,
    'user-backup-cheats': install_cheats_backup,
    'user-content-gamecontrollerdb': install_gamecontrollerdb,
}

# mister files utils

def mra_files(folder):
    return [without_folder(folder, f) for f in list_files(folder, recursive=False) if Path(f).suffix.lower() == '.mra']

def is_arcade_core(path):
    return Path(path).name.lower().startswith('arcade-')

def is_rbf(path):
    return Path(path).suffix.lower() == '.rbf'

def get_latest_release(folder, bin):
    files = [without_folder(folder, f) for f in list_files(folder, recursive=False)]
    releases = sorted([f for f in files if bin in f and remove_date(f) != f])
    return releases[-1]

def uniq_files_with_stripped_date(folder):
    result = []
    for f in list_files(folder, recursive=False):
        f = without_folder(folder, str(Path(f).with_suffix('')))

        no_date = remove_date(f)
        if no_date == f or no_date in result:
            continue

        result.append(no_date)

    return result

def clean_palettes(palette_folder):
    for file in list_files(palette_folder, recursive=True):
        path = Path(file)
        if path.suffix.lower() in ['.pal', '.gbp']:
            continue

        path.unlink()

def find_palette_folder(path):
    for folder in list_folders(path):
        if folder.lower() in ['palette', 'palettes']:
            return folder
        
    return None

def copy_file_according_to_extension(path, target_dir, folder, file, category):
    if is_mgl(file):
        copy_file(path, f'{target_dir}/{category}/{file}')
    elif is_doc(file):
        copy_file(path, f'{target_dir}/docs/{folder}/{file}')
    else:
        copy_file(path, f'{target_dir}/games/{folder}/{file}')

def is_mgl(file):
    return Path(file).suffix.lower() == '.mgl'

def is_doc(file):
    return Path(file).suffix.lower() in ['.md', '.pdf', '.txt', '.rtf']

def is_mra(file):
    return Path(file).suffix.lower() == '.mra'

def files_with_no_date(folder):
    return [without_folder(folder, f) for f in list_files(folder, recursive=False) if f == remove_date(f)]

def list_readmes(folder):
    return [without_folder(folder, f) for f in list_files(folder, recursive=False) if f.lower().startswith('readme.')]

def mgl_folders(releases_dir):
    extracts = [extract_mgl_setname(f) for f in list_files(releases_dir, recursive=False) if Path(f).suffix.lower() == '.mgl']
    return [x for x in extracts if x is not None]

def extract_mgl_setname(mgl):
    try:
        for _, elem in ET.iterparse(mgl, events=('start',)):
            if elem.tag.lower() == 'setname' and elem.text is not None:
                return elem.text.strip()
    except ET.ParseError as e:
        return None

def remove_date(path):
    if len(path) < 10:
        return path

    last_part = Path(path).stem[-9:]
    if last_part[0] == '_' and last_part[1:].isnumeric():
        return path.replace(last_part, '')

    return path

def without_folder(folder, f):
    return f.replace(f'{folder}/', '').replace(folder, '').strip()

def is_empty_release(bin):
    return bin == '' or bin is None or len(bin) == 0

def list_fonts(path):
    return [Path(f).name for f in list_files(path, recursive=True) if Path(f).suffix.lower() == '.pf']

def collect_cheat_zips(url):
    r = requests.get(url, cookies={'challenge': 'BitMitigate.com'})
    if r.status_code != 200:
        raise Exception(f'Request to {url} failed')
    
    return [f[f.find('mister_'):f.find('.zip') + 4] for f in r.text.splitlines() if 'mister_' in f and '.zip' in f]

# file system utilities

def path_tail(folder, f):
    pos = f.find(folder)
    return f[pos + len(folder):]

def get_branch(name):
    pos = name.find('/tree/')
    if pos == -1:
        return name, ""
    return name[0:pos], name[pos + len('/tree/'):]

def list_files(directory, recursive):
    for f in os.scandir(directory):
        if f.is_dir() and recursive:
            yield from list_files(f.path, recursive)
        elif f.is_file():
            yield f.path

def list_folders(directory):
    for f in os.scandir(directory):
        if f.is_dir():
            yield (f.path.replace(directory + '/', '').replace(directory, ''))

def copy_file(source, target):
    touch_folder(Path(target).parent)
    shutil.copy2(source, target)

def copy_folder(source, target):
    shutil.copytree(source, target)

def touch_folder(folder):
    Path(folder).mkdir(parents=True, exist_ok=True)

def unzip(zip_file, target_dir):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

# threading utilities

class Error:
    def __init__(self, e):
        self.e = e

def thread_worker(fn, ctx, finish_queue):
    error = None
    try:
        job(fn, ctx)
    except BaseException as e:
        error = Error(e)
    except:
        error = Error(SystemError("Unknown"))

    finish_queue.put(error, False)

def job(fn, ctx):
    error = None
    for i in range(10):
        try:
            return fn()
        except Exception as e:
            print(f'Error on "{ctx}" attempt {i}')
            traceback.print_exc()
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

# network utilities

def fetch_text(url):
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f'Request to {url} failed')
    
    return r.text

def download_repository(path, url, branch):
    if Path(path).exists():
        shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)

    url = url.replace(f'/tree/{branch}', '')

    run('git init -q', path)
    run('git remote add origin ' + url, path)
    run('git -c protocol.version=2 fetch --depth=1 -q --no-tags --prune --no-recurse-submodules origin ' + branch, path)
    run('git checkout -qf FETCH_HEAD', path)

def download_file(url, target):
    r = requests.get(url, allow_redirects=True)
    if r.status_code != 200:
        raise Exception(f'Request to {url} failed')
    
    with open(target, 'wb') as f:
        f.write(r.content)

# execution utilities

def run(command, path):
    result = subprocess.run(shlex.split(command), cwd=path, shell=False, stderr=subprocess.STDOUT)
    if result.returncode == -2:
        raise KeyboardInterrupt()
    elif result.returncode != 0:
        print(f'returncode {result.returncode} from: {command}')
        raise Exception(f'returncode {result.returncode} from: {command}')

if __name__ == '__main__':
    main()
