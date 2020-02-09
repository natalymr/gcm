import collections
import os
import json
from tqdm import tqdm
from pathlib import Path
from subprocess import call
from typing import List, Mapping

from code2seq_dataset.global_vars import Commit, changed_files_log_line, Blob
from code2seq_dataset.info_classes import FullLogLine
from common_dataset.commit_crawler.get_logs_and_diffs import LocalGitRepository
from common_dataset.diffs import CommitDiff, get_commit_vs_blobs
from common_dataset.logs import COMMON_SEP


def get_commits_from_json(json_file: Path) -> List[CommitDiff]:
    with open(json_file, 'r') as f:
        commits = json.load(f)
    return [CommitDiff.from_dict(commit) for commit in commits]


def collect_all_needed_blobs(filtered_diffs_dir: Path, raw_dir: Path) -> List[str]:
    all_diffs_files: List[str] = os.listdir(filtered_diffs_dir)
    output_file: Path = filtered_diff_dir.parent.joinpath('common_blobs.log')
    with open(output_file, 'w') as output_f:
        for diff in all_diffs_files:
            # get filtered commits
            commits: List[CommitDiff] = get_commits_from_json(filtered_diff_dir / diff)

            # get blobs for all commits
            [name, *_] = diff.split('.filtered_diff')
            changed_file_log: Path = raw_dir.joinpath(f'{name}.changed_files.logs')
            commit_vs_blobs: Mapping[Commit, List[FullLogLine]] = get_commit_vs_blobs(changed_file_log, COMMON_SEP)

            # find needed blobs for all filtered commits
            for commit in commits:
                full_log_lines: List[FullLogLine] = commit_vs_blobs[commit.commit]
                for changed_file in commit.changed_java_files:
                    for log_file_line in full_log_lines:
                        if changed_file.file_name == log_file_line.file:
                            full_log_line: str = changed_files_log_line.substitute(commit_hash=log_file_line.commit,
                                                                                   author=log_file_line.author,
                                                                                   status=log_file_line.status,
                                                                                   file_name=log_file_line.file,
                                                                                   old_blob=log_file_line.old_blob,
                                                                                   new_blob=log_file_line.new_blob,
                                                                                   message=log_file_line.message,
                                                                                   sep=COMMON_SEP)
                            output_f.write(f'{name}{COMMON_SEP}{full_log_line}')


def check_file_is_not_empty(file_path: Path) -> bool:
    return os.path.getsize(file_path) != 0


def download_blob_content_other_output_file_name(blob_hash: str, repo_name: str, blobs_dir: Path, git_dir) -> bool:
    blob_file_name: Path = blobs_dir.joinpath(f'{repo_name}_{blob_hash}').absolute()
    if blob_hash != '0000000000000000000000000000000000000000':
        call(f'git cat-file -p {blob_hash} > {blob_file_name}',
             cwd=git_dir,
             shell=True)

    return check_file_is_not_empty(blob_file_name)


def download_blobs(dir_for_repos: Path, blobs_dir: Path, common_blobs_file: Path) -> None:
    repo_vs_full_log_lines: Mapping[str, List[FullLogLine]] = collections.defaultdict(list)
    total_blobs_count: int = 0
    with open(common_blobs_file, 'r') as common_blobs_f:
        for line in common_blobs_f:
            total_blobs_count += 2
            [repo_name, *full_line] = line.split(COMMON_SEP)
            repo_vs_full_log_lines[repo_name].append(FullLogLine.parse_from_line(COMMON_SEP.join(full_line),
                                                                                 COMMON_SEP))
    with tqdm(total=total_blobs_count) as pbar:
        for repo_name in repo_vs_full_log_lines.keys():
            repo_name_for_clone = repo_name.replace('_', '/')
            with LocalGitRepository(repo_name_for_clone, dir_for_repos) as git_dir:
                for log_line in repo_vs_full_log_lines[repo_name]:
                    download_blob_content_other_output_file_name(log_line.old_blob, repo_name, blobs_dir, git_dir)
                    download_blob_content_other_output_file_name(log_line.new_blob, repo_name, blobs_dir, git_dir)
                    pbar.update(2)


def double_download_some_empty_blobs(repos_file_json: Path, empty_blobs_file: Path,
                                     blobs_dir: Path, dir_for_repos: Path) -> None:

    with open(repos_file_json, 'r') as f:
        repos = json.load(f)
    repos_full_names: List[str] = [repo['full_name'] for repo in repos['items']][:1000]
    repos_full_names_vs_blobs: Mapping[str, List[Blob]] = collections.defaultdict(list)
    with open(empty_blobs_file, 'r') as empty_f:
        for line in empty_f:
            line = line.strip('\n')
            line.replace('.java', '')
            [repo_name, blob_hash] = line.rsplit('_', 1)
            repo_name = repo_name.replace('_', '/', 1)
            if repo_name not in repos_full_names:
                print(repo_name)
            else:
                repos_full_names_vs_blobs[repo_name].append(blob_hash)

    total_empty_blobs: int = 0
    for repo in repos_full_names_vs_blobs.keys():
        with LocalGitRepository(repo, dir_for_repos) as git_dir:
            for blob in repos_full_names_vs_blobs[repo]:
                blob = blob.replace('.java', '')
                appropriate_repo_name = repo.replace('/', '_')
                if not download_blob_content_other_output_file_name(blob, appropriate_repo_name, blobs_dir, git_dir):
                    total_empty_blobs += 1
                    print(f'Repo: {repo}, this blob is empty: {blob}')

    print(f'Really empty blobs is {total_empty_blobs}')


if __name__ == '__main__':
    raw_data: Path = Path('../../../new_data/raw_data/')
    filtered_diff_dir: Path = Path('../../../new_data/processed_data/')
    blobs_dir: Path = Path('../../../new_data/raw_data/blobs')
    repos_file: Path = filtered_diff_dir.parent.joinpath('repos.json')
    common_blobs_log: Path = filtered_diff_dir.parent.joinpath('common_blobs.log')
    empty_blobs_log: Path = filtered_diff_dir.parent.joinpath('emplty_blobs.log')
    double_download_some_empty_blobs(repos_file, empty_blobs_log, blobs_dir, filtered_diff_dir.parent)
    # collect_all_needed_blobs(filtered_diff_dir, raw_data)
    # download_blobs(filtered_diff_dir.parent, blobs_dir, common_blobs_log)
