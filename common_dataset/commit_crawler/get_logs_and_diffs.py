import json
import subprocess
from pathlib import Path
from typing import List

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
            return self.path

    def __exit__(self, type, value, traceback):
        subprocess.call(f'rm -r {self.git_dir_name}',
                        cwd=self.parent_repository,
                        shell=True)


def test():
    full_name = 'natalymr/spbau_java_hw'
    parent_dir = Path('/Users/natalia.murycheva/crawler_test')
    with LocalGitRepository(full_name, parent_dir) as git_dir:
        appropriate_full_name = full_name.replace("/", "_")
        # get logs
        commits_log: Path = parent_dir.joinpath(f'{appropriate_full_name}.commits.logs')
        changed_files_log: Path = parent_dir.joinpath(f'{appropriate_full_name}.changed_files.logs')
        get_commits_log(git_dir, commits_log, '2000-01-01', '2019-12-12')
        get_changed_java_files_log(git_dir, changed_files_log, commits_log)

        # get diffs
        diffs_file: Path = parent_dir.joinpath(f'{appropriate_full_name}.diffs.LOC_10.json')
        get_diffs(changed_files_log, diffs_file, 10, git_dir)


def get_logs_and_diffs(repos_file_json: Path, parent_dir: Path) -> List[str]:
    with open(repos_file_json, 'r') as f:
        repos = json.load(f)

    for cur_repo in repos['items']:
        cur_repo_full_name = cur_repo['full_name']
        with LocalGitRepository(cur_repo_full_name, parent_dir) as git_dir:
            appropriate_full_name = cur_repo_full_name.replace("/", "_")
            # get logs
            commits_log: Path = parent_dir.joinpath(f'{appropriate_full_name}.commits.logs')
            changed_files_log: Path = parent_dir.joinpath(f'{appropriate_full_name}.changed_files.logs')

            get_commits_log(git_dir, commits_log, '2000-01-01', '2019-12-12')
            get_changed_java_files_log(git_dir, changed_files_log, commits_log)

            # get diffs
            diffs_file: Path = parent_dir.joinpath(f'{appropriate_full_name}.diffs.LOC_10.json')

            get_diffs(changed_files_log, diffs_file, 10, git_dir)

        break


def main():
    repos_file: Path = Path('../data/raw_data/repos.json')
    # test()
    raw_data_dir: Path = Path('../data/raw_data/')
    get_logs_and_diffs(repos_file, raw_data_dir)


if __name__ == '__main__':
    main()
