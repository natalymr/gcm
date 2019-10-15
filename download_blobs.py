import os
from subprocess import call
from typing import Tuple


SEPARATOR = "THIS_STRING_WILL_NEVER_APPEAR_IN_DATASET_AND_IT_WILL_BE_USED_AS_SEPARATOR"


def download_blob_content(blob_hash: str, blobs_dir: str, git_dir: str):
    if not os.path.exists(blobs_dir):
        os.mkdir(blobs_dir)
    if blob_hash != "0000000000000000000000000000000000000000":
        blob_file_path = os.path.join(blobs_dir, blob_hash)
        call(f"cd {git_dir} && git cat-file -p {blob_hash} > {blob_file_path}", shell=True)


def download_several_blobs(full_log: str, lines_range: Tuple[int, int], blobs_dir: str, git_dir: str):
    start_line = lines_range[0]
    end_line = lines_range[1]
    print(f"start line: {start_line}, end_line: {end_line}")
    with open(full_log, 'r') as full_log_file:
        i = 0
        for i in range(start_line):
            full_log_file.readline()
            i += 1
        for line in full_log_file:
            i += 1
            if start_line <= i and i <= end_line:
                if i % 20 == 0:
                    print(f"Start to process {i} file; ({start_line}, {end_line})")
                line_list = line.split(SEPARATOR)
                old_blob, cur_blob = line_list[4], line_list[5]
                all_blobs = os.listdir(blobs_dir)
                if old_blob not in all_blobs:
                    download_blob_content(old_blob, blobs_dir, git_dir)
                if cur_blob not in all_blobs:
                    download_blob_content(cur_blob, blobs_dir, git_dir)


if __name__ == "__main__":
    # values
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "dubbo"
    # git_dir = os.path.join(parent_dir, "packed_intellij")
    git_dir = os.path.join(parent_dir, git_dir_name)
    full_log_file = f"gcm_{git_dir_name}_full.log"
    full_log_file = os.path.join(parent_dir, full_log_file)
    blobs_dir = os.path.join(parent_dir, f"{git_dir_name}_blobs")

    number_of_process = 1
    changed_files = 26054
    indexes = [i for i in range(number_of_process)]
    each_process_lines_count = changed_files // number_of_process
    lines_ranges = [
        (i * each_process_lines_count + 1, (i + 1) * each_process_lines_count) for i in range(number_of_process)
    ]
    lines_ranges[-1] = (lines_ranges[-1][0], changed_files)

    download_several_blobs(full_log_file, lines_ranges[0], blobs_dir, git_dir)

