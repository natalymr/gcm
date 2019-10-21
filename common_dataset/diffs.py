import difflib
import json
import re
import subprocess
from pathlib import Path
from enum import Enum
from typing import List, Dict
from dataclasses import dataclass, asdict

from code2seq_dataset.global_vars import Commit, Message, Blob
from code2seq_dataset.info_classes import FullLogLine, FileStatus
from code2seq_dataset.process_dataset_rnn_case import get_commit_vs_blobs
from common_dataset.logs import COMMON_SEP


@dataclass
class FileDiff:
    file_name: str
    status: FileStatus
    diff_body: List[str]

    @staticmethod
    def from_dict(input):
        return FileDiff(file_name=input['file_name'], status=input['status'], diff_body=input['diff_body'])

    def delete_useless_git_diff_output(self):
        """
        Delete some useless output from git diff command,
        This lines will be deleted:
         'diff --git a / b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef b / 6f2f19b981c9fbc66138807b4d199851a2fd13e9'
         'index b5cb9bb9bf2 . . 6f2f19b981c 100644'
         '--- a / b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef'
         '+++ b / 6f2f19b981c9fbc66138807b4d199851a2fd13e9'
        """
        new_diff_body: List[str] = []
        for line in self.diff_body:
            if not line.startswith('diff --git') and not line.startswith('index') and \
                    not line.startswith('---') and not line.startswith('+++'):
                new_diff_body.append(line)
        self.diff_body = new_diff_body

    def keep_only_needed_number_of_line_around_changes(self, context_size_in_lines: int):
        """
        This function will keep only those line that are reletaed to changes or its context
        :param context_size_in_lines: what number of lines will be saved around changes
        """
        mask: List[int] = [0] * len(self.diff_body)
        for i, line in enumerate(self.diff_body):
            if line.startswith('@@'):
                mask[i] = 1
            if line.startswith('+') or line.startswith('-'):
                min_ind = max(0, i - context_size_in_lines)
                max_ind = min(i + context_size_in_lines, len(self.diff_body) - 1)
                for j in range(min_ind, max_ind + 1):
                    mask[j] = 1
        self.diff_body = [self.diff_body[i] for i, v in enumerate(mask) if v]

    def tokenize_each_line_of_diff_body(self) -> int:
        new_diff_body: List[str] = []
        total_tokens_count: int = 0
        for line in self.diff_body:
            line = re.sub(r'\"([^\\\"]|\\.)*\"', 'str_variable', line)
            line = re.sub(r'(\w)(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
            line = re.sub(r'([^a-zA-Z0-9_ ])(?=\w)', r'\1 ', line)
            line = re.sub(r'([^a-zA-Z0-9_ ])(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
            line = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', line)
            total_tokens_count += len(line.split(' '))
            new_diff_body.append(line)
        self.diff_body = new_diff_body
        return total_tokens_count

    def tokenize_camel_case(self):
        new_diff_body: List[str] = []

        for line in self.diff_body:
            line = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', line)).lower()
            new_diff_body.append(line)

        self.diff_body = new_diff_body

    @staticmethod
    def __my_git_diff(old_blob: Blob, new_blob: Blob, status: str, context_size: int, git_dir: Path) -> List[str]:
        if status == FileStatus.MODIFIED:
            try:
                return subprocess.check_output(f'git diff {old_blob} {new_blob} -U{context_size}'.split(),
                                               cwd=git_dir,
                                               stderr=subprocess.PIPE).decode('utf-8').split('\n')
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []
        if status == FileStatus.ADDED:
            try:
                lines = subprocess.check_output(f'git cat-file -p {new_blob}'.split(), cwd=git_dir).decode('utf-8').split('\n')
                return list(difflib.ndiff([], lines))
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []
        if status == FileStatus.DELETED:
            try:
                lines = subprocess.check_output(f'git cat-file -p {old_blob}'.split(), cwd=git_dir).decode('utf-8').split('\n')
                return list(difflib.ndiff(lines, []))
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []

    @staticmethod
    def from_git_diff(changed_files_log_line: FullLogLine, context_size: int, git_dir: Path) -> 'FileDiff':
        return FileDiff(file_name=changed_files_log_line.file,
                        status=changed_files_log_line.status,
                        diff_body=FileDiff.__my_git_diff(changed_files_log_line.old_blob,
                                                         changed_files_log_line.new_blob,
                                                         changed_files_log_line.status,
                                                         context_size,
                                                         git_dir))


@dataclass
class CommitDiff:
    commit: Commit
    message: Message
    author: str
    changed_java_files: List[FileDiff]
    is_there_dobj: bool = False
    @staticmethod
    def to_json(self) -> None:
        return asdict(self)
    @staticmethod
    def from_dict(input) -> 'CommitDiff':
        return CommitDiff(commit=Commit(input['commit']),
                          message=Message(input['message']),
                          author=input['author'],
                          changed_java_files=[FileDiff.from_dict(file) for file in input['changed_java_files']])


def get_all_diffs_per_commit(changed_files: List[FullLogLine], context_size: int, git_dir: Path) -> List[FileDiff]:
    return [
        FileDiff.from_git_diff(changed_file, context_size, git_dir)
        for changed_file in changed_files
    ]


def get_diffs(changed_files_log: Path, output: Path, context_size: int, git_dir: Path):
    commits_diffs: List[CommitDiff] = []
    commit_vs_blobs: Dict[Commit, List[FullLogLine]] = get_commit_vs_blobs(changed_files_log, sep=COMMON_SEP)
    i = 0

    for commit, changed_files in commit_vs_blobs.items():
        i += 1
        if i % 10 == 0:
            print(f"At {i} from 165542")
        # if i < 19540:
        #     continue
        message = Message(changed_files[0].message)
        author = changed_files[0].author
        files_diffs = get_all_diffs_per_commit(changed_files, context_size, git_dir)
        commits_diffs.append(CommitDiff(commit=commit, message=message, author=author, changed_java_files=files_diffs))

    with open(output, 'w') as output_f:
        output_f.write(json.dumps(commits_diffs, default=CommitDiff.to_json, indent=2))


if __name__ == '__main__':
    git_dir_name: str = 'intellij'
    git_dir: Path = Path(f'/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/packed_intellij/{git_dir_name}')
    output_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath('raw_data').joinpath(git_dir_name)
    if not output_dir.exists():
        output_dir.mkdir()
    changed_files_log: Path = output_dir.joinpath('changed_java_files.log')
    context_size: int = 10
    all_diffs: Path = output_dir.joinpath(f'diffs_context_size_{context_size}.json')

    get_diffs(changed_files_log, all_diffs, context_size, git_dir)
