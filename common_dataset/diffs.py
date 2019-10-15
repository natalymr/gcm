import difflib
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict

from code2seq_dataset.global_vars import Commit, Message, Blob
from code2seq_dataset.info_classes import FullLogLine
from code2seq_dataset.process_dataset_rnn_case import get_commit_vs_blobs
from common_dataset.logs import COMMON_SEP


@dataclass
class FileDiff:
    file_name: str
    status: str
    diff_body: List[str]

    @staticmethod
    def from_dict(input):
        return FileDiff(file_name=input['file_name'], status=input['status'], diff_body=input['diff_body'])


    @staticmethod
    def __my_git_diff(old_blob: Blob, new_blob: Blob, status: str, context_size: int, git_dir: Path) -> List[str]:
        if status == 'M':
            try:
                return subprocess.check_output(f'git diff {old_blob} {new_blob} -U{context_size}'.split(),
                                               cwd=git_dir,
                                               stderr=subprocess.PIPE).decode('utf-8').split('\n')
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []
        if status == 'A':
            try:
                lines = subprocess.check_output(f'git cat-file -p {new_blob}'.split(), cwd=git_dir).decode('utf-8').split('\n')
                return list(difflib.ndiff([], lines))
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []
        if status == 'D':
            try:
                lines = subprocess.check_output(f'git cat-file -p {old_blob}'.split(), cwd=git_dir).decode('utf-8').split('\n')
                return list(difflib.ndiff(lines, []))
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")

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
            print(f"At {i}")
        # if i < 19540:
        #     continue
        message = Message(changed_files[0].message)
        author = changed_files[0].author
        files_diffs = get_all_diffs_per_commit(changed_files, context_size, git_dir)
        commits_diffs.append(CommitDiff(commit=commit, message=message, author=author, changed_java_files=files_diffs))

    with open(output, 'w') as output_f:
        output_f.write(json.dumps(commits_diffs, default=CommitDiff.to_json, indent=2))


if __name__ == '__main__':
    git_dir_name: str = 'camel'
    git_dir: Path = Path(f'/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/{git_dir_name}')
    output_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath("raw_data").joinpath(git_dir_name)
    if not output_dir.exists():
        output_dir.mkdir()
    changed_files_log: Path = output_dir.joinpath("changed_java_files.log")
    context_size: int = 10
    all_diffs: Path = output_dir.joinpath(f"diffs_context_size_{context_size}.json")

    get_diffs(changed_files_log, all_diffs, context_size, git_dir)
