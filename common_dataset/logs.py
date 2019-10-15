import random
import subprocess
import string
from dataclasses import dataclass
from pathlib import Path
from typing import List

from code2seq_dataset.global_vars import Blob, changed_files_log_line
from code2seq_dataset.info_classes import CommitLogLine

COMMON_SEP = "<SEP>"


def get_commits_log(git_dir: Path, output: Path, start_date: str, end_date: str):
    global COMMON_SEP
    log_pretty_template = f'"%P{COMMON_SEP}%H{COMMON_SEP}%an{COMMON_SEP}%cd{COMMON_SEP}%s{COMMON_SEP}"'

    with open(output, 'w') as file:
        subprocess.call(f'git log --pretty={log_pretty_template} --since={start_date} --before={end_date} --no-merges',
                        cwd=git_dir,
                        stdout=file,
                        shell=True)

    commits_count = subprocess.check_output(f"wc -l {output}".split()).decode().split()[0]
    print(f"Commits number is {commits_count}")


@dataclass
class ChangedFile:
    old_blob: Blob
    new_blob: Blob
    status: str
    file_name: str

    @staticmethod
    def parse_from_git_diff_tree_line(line: str) -> 'ChangedFile':
        list_ = line.split()
        return ChangedFile(old_blob=Blob(list_[2]),
                           new_blob=Blob(list_[3]),
                           status=list_[4],
                           file_name=list_[5])


def run_and_parse_diff_tree(parent_commit: str, cur_commit: str, git_dir: Path) -> List[ChangedFile]:
    tmp_file: Path = Path.cwd().joinpath(''.join(random.sample(string.ascii_lowercase, 10)))  # (random file name)
    with open(tmp_file, 'w') as file:
        subprocess.call(f"git diff-tree -r -M {parent_commit} {cur_commit}",
                        cwd=git_dir,
                        stdout=file,
                        shell=True)

    result: List[ChangedFile] = []
    with open(tmp_file, 'r') as file:
        for line in file:
            result.append(ChangedFile.parse_from_git_diff_tree_line(line))

    tmp_file.unlink()  # delete tmp file
    return result


def is_java_file(file: ChangedFile) -> bool:
    return file.file_name.endswith(".java")


def get_changed_java_files_log(git_dir: Path, output: Path, commits_log: Path):
    global COMMON_SEP
    total_commit_number: int = subprocess.check_output(f'wc -l {commits_log}'.split()).decode().split()[0]
    commits_with_changed_java_files_number: int = 0
    commit_number: int = 0

    with open(output, 'w') as output_f, open(commits_log, 'r') as commits_log_f:
        for line in commits_log_f:
            commit_number += 1
            if commit_number % 100 == 0:
                print(f'Start to process {commit_number} commit from {total_commit_number}')

            # if commits_with_changed_java_files_number > 4_000:
            #     break

            commits_log_line: CommitLogLine = CommitLogLine.parse_from_line(line, separator=COMMON_SEP)
            changed_files: List[ChangedFile] = run_and_parse_diff_tree(commits_log_line.parent_commit,
                                                                       commits_log_line.current_commit,
                                                                       git_dir)

            changed_files = list(filter(is_java_file, changed_files))
            if not changed_files:
                continue

            commits_with_changed_java_files_number += 1
            for changed_file in changed_files:
                output_f.write(changed_files_log_line.substitute(commit_hash=commits_log_line.current_commit,
                                                                 author=commits_log_line.author,
                                                                 status=changed_file.status,
                                                                 file_name=changed_file.file_name,
                                                                 old_blob=changed_file.old_blob,
                                                                 new_blob=changed_file.new_blob,
                                                                 message=commits_log_line.message,
                                                                 sep=COMMON_SEP))
    print(f"Number of commits with changed java files is {commits_with_changed_java_files_number}")


if __name__ == '__main__':
    git_dir_name: str = "camel"
    git_dir: Path = Path(f"/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/{git_dir_name}")
    output_dir: Path = Path.cwd().parent.parent.joinpath("data").joinpath("raw_data").joinpath(git_dir_name)
    if not output_dir.exists():
        output_dir.mkdir()
    commits_log: Path = output_dir.joinpath("commits.log")
    changed_files_log: Path = output_dir.joinpath("changed_java_files.log")

    get_commits_log(git_dir, commits_log, "1999-01-01", "2019-11-10")
    get_changed_java_files_log(git_dir, changed_files_log, commits_log)
