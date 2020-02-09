import json
import os
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Set

import sys
sys.path.append('/home/ubuntu/crawler/gcm')

from common_dataset.diffs import get_diffs
from common_dataset.logs import get_commits_log, get_changed_java_files_log


class LocalGitRepository:
    def __init__(self, full_name: str, parent_dir: Path):
        self.full_name: str = full_name
        self.git_dir_name: str = full_name.split('/')[1]
        self.parent_repository: Path = parent_dir
        self.path: Path = parent_dir / self.git_dir_name

    def __enter__(self):
        subprocess.call(f'git clone https://github.com/{self.full_name}.git',
                        cwd=self.parent_repository,
                        shell=True)
        if self.path.exists():
            print('Finished cloning')
            return self.path

    def __exit__(self, type, value, traceback):
        subprocess.call(f'rm -rf {self.git_dir_name}',
                        cwd=self.parent_repository,
                        shell=True)


def get_logs_and_diffs(repos_file_json: Path):
    with open(repos_file_json, 'r') as f:
        repos = json.load(f)
    repos_full_names_tmp: List[str] = [repo['full_name'] for repo in repos['items']][:1000]
    set_repos: Set[str] = set(repos_full_names_tmp)
    if len(repos_full_names_tmp) == len(set_repos):
        print('Everything is fine')
    else:
        print('We have dublicates for repos')
    print(f'Len of repos is {len(repos_full_names_tmp)}')
    parent_dir: Path = Path('../../../new_data/raw_data/')
    already_downloaded_files: List[str] = os.listdir(parent_dir)
    already_downloaded: Path = parent_dir.joinpath('downloaded.log')
    downloaded: List[str] = []
    with open(already_downloaded, 'w') as f:
        for already_downloaded_file in already_downloaded_files:
            if already_downloaded_file.endswith('.commits.logs'):
                [name, _] = already_downloaded_file.split('.commits.')
                name: str = name.replace('_', '/')
                f.write(f'{name}\n')
                downloaded.append(name)
    repos_full_names: List[str] = [repo for repo in repos_full_names_tmp if repo not in downloaded]
    print(f'NEW Len of repos is {len(repos_full_names)}')
    with multiprocessing.Pool() as pool:
        pool.map(download_everything_for_one_repository, repos_full_names)


def download_everything_for_one_repository(repo_full_name: str):
    print(f'Start to process {repo_full_name}')
    # the parent_dir should ba argument, but for pool.map
    parent_dir: Path = Path('../../../new_data/raw_data/')
    already_downloaded: Path = parent_dir.joinpath('downloaded.log')
    with open(already_downloaded, 'a') as f:
        f.write(f'{repo_full_name}\n')
    dir_for_repos: Path = Path('../../../new_data/')

    with LocalGitRepository(repo_full_name, dir_for_repos) as git_dir:
        appropriate_full_name = repo_full_name.replace("/", "_")
        commits_log: Path = parent_dir.joinpath(f'{appropriate_full_name}.commits.logs')
        changed_files_log: Path = parent_dir.joinpath(f'{appropriate_full_name}.changed_files.logs')
        diffs_file: Path = parent_dir.joinpath(f'{appropriate_full_name}.diffs.LOC_10.json')
        try:
            # get logs
            get_commits_log(git_dir, commits_log, '2000-01-01', '2019-12-12')
            get_changed_java_files_log(git_dir, changed_files_log, commits_log)

            # get diffs
            get_diffs(changed_files_log, diffs_file, 10, git_dir)
        except Exception as e:
            try:
                commits_log.unlink()
                changed_files_log.unlink()
                diffs_file.unlink()
            except FileNotFoundError:
                pass
            error_log: Path = parent_dir.joinpath('errors.log')
            with open(error_log, 'a') as error:
                error.write(f'{repo_full_name}\n')
                error.write(f'{str(e)}\n')


def main():
    repos_file: Path = Path('../../../new_data/repos.json')
    # test()
    get_logs_and_diffs(repos_file)


if __name__ == '__main__':
    main()
