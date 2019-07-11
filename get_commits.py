import os
from subprocess import call, check_output
from typing import List, Tuple
import multiprocessing as mp


def git_clone(http: str, parent_dir: str):
    print("go to storage_dir & start to clone")
    call(f"cd {parent_dir} && git clone {http}", shell=True)


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
    print("Start to create com_com_log file")
    # logic
    call(f'echo "parent_commit_file_hash; current_commit_file_hash; message; author; date;" > {com_com_log}', shell=True)
    cd_command = f"cd {git_dir}"
    git_log_command = f'git log --pretty="%P;%H;%s;%an;%cd;" --since={start_date} --before={end_date} ' \
        f'--branches --all --no-merges'
    write_to_file_command = f" >> {com_com_log}"
    call(cd_command + " && " + git_log_command + write_to_file_command, shell=True)
    # check that we've got all commits
    total_count_expected = parse_shortlog_command(git_dir)
    total_count_actual = check_output(f"wc -l {com_com_log}".split()).decode().split()[0]
    print(total_count_actual)
    total_count_actual = int(total_count_actual) - 1  # because of header, one line
    if total_count_actual == total_count_expected:
        print("Everything is fine! Got all commits")
    else:
        print(f"Expected commits count \t{total_count_expected}")
        print(f"Actual commits count \t{total_count_actual}")
    print("Finished to create com_com_log file")
    return total_count_actual


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
    return result


def download_blob_content(blob_hash: str, blobs_dir: str, git_dir: str):
    if not os.path.exists(blobs_dir):
        os.mkdir(blobs_dir)
    if blob_hash != "0000000000000000000000000000000000000000":
        blob_file_path = os.path.join(blobs_dir, blob_hash)
        call(f"cd {git_dir} && git cat-file -p {blob_hash} > {blob_file_path}", shell=True)


def create_full_log_file_and_download_blobs(com_com_log: str, full_log: str, blobs_dir: str, git_dir: str):
    print("Start to create full_log file")
    with open(full_log, 'w') as full_log_file:
        full_log_file.write("commit_hash; author; status; file; old_blob; new_blob; message;\n")
        with open(com_com_log, 'r') as com_com_log_file:
            i = 0
            for line in com_com_log_file:
                i += 1
                if i % 20 == 0:
                    print(f"Start to process {i} commit")
                if line.startswith("parent_commit_file_hash"):  # csv title # заменить на проверку приведения к числу
                    continue
                line_list = line.split(";")
                parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[2], line_list[3]
                changed_files = parse_diff_tree_command(parent_commit, cur_commit, full_log, git_dir)
                for changed_file in changed_files:
                    # write to log
                    full_log_file.write(f"{cur_commit}; {author}; {changed_file}; {message};\n")
                    # download both blob files
                    all_blobs = os.listdir(blobs_dir)
                    if changed_file.old_blob not in all_blobs:
                        download_blob_content(changed_file.old_blob, blobs_dir, git_dir)
                    if changed_file.cur_blob not in all_blobs:
                        download_blob_content(changed_file.cur_blob, blobs_dir, git_dir)
    print("Finished to create full_log file")


def create_full_log_file_and_download_blobs_parallel(com_com_log: str, full_log: str, blobs_dir: str,
                                                     lines_range: (int, int), git_dir: str):
    start_line = lines_range[0]
    end_line = lines_range[1]
    with open(full_log, 'w') as full_log_file:
        full_log_file.write("commit_hash; author; status; file; old_blob; new_blob; message;\n")
        with open(com_com_log, 'r') as com_com_log_file:
            i = 0
            for i in range(start_line):
                com_com_log_file.readline()
                i += 1
            for line in com_com_log_file:
                i += 1
                if start_line <= i and i <= end_line:
                    if i == 1:  # csv title # заменить на проверку приведения к числу
                        continue
                    if i % 20 == 0:
                        print(f"Start to process {i} commit; ({start_line}, {end_line})")
                    line_list = line.split(";")
                    parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[2], line_list[3]
                    changed_files = parse_diff_tree_command(parent_commit, cur_commit, str(start_line), git_dir)
                    for changed_file in changed_files:
                        # write to log
                        full_log_file.write(f"{cur_commit}; {author}; {changed_file}; {message};\n")
                        # download both blob files
                        all_blobs = os.listdir(blobs_dir)
                        if changed_file.old_blob not in all_blobs:
                            download_blob_content(changed_file.old_blob, blobs_dir, git_dir)
                        if changed_file.cur_blob not in all_blobs:
                            download_blob_content(changed_file.cur_blob, blobs_dir, git_dir)


if __name__ == "__main__":
    # values
    # http = "https://github.com/natalymr/interpreter.git"
    http = "https://github.com/natalymr/spbau_java_hw.git"
    is_cloned = True
    # tmp_dir = "10"
    # tmp_dir = os.path.join(parent_dir, tmp_dir)
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "intellij"
    git_dir = os.path.join(parent_dir, git_dir_name)
    start_date = "2004-01-01"
    end_date = "2006-07-01"
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    full_log_file = f"gcm_{git_dir_name}_full.log"
    full_log_file = os.path.join(parent_dir, full_log_file)
    blobs_dir = os.path.join(parent_dir, f"{git_dir_name}_blobs")

    # logic
    if not is_cloned:
        git_clone(http, parent_dir)

    print("Number of processors: ", mp.cpu_count())
    processors_number = mp.cpu_count()

    commit_count = create_com_com_log_file(com_com_log_file, start_date, end_date, git_dir)
    # indexes = [i for i in range(processors_number)]
    #
    # each_process_lines_count = commit_count // mp.cpu_count()
    # lines_ranges = [(i * each_process_lines_count + 1, (i + 1) * each_process_lines_count) for i in indexes]
    # lines_ranges[-1] = (lines_ranges[-1][0], commit_count)
    #
    # full_log_files_names = [f"gcm_{git_dir_name}_full_{i}.log" for i in indexes]
    # full_log_files = [os.path.join(parent_dir, log) for log in full_log_files_names]
    # print(full_log_files)
    # print(lines_ranges)
    # print(f"len_ind {len(indexes)}, len_logs {len(full_log_files)}, len_lines {len(lines_ranges)} ")
    # print(f"len_ind {indexes[9:]}, len_logs {len(full_log_files[9:])}, len_lines {lines_ranges[9:]} ")
    #
    # pool = mp.Pool(7)
    # pool.starmap(create_full_log_file_and_download_blobs_parallel,
    #              [(com_com_log_file, full_log_files[i], blobs_dir, lines_ranges[i], git_dir) for i in indexes[9:]])
    #

    # create_full_log_file_and_download_blobs(com_com_log_file, full_log_file, blobs_dir, git_dir)


