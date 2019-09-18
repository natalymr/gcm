from code2seq_dataset.info_classes import CommitLogLine, FullLogLine
from keras.preprocessing.text import text_to_word_sequence
from pathlib import Path
import pickle
from typing import Set


def get_commits_for_train_aurora(com_log: Path, empty_commits_file: Path, is_pickle: bool,
                                 commits_for_train_file: Path, new_com_log: Path):
    needed_commits: Set[str] = set()
    with open(empty_commits_file, 'rb') as file:
        empty_commits: Set[str] = pickle.load(file)

    with open(new_com_log, 'w') as new_log_file, open(com_log, 'r') as old_log_file:
        total_commit_number: int = 0

        for line in old_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue

            commit_log_line: CommitLogLine = CommitLogLine.parse_from_line(line)
            if commit_log_line.current_commit in empty_commits:
                continue

            message = commit_log_line.message.lower()
            if commit_log_line.author == "builder":
                if message == "new version" or \
                        message == "build completed" or \
                        message == "build failed":
                    continue
            if message == "no message" or \
                    message == "*** empty log message ***" or \
                    message.startswith("this commit was manufactured by cvs2svn"):
                continue
            text_list = text_to_word_sequence(message)
            if text_list:
                total_commit_number += 1
                needed_commits.add(commit_log_line.current_commit)
            new_log_file.write(f"{line}")

    print(f"Number of needed commits {len(needed_commits)}")

    if is_pickle:
        with open(commits_for_train_file, 'wb') as file:
            pickle.dump(needed_commits, file)
    else:
        with open(commits_for_train_file, 'w') as file:
            for commit in needed_commits:
                file.write(f"{commit}\n")


def get_commits_for_train_intellij(com_log: Path, empty_commits_file: Path, is_pickle: bool,
                                   commits_for_train_file: Path, new_com_log: Path):
    needed_commits: Set[str] = set()
    with open(empty_commits_file, 'rb') as file:
        empty_commits: Set[str] = pickle.load(file)

    with open(new_com_log, 'w') as new_com_log_file, open(com_log, 'r') as com_log_file:
        total_commit_number: int = 0
        for line in com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue

            commit_log_line: CommitLogLine = CommitLogLine.parse_from_line(line)

            if commit_log_line.current_commit in empty_commits:
                continue
            message = commit_log_line.message.lower()
            if message == "(no message)":
                continue
            text_list = text_to_word_sequence(message)
            if text_list:
                total_commit_number += 1
                needed_commits.add(commit_log_line.current_commit)
            new_com_log_file.write(f"{line}")

    print(f"Number of needed commits {len(needed_commits)}")

    if is_pickle:
        with open(commits_for_train_file, 'wb') as file:
            pickle.dump(needed_commits, file)
    else:
        with open(commits_for_train_file, 'w') as file:
            for commit in needed_commits:
                file.write(f"{commit}\n")


def create_new_full_log_file(old_full_log: Path, new_full_log: Path, commits_for_train_file: Path):
    with open(commits_for_train_file, 'rb') as f:
        needed_commits: Set[str] = pickle.load(f)

    with open(new_full_log, 'w') as new_full_log_file, open(old_full_log, 'r') as old_full_log_file:
        for line in old_full_log_file:
            if line.startswith("commit_hash"):
                continue

            full_log_line: FullLogLine = FullLogLine.parse_from_line(line)
            if full_log_line.commit in needed_commits:
                new_full_log_file.write(line)


if __name__ == "__main__":
    git_dir_name: str = "aurora"
    parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")

    com_log_file: Path = parent_dir.joinpath(f"gcm_{git_dir_name}_com_com_msg_author_date_2010.log")
    new_com_log_file: Path = parent_dir.joinpath(f"gcm_{git_dir_name}_for_train_com_com_author_date.log")
    empty_commits_file: Path = parent_dir.joinpath(f"no_files_change_commits_{git_dir_name}.pickle")
    commits_for_train_file: Path = parent_dir.joinpath(f"{git_dir_name}_commits_for_train.pickle")

    # get_commits_for_train_intellij(com_log_file, empty_commits_file, True, commits_for_train_file,
    #                                new_com_log_file)

    old_full_log: Path = parent_dir.joinpath(f"gcm_{git_dir_name}_full.log")
    new_full_log: Path = parent_dir.joinpath(f"gcm_{git_dir_name}_full_log_for_train_commits.log")

    # create_new_full_log_file(old_full_log, new_full_log, commits_for_train_file)
