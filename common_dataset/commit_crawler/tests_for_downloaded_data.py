import json
import os
import subprocess
import unittest
from pathlib import Path
from typing import List, Tuple

from common_dataset.diffs import CommitDiff


def get_repo_name(file_name: str, sep: str) -> str:
    [name, *_] = file_name.split(sep)
    return name


class DiffTest(unittest.TestCase):

    dir_with_files: Path = Path('../../../new_data/raw_data/')
    all_downloaded_files: List[str] = os.listdir(dir_with_files)
    repo_names: List[str] = [get_repo_name(f, '.commits') for f in all_downloaded_files if f.endswith('.commits.logs')]

    @staticmethod
    def is_non_zero_file(fpath: Path) -> bool:
        return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

    def test_not_empty_commits_files(self):
        commits: List[Path] = [self.dir_with_files.joinpath(rn + '.commits.logs') for rn in self.repo_names]
        for commit in commits:
            with self.subTest(commit=commit):
                self.assertTrue(self.is_non_zero_file(commit),
                                msg=f'Something went wrong for {commit}')

    def test_changed_file_exists(self):
        changed_files: List[Path] = [self.dir_with_files.joinpath(rn + '.changed_files.logs') for rn in self.repo_names]

        for changed_file in changed_files:
            with self.subTest(changed_file=changed_file):
                self.assertTrue(changed_file.exists(), msg=f'Something went wrong for {changed_file}')

    def test_diff_files_exists(self):
        diff_files: List[Path] = [self.dir_with_files.joinpath(rn + '.diffs.LOC_10.json') for rn in self.repo_names]

        for diff in diff_files:
            with self.subTest(diff=diff):
                self.assertTrue(diff.exists(), msg=f'Something went wrong for {diff}')

    def test_not_empty_other_files(self):
        for repo_name in self.repo_names:
            with self.subTest(repo_name=repo_name):
                changed_file: Path = self.dir_with_files.joinpath(repo_name + '.changed_files.logs')
                diff_file: Path = self.dir_with_files.joinpath(repo_name + '.diffs.LOC_10.json')
                if not self.is_non_zero_file(changed_file) == self.is_non_zero_file(diff_file):
                    self.assertEqual(os.path.getsize(diff_file), 2,
                                     msg=f'Something went wrong for {repo_name}')

    @staticmethod
    def get_file_lines_count(fpath: Path) -> int:
        return int(subprocess.check_output(f"wc -l {fpath}".split()).decode().split()[0])

    @staticmethod
    def get_changed_files_count(fpath: Path) -> int:
        with open(fpath, 'r') as f:
            commits = json.load(f)
        return sum([len(CommitDiff.from_dict(commit).changed_java_files) for commit in commits])

    def test_count_changed_files_match(self):
        for repo_name in self.repo_names:
            with self.subTest(repo_name=repo_name):
                changed_file: Path = self.dir_with_files.joinpath(repo_name + '.changed_files.logs')
                diff_file: Path = self.dir_with_files.joinpath(repo_name + '.diffs.LOC_10.json')
                self.assertEqual(self.get_file_lines_count(changed_file), self.get_changed_files_count(diff_file),
                                 msg=f'test_count_changed_files_match: {self.get_file_lines_count(changed_file)} '
                                     f'vs. {self.get_changed_files_count(diff_file)} ')

    def test_get_raw_commits_number(self):
        total_count: int = 0
        for repo_name in self.repo_names:
            changed_file: Path = self.dir_with_files.joinpath(repo_name + '.changed_files.logs')
            total_count += self.get_file_lines_count(changed_file)

        print(f'Total raw commits count is {total_count}')

    def test_get_filtered_commits_number(self):
        processed_dir: Path = Path('../../../new_data/processed_data/')
        all_files: List[str] = os.listdir(processed_dir)
        total_count: int = 0
        for f in all_files:
            total_count += self.get_changed_files_count(processed_dir / f)

        print(f'Total filtered commits count is {total_count}')