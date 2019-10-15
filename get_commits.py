import os
from dataclasses import dataclass
from subprocess import call, check_output
from typing import List

from code2seq_dataset.global_vars import Blob

SEPARATOR = "THIS_STRING_WILL_NEVER_APPEAR_IN_DATASET_AND_IT_WILL_BE_USED_AS_SEPARATOR"


def parse_shortlog_command(git_dir: str) -> int:
    """
        NB: command to check commits total count
            git shortlog -s -n --all --no-merges

            command to get number of lines in file
            wc -l <filename>
    """
    tmp_file = os.path.join(git_dir, "tmp")
    cd_command = f"cd {git_dir}"
    git_com_count_command = "git shortlog -s -n --all --no-merges"
    write_to_file_command = f" > {tmp_file}"
    commit_total_count = 0
    call(cd_command + " && " + git_com_count_command + write_to_file_command, shell=True)
    with open(tmp_file, 'r') as file:
        for line in file:
            print(line)
    with open(tmp_file, 'r') as file:
        for line in file:
            line_list = line.split()
            commit_total_count += int(line_list[0])
    return commit_total_count


def create_com_com_log_file(com_com_log: str, start_date: str, end_date: str, git_dir: str) -> int:
    global SEPARATOR
    print("Start to create com_com_log file")
    # logic
    cd_command = f"cd {git_dir}"
    git_log_command = f'git log --pretty="%P{SEPARATOR}%H{SEPARATOR}%an{SEPARATOR}%cd{SEPARATOR}%s{SEPARATOR}" ' \
        f'--since={start_date} --before={end_date} ' \
        f'--no-merges'
        # ?f'--branches --all --no-merges'
    write_to_file_command = f" > {com_com_log}"
    call(cd_command + " && " + git_log_command + write_to_file_command, shell=True)
    # check that we've got all commits
    total_count_expected = parse_shortlog_command(git_dir)
    total_count_actual = check_output(f"wc -l {com_com_log}".split()).decode().split()[0]
    total_count_actual = int(total_count_actual) - 1  # because of header, one line
    if total_count_actual == total_count_expected:
        print("Everything is fine! Got all commits")
    else:
        print(f"Expected commits count \t {total_count_expected}")
        print(f"Actual commits count \t {total_count_actual}")
    print("Finished to create com_com_log file")
    return total_count_actual


@dataclass
class ChangedFile:
    old_blob: Blob
    new_blob: Blob
    status: str
    file_name: str

    def __str__(self):
        return f"{self.status}{SEPARATOR}{self.file_name}{SEPARATOR}{self.old_blob}{SEPARATOR}{self.new_blob}"

    @staticmethod
    def parse_from_git_diff_tree_line(line: str) -> 'ChangedFile':
        list_ = line.split()
        return ChangedFile(old_blob=Blob(list_[2]),
                           new_blob=Blob(list_[3]),
                           status=list_[4],
                           file_name=list_[5])


def parse_diff_tree_command(old_commit: str, cur_commit: str, file_name: str, git_dir: str) -> List[ChangedFile]:
    tmp_file = os.path.join(git_dir, file_name)
    call(f"cd {git_dir} && git diff-tree -r -M {old_commit} {cur_commit} > {tmp_file}", shell=True)
    result: List[ChangedFile] = []

    with open(tmp_file, 'r') as file:
        for line in file:
            result.append(ChangedFile.parse_from_git_diff_tree_line(line))

    return result


def check_there_is_changed_java_file_in_commit(changed_files: List[ChangedFile]) -> bool:
    for changed_file in changed_files:
        if changed_file.file_name.endswith(".java"):
            return True

    return False


def create_full_log_file(com_com_log: str, full_log: str, git_dir: str):
    print("Start to create full_log file")
    commits_with_changed_java_files_number: int = 0
    with open(full_log, 'w') as full_log_file:
        total_blobs_count = 0
        with open(com_com_log, 'r') as com_com_log_file:
            commit_number = 0
            for line in com_com_log_file:
                commit_number += 1
                if commit_number % 20 == 0:
                    print(f"Start to process {commit_number} commit; Blobs count top score {total_blobs_count}")

                if commits_with_changed_java_files_number > 4_000:
                    break
                line_list = line.split(SEPARATOR)
                parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[4], line_list[2]
                changed_files: List[ChangedFile] = parse_diff_tree_command(parent_commit, cur_commit, "qwerty", git_dir)
                total_blobs_count += len(changed_files)

                if check_there_is_changed_java_file_in_commit(changed_files):
                    commits_with_changed_java_files_number += 1
                    for changed_file in changed_files:
                        full_log_file.write(f"{cur_commit}{SEPARATOR}{author}{SEPARATOR}"
                                            f"{changed_file}{SEPARATOR}{message}{SEPARATOR}\n")

    print(f"Top score for blobs number {total_blobs_count}")
    print("Finished to create full_log file")


if __name__ == "__main__":
    # values
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "dubbo"
    # packed_dir = "packed_intellij"
    git_dir = os.path.join(parent_dir, git_dir_name)
    start_date = "2004-01-01"
    end_date = "2019-31-09"
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    full_log_file = f"gcm_{git_dir_name}_full.log"
    full_log_file = os.path.join(parent_dir, full_log_file)
    blobs_dir = os.path.join(parent_dir, f"{git_dir_name}_blobs")

    # commit_commit file
    commit_count = create_com_com_log_file(com_com_log_file, start_date, end_date, git_dir)
    print("Number of commits: {}".format(commit_count))

    # full log file
    create_full_log_file(com_com_log_file, full_log_file, git_dir)
