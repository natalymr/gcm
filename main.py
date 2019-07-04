import os
from subprocess import call
from typing import List


def git_clone(http: str, parent_dir: str):
    print("go to storage_dir & start to clone")
    call(f"cd {parent_dir} && git clone {http}", shell=True)


def create_com_com_log_file(git_dir: str, start_date: str, end_date: str, output_file: str):
    call(f'echo "parent_commit_file_hash; current_commit_file_hash; message; author;" > {output_file}', shell=True)

    cd_command = f"cd {git_dir}"
    git_log_command = f'git log --pretty="%P;%H;%s;%an;" --since={start_date} --before={end_date}'
    write_to_file_command = f" >> {output_file}"
    call(cd_command + " && " + git_log_command + write_to_file_command, shell=True)


class ChangedFile:
    def __init__(self, old_blob, cur_blob, status, file_name):
        self.old_blob = old_blob
        self.cur_blob = cur_blob
        self.status = status
        self.file_name = file_name

    def __str__(self):
        return f"{self.status}; {self.file_name}; {self.old_blob}; {self.cur_blob}"


def parse_diff_tree_command(old_commit: str, cur_commit: str, git_dir: str) -> List[ChangedFile]:
    tmp_file = os.path.join(git_dir, "tmp")
    call(f"cd {git_dir} && git diff-tree -r -M {old_commit} {cur_commit} > {tmp_file}", shell=True)

    result = []
    with open(tmp_file, 'r') as file:
        for line in file:
            line_list = line.split()
            old_blob, cur_blob, status, file_name = line_list[2], line_list[3], line_list[4], line_list[5]
            result.append(ChangedFile(old_blob, cur_blob, status, file_name))

    return result


def download_blob_content(blob_hash: str, blobs_dir: str, git_dir: str):
    if not os.path.exists(blobs_dir):
        os.mkdir(blobs_dir)

    if blob_hash != "0000000000000000000000000000000000000000":
        blob_file_path = os.path.join(blobs_dir, blob_hash)
        call(f"cd {git_dir} && git cat-file -p {blob_hash} > {blob_file_path}", shell=True)


def create_full_log_file_and_download_blobs(com_com_log: str, full_log: str, blobs_dir: str, git_dir: str):
    with open(full_log, 'w') as full_log_file:
        full_log_file.write("commit_hash; author; status; file; old_blob; new_blob; message;\n")

        with open(com_com_log, 'r') as com_com_log_file:
            for line in com_com_log_file:
                if line.startswith("parent_commit_file_hash"):  # csv title # заменить на проверку приведения к числу
                    continue
                line_list = line.split(";")
                parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[2], line_list[3]
                changed_files = parse_diff_tree_command(parent_commit, cur_commit, git_dir)

                for changed_file in changed_files:
                    # write to log
                    full_log_file.write(f"{cur_commit}; {author}; {changed_file}; {message};\n")

                    # download both blob files
                    download_blob_content(changed_file.old_blob, blobs_dir, git_dir)
                    download_blob_content(changed_file.cur_blob, blobs_dir, git_dir)


if __name__ == "__main__":
    # values
    http = "https://github.com/natalymr/interpreter.git"
    # http = "https://github.com/natalymr/spbau_java_hw.git"
    http = "https://git.jetbrains.team/aurora.git"
    is_cloned = False
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "interpreter"
    # git_dir_name = "spbau_java_hw"
    git_dir = os.path.join(parent_dir, git_dir_name)
    start_date = "2017-01-01"
    end_date = "2019-07-01"
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    full_log_file = f"gcm_{git_dir_name}_full.log"
    full_log_file = os.path.join(parent_dir, full_log_file)
    blobs_dir = os.path.join(parent_dir, "blobs")

    # logic
    if not is_cloned:
        git_clone(http, parent_dir)

    create_com_com_log_file(git_dir, start_date, end_date, com_com_log_file)
    create_full_log_file_and_download_blobs(com_com_log_file, full_log_file, blobs_dir, git_dir)
