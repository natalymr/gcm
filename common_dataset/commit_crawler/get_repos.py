import json
import os
import time
from pathlib import Path
from typing import Dict, List

import requests
from tqdm import tqdm

_keys = [
    "token a1e00335ceea4313eabe48ef321195713b77f7fd",
    "token 45fe70e767c19f2c9e49dfd97321e27dc0c23fcb",
    "token 6354b1062717819873a3635f3f77c1c1de86f948",
    "token 3617d65b797343e4fb93f2146320f6f5a63feec5",
    "token b954f9b410ca3d258d072d95975f62bfbbf0d332",
    "token 5fc7506a722c6332fa1f0374da11c05c509035fd",
    "token 0ea1a9b990ea6adb06d2489c3b0b0daf12ee4a95",
    "token 1f9f75e570bf5595791e621b0bd707bbbb44d0da",
    "token 85da3a3be60001e3ffad383647f280ba92caf4e7",
    "token 2fd67e8a7cde89e0a09a35b7e00ca7bb56a44ea5",
]

from_one_key = 2000
max_iters = 10000000000


def check_key(kkey: str):
    url = "https://api.github.com/rate_limit"
    r = requests.get(url, headers={'Authorization': kkey})
    json_data = r.json()
    num = json_data['resources']['core']['remaining']
    print(kkey, num)
    return num


def check_keys():
    kk = []
    for key in _keys:
        num = check_key(key)
        if num > 4500:
            kk.append(key)
    return kk


def check_request_result(status, url: str):
    if status is not None:
        print(f'Error! Message: {status} {url}')
        raise Exception('Stopped.')


def get_data_from_github_api(request: str, key: str, page_number: int, per_page: int) -> Dict:
    url: str = 'https://api.github.com/' + request + f'&page={page_number}&per_page={per_page}'
    request_result = requests.get(url, headers={'Authorization': key}).json()
    # check_request_result(request_result.get('message'), url)
    return request_result


def get_repos(output_file: str, per_page: int) -> None:
    """
    We want top 1k repos on java language, so, we'll send 1000/{per_page} requests
    :param output_file: where all collected repos will store
    """
    request = 'search/repositories?q=stars:>1000+language:Java&sort=stars'
    all_repos = 1000
    keys = check_keys()
    data = get_data_from_github_api(request, keys[0], 1, per_page)
    for page_number in tqdm(range(2, int(all_repos / per_page) + 1)):
        data['items'].extend(get_data_from_github_api(request, keys[0], page_number, per_page)['items'])

    with open(output_file, 'w') as output_f:
        output_f.write(json.dumps(data, indent=2))


def get_commits(repo_file: str, output_dir: Path, per_page: int):
    with open(repo_file, 'r') as f:
        repos = json.load(f)
    all_downloaded_files: List[str] = os.listdir(output_dir)
    # we need only top-1k repos, so, let's get counter
    counter: int = len(all_downloaded_files)
    print(f'Number of all repos: {len(repos["items"])}')
    for cur_repo in repos['items']:

        cur_repo_name = cur_repo['full_name']
        print(f'Current repo: {cur_repo_name}')
        if cur_repo_name.replace('/', '_') in all_downloaded_files:
            continue
        keys = check_keys()
        print(f'Number of left keys: {len(keys)}')
        if not keys:
            time.sleep(600)
        counter += 1
        if counter > 1000:
            break

        cur_repo_output_file: Path = output_dir / cur_repo_name.replace('/', '_')
        cur_repo_commits = get_data_from_github_api('repos/' + cur_repo_name + '/commits', keys[0])
        with open(cur_repo_output_file, 'w') as output_f:
            output_f.write(json.dumps(cur_repo_commits, indent=2))


def cut_part(content):
    was_len = len(content)
    part = content[:from_one_key]
    content = content[from_one_key:]
    assert len(content) + len(part) == was_len
    return part, content


def get_commits_number(input_file: str):
    with open(input_file, 'r') as f:
        commits = json.load(f)
    print(f'Number of commits for {input_file} is {len(commits)}')


if __name__ == '__main__':
    get_repos(Path('../../../new_data/repos.json'), 100)
    # get_commits(Path('../data/raw_data/repos.json'), Path('../data/raw_data/commits'), 100)
    # get_commits_number(Path('../data/raw_data/commits/apache_dubbo'))