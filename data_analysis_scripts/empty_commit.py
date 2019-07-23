import os
from pickle import dump
from subprocess import call, check_output
from typing import List


class ChangedFile:
    def __init__(self, old_blob, cur_blob, status, file_name):
        self.old_blob = old_blob
        self.cur_blob = cur_blob
        self.status = status
        self.file_name = file_name

    def __str__(self):
        return f"{self.status}; {self.file_name}; {self.old_blob}; {self.cur_blob}"


def parse_diff_tree_command(old_commit: str, cur_commit: str, file_name: str, git_dir: str) -> List[ChangedFile]:
    tmp_file = os.path.join(git_dir, file_name)

    call(f"cd {git_dir} && git diff-tree -r -M {old_commit} {cur_commit} > {tmp_file}", shell=True)
    result = []

    with open(tmp_file, 'r') as file:
        for line in file:
            line_list = line.split()
            old_blob, cur_blob, status, file_name = line_list[2], line_list[3], line_list[4], line_list[5]
            result.append(ChangedFile(old_blob, cur_blob, status, file_name))

    if not result:
        print(f"NO RESULT old = {old_commit} cur = {cur_commit}")

    return result


def collect_statistics_no_changing_commits(com_com_log: str, output_file: str, git_dir: str):
    author_vs_number = {}
    with open(com_com_log, 'r') as com_com_log_file:
        i = 0
        for line in com_com_log_file:
            i += 1

            if i > 1000:
                break

            if i % 20 == 0:
                print(f"{i}")

            if line.startswith("parent_commit_file_hash"):
                continue
            line_list = line.split(";")
            parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[2], line_list[3]
            changed_files = parse_diff_tree_command(parent_commit, cur_commit, "aaa", git_dir)
            if not changed_files:
                if author not in author_vs_number:
                    author_vs_number[author] = [(cur_commit, message)]
                else:
                    author_vs_number[author].append((cur_commit, message))

    with open(output_file, 'w') as file:
        file.write("Author; \t Number of commits that does not change any file; \t Commit-files hash;\n")
        for author, commits  in author_vs_number.items():
            file.write("{:>20}; {:>5};\n".format(author, len(commits)))
            file.write("{}; \n\n\n".format(commits))


def collect_all_no_changing_commits(com_com_log: str, output_file: str, git_dir: str):
    empty_commits = set()
    try:
        with open(com_com_log, 'r') as com_com_log_file:
            i = 0
            for line in com_com_log_file:
                i += 1
                if i < 1700:
                    continue

                if i % 20 == 0:
                    print(f"{i}")

                if i % 100 == 0:
                    print(f"Empry commits number: {len(empty_commits)}")

                if line.startswith("parent_commit_file_hash"):
                    continue
                line_list = line.split(";")
                # print(line_list)
                parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[2], line_list[3]
                changed_files = parse_diff_tree_command(parent_commit, cur_commit, "aaa", git_dir)
                if not changed_files:
                    empty_commits.add(cur_commit)
    except Exception:
        print("everything is bad")

    print(f"Number of empty commits {len(empty_commits)}")
    print(empty_commits)

    with open(output_file, 'wb') as file:
        dump(empty_commits, file)


def collect_statistics_no_changing_commits_per_author(commit_history_len: int, com_com_log: str,
                                                      output_dir: str, git_dir: str):
    # collect commits that does not change any file
    author_vs_number = {}
    with open(com_com_log, 'r') as com_com_log_file:
        i = 0
        for line in com_com_log_file:
            i += 1
            # if i > 40:
            #     break

            if i % 20 == 0:
                print(f"{i}")

            if line.startswith("parent_commit_file_hash"):
                continue
            line_list = line.split(";")
            parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[2], line_list[3]
            changed_files = parse_diff_tree_command(parent_commit, cur_commit, "aaa", git_dir)
            if not changed_files:
                if author not in author_vs_number:
                    author_vs_number[author] = [cur_commit]
                else:
                    author_vs_number[author].append(cur_commit)

    # for each author get "commit_history_len" prev commits for each empty commit
    # and write results to the corresponding file
    for author, commits in author_vs_number.items():
        output_file = os.path.join(output_dir, f"no_changes_{author}.log")
        for commit in commits:
            call(f"echo '\n\n|-----------------------new empty commit history with {commit_history_len} len-----------------------|' >> {output_file}",
                 shell=True)
            call(f"cd {git_dir} && git log --parents {commit} -n {commit_history_len} --raw --author={author} >> {output_file}",
                 shell=True)


if __name__ == "__main__":
    # values
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir_name = "intellij"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    no_change_commit_log_file = f"no_files_change_commits_{git_dir_name}.log"
    no_change_commit_log_file = os.path.join(parent_dir, no_change_commit_log_file)
    no_change_commit_pickle_file = f"no_files_change_commits_{git_dir_name}.pickle"
    no_change_commit_pickle_file = os.path.join(parent_dir, no_change_commit_pickle_file)
    log_output_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/no_changes_logs"

    # collect_statistics_no_changing_commits(com_com_log_file, no_change_commit_log_file, git_dir)

    # collect_statistics_no_changing_commits_per_author(10, com_com_log_file, log_output_dir, git_dir)
    print("hello")
    # collect_all_no_changing_commits(com_com_log_file, no_change_commit_pickle_file, git_dir)