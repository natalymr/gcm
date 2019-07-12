import os
from typing import Tuple
from get_commits import download_blob_content


def download_several_blobs(full_log: str, lines_range: Tuple[int, int], blobs_dir: str, git_dir: str):
    start_line = lines_range[0]
    end_line = lines_range[1]
    with open(full_log, 'r') as full_log_file:
        i = 0
        for i in range(start_line):
            full_log_file.readline()
            i += 1
        for line in full_log_file:
            i += 1
            if start_line <= i and i <= end_line:
                if i == 1:  # csv title # заменить на проверку приведения к числу
                    continue
                if i % 20 == 0:
                    print(f"Start to process {i} file; ({start_line}, {end_line})")
                line_list = line.split(";")
                old_blob, cur_blob = line_list[4], line_list[5]
                all_blobs = os.listdir(blobs_dir)
                if old_blob not in all_blobs:
                    download_blob_content(old_blob, blobs_dir, git_dir)
                if cur_blob not in all_blobs:
                    download_blob_content(cur_blob, blobs_dir, git_dir)


if __name__ == "__main__":
    # values
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "intellij"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    full_log_file = f"gcm_{git_dir_name}_full.log"
    full_log_file = os.path.join(parent_dir, full_log_file)
    blobs_dir = os.path.join(parent_dir, f"{git_dir_name}_blobs")

    number_of_process = 6
    changed_files = 89796
    indexes = [i for i in range(number_of_process)]
    each_process_lines_count = changed_files // number_of_process
    lines_ranges = [(i * each_process_lines_count + 1, (i + 1) * each_process_lines_count) for i in range(number_of_process)]
    lines_ranges[-1] = (lines_ranges[-1][0], changed_files)


    download_several_blobs(full_log_file, lines_ranges[0], blobs_dir, git_dir)

