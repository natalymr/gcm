import json
import os
from pathlib import Path
from subprocess import call
from typing import Tuple, List, Set

from code2seq_dataset.global_vars import Commit
from code2seq_dataset.info_classes import FullLogLine
from common_dataset.diffs import CommitDiff
from common_dataset.logs import COMMON_SEP


def download_blob_content(blob_hash: str, blobs_dir: str, git_dir: str):
    if not os.path.exists(blobs_dir):
        os.mkdir(blobs_dir)
    if blob_hash != '0000000000000000000000000000000000000000':
        blob_file_path = os.path.join(blobs_dir, blob_hash)
        call(f'git cat-file -p {blob_hash} > {blob_file_path}',
             cwd=git_dir,
             shell=True)


def download_blobs_from_filtered_commits(changed_files_log: Path, lines_range: Tuple[int, int],
                                         filtered_commits_json: Path, blobs_dir: Path, git_dir: Path) -> None:
    start_line = lines_range[0]
    end_line = lines_range[1]
    print(f"start line: {start_line}, end_line: {end_line}")
    with open(filtered_commits_json, 'r') as f:
        commits = json.load(f)
    commits: List[CommitDiff] = [CommitDiff.from_dict(commit) for commit in commits]
    filtered_commits: Set[Commit] = {commit.commit for commit in commits}
    print(f'Number of filtered commits is {len(filtered_commits)}')
    with open(changed_files_log, 'r') as full_log_file:
        i = 0
        for i in range(start_line):
            full_log_file.readline()
            i += 1
        for line in full_log_file:
            i += 1
            if start_line <= i and i <= end_line:
                if i % 20 == 0:
                    print(f"Start to process {i} file; ({start_line}, {end_line})")
                full_log_line: FullLogLine = FullLogLine.parse_from_line(line, COMMON_SEP)
                if full_log_line.commit not in filtered_commits:
                    continue
                all_blobs = os.listdir(blobs_dir)
                if full_log_line.old_blob not in all_blobs:
                    download_blob_content(full_log_line.old_blob, blobs_dir, git_dir)
                if full_log_line.new_blob not in all_blobs:
                    download_blob_content(full_log_line.new_blob, blobs_dir, git_dir)


if __name__ == "__main__":
    git_dir_name: str = 'intellij'
    git_dir: Path = Path(f'/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/{git_dir_name}')
    output_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath('raw_data').joinpath(git_dir_name)
    if not output_dir.exists():
        output_dir.mkdir()

    changed_files_log: Path = output_dir.joinpath('changed_java_files.log')
    filtered_commits: Path = Path.cwd().parent.parent.joinpath('data').joinpath('processed_data').joinpath(git_dir_name).joinpath('diff_filtered.json')
    blobs_dir: Path = output_dir.joinpath('blobs')
    if not blobs_dir.exists():
        blobs_dir.mkdir()

    number_of_process = 4
    changed_files = 701344
    indexes = [i for i in range(number_of_process)]
    each_process_lines_count = changed_files // number_of_process
    lines_ranges = [
        (i * each_process_lines_count + 1, (i + 1) * each_process_lines_count) for i in range(number_of_process)
    ]
    lines_ranges[-1] = (lines_ranges[-1][0], changed_files)

    download_blobs_from_filtered_commits(changed_files_log, lines_ranges[0], filtered_commits, blobs_dir, git_dir)