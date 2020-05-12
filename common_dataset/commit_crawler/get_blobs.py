import collections
import multiprocessing
import os
import json
import pickle

from tqdm import tqdm
from pathlib import Path
from subprocess import call
from typing import List, Mapping, Set, Dict

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
    output_file: Path = filtered_diff_dir.parent.joinpath('common_blobs_200.log')
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
    blob_file_name: Path = blobs_dir.joinpath(f'{repo_name}_{blob_hash}.java').absolute()
    if blob_hash != '0000000000000000000000000000000000000000':
        call(f'git cat-file -p {blob_hash} > {blob_file_name}',
             cwd=git_dir,
             shell=True)

    # return check_file_is_not_empty(blob_file_name)


def is_blob_downloaded(blob_hash: str, repo_name, blobs_dir, downloaded_blobs) -> bool:
    blob_file_name = f'{repo_name}_{blob_hash}.java'
    if blob_hash == '0000000000000000000000000000000000000000':
        return True
    return blob_file_name in downloaded_blobs


def do_we_need_to_clone_repo(full_log_lines, repo_name, blobs_dir, downloaded_blobs):
    for log_line in full_log_lines:
        if not is_blob_downloaded(log_line.old_blob, repo_name, blobs_dir, downloaded_blobs):
            return True
        if not is_blob_downloaded(log_line.new_blob, repo_name, blobs_dir, downloaded_blobs):
            return True


def download_blobs(dir_for_repos: Path, blobs_dir: Path, common_blobs_file: Path) -> None:
    repo_vs_full_log_lines: Mapping[str, List[FullLogLine]] = collections.defaultdict(list)
    total_blobs_count: int = 0
    with open(common_blobs_file, 'r') as common_blobs_f:
        for line in common_blobs_f:
            total_blobs_count += 2
            [repo_name, *full_line] = line.split(COMMON_SEP)
            repo_vs_full_log_lines[repo_name].append(FullLogLine.parse_from_line(COMMON_SEP.join(full_line),
                                                                                 COMMON_SEP))
    for repo_name in tqdm(repo_vs_full_log_lines.keys()):
        repo_name_for_clone = repo_name.replace('_', '/')
        if repo_name in repo_vs_full_log_lines:
            if do_we_need_to_clone_repo(repo_vs_full_log_lines[repo_name], repo_name, blobs_dir):
                pass
                # with LocalGitRepository(repo_name_for_clone, dir_for_repos) as git_dir:
                #     for log_line in repo_vs_full_log_lines[repo_name]:
                #         if not is_blob_downloaded(log_line.old_blob, repo_name, blobs_dir):
                #             download_blob_content_other_output_file_name(log_line.old_blob, repo_name, blobs_dir, git_dir)
                #         if not is_blob_downloaded(log_line.new_blob, repo_name, blobs_dir):
                #             download_blob_content_other_output_file_name(log_line.new_blob, repo_name, blobs_dir, git_dir)



def process_one_dir(repo_name_input):
    repo_name_input, download_blobs_files = repo_name_input
    blobs_dir: Path = Path('../../../new_data/raw_data/blobs_200')
    filtered_diff_dir: Path = Path('../../../new_data/processed_data/two_inputs_200')
    dir_for_repos = filtered_diff_dir.parent
    common_blobs_file: Path = filtered_diff_dir.parent.joinpath('common_blobs_200.log')
    full_log_lines: List[FullLogLine] = []
    with open(common_blobs_file, 'r') as common_blobs_f:
        for line in common_blobs_f:
            [repo_name, *full_line] = line.split(COMMON_SEP)
            if repo_name == repo_name_input:
                full_log_lines.append(FullLogLine.parse_from_line(COMMON_SEP.join(full_line), COMMON_SEP))

    repo_name_for_clone = repo_name_input.replace('_', '/')
    if repo_name_for_clone == 'aosp-mirror/platform/frameworks/base':
        repo_name_for_clone = 'aosp-mirror/platform_frameworks_base'
    if full_log_lines:
        with LocalGitRepository(repo_name_for_clone, dir_for_repos) as git_dir:
            for log_line in full_log_lines:
                if not is_blob_downloaded(log_line.old_blob, repo_name_input, blobs_dir, download_blobs_files):
                    download_blob_content_other_output_file_name(log_line.old_blob, repo_name_input, blobs_dir, git_dir)
                if not is_blob_downloaded(log_line.new_blob, repo_name_input, blobs_dir, download_blobs_files):
                    download_blob_content_other_output_file_name(log_line.new_blob, repo_name_input, blobs_dir, git_dir)


def download_blobs_parallel(common_blobs_file: Path) -> None:
    repo_vs_full_log_lines: Dict[str, List[FullLogLine]] = collections.defaultdict(list)
    total_blobs_count: int = 0
    with open(common_blobs_file, 'r') as common_blobs_f:
        for line in common_blobs_f:
            total_blobs_count += 2
            [repo_name, *full_line] = line.split(COMMON_SEP)
            repo_vs_full_log_lines[repo_name].append(FullLogLine.parse_from_line(COMMON_SEP.join(full_line),
                                                                                 COMMON_SEP))
    print(f'Total blobs count = {total_blobs_count}')
    print(f'We needed to download data for {len(repo_vs_full_log_lines)} repos, but we already have one part')
    blobs_dir = Path('../../../new_data/raw_data/blobs_200')
    repos_not_to_download = []
    downloaded_blobs_files = set(os.listdir(blobs_dir))
    for repo in tqdm(repo_vs_full_log_lines.keys()):
        if not do_we_need_to_clone_repo(repo_vs_full_log_lines[repo], repo, blobs_dir, downloaded_blobs_files):
            repos_not_to_download.append(repo)

    for del_repos in repos_not_to_download:
        del repo_vs_full_log_lines[del_repos]

    print(len(repo_vs_full_log_lines['aosp-mirror_platform_frameworks_base']))
    print(f'So now we need to download {len(repo_vs_full_log_lines)} repos')

    repos = repo_vs_full_log_lines.keys()
    repos = [(repo, downloaded_blobs_files) for repo in repos]
    for _ in tqdm(multiprocessing.Pool().imap_unordered(process_one_dir, repos), total=len(repos)):
        pass
    # # with multiprocessing.Pool() as pool:
    #     pool.map(process_one_dir, repos)


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


def check_downloaded_blobs(blobs_dir: Path, common_blobs_file: Path) -> None:
    repo_vs_full_log_lines: Mapping[str, List[FullLogLine]] = collections.defaultdict(list)
    total_blobs_count: int = 0
    with open(common_blobs_file, 'r') as common_blobs_f:
        for line in common_blobs_f:
            total_blobs_count += 2
            [repo_name, *full_line] = line.split(COMMON_SEP)
            repo_vs_full_log_lines[repo_name].append(FullLogLine.parse_from_line(COMMON_SEP.join(full_line),
                                                                                 COMMON_SEP))
            # if total_blobs_count > 17000:
            #     break

    all_downloaded_blobs = os.listdir(blobs_dir)
    all_needed_blobs = set()
    print(f'len all downloaded {len(all_downloaded_blobs)}')
    failed_repo_vs_count = collections.defaultdict(set)
    must_be_repo_vs_count = collections.defaultdict(set)
    list_blobs_hash = []
    repo_vs_blobs = collections.defaultdict(set)
    all_blobs_set = set()
    repos_with_collisions = 0
    collisions_blobs = []
    for repo_name in tqdm(repo_vs_full_log_lines.keys()):
        for changed_file in repo_vs_full_log_lines[repo_name]:
            if changed_file.old_blob != '0000000000000000000000000000000000000000':
                list_blobs_hash.append(changed_file.old_blob)
                repo_vs_blobs[repo_name].add(changed_file.old_blob)
                all_needed_blobs.add(f'{repo_name}_{changed_file.old_blob}.java')
            if changed_file.new_blob != '0000000000000000000000000000000000000000':
                list_blobs_hash.append(changed_file.new_blob)
                repo_vs_blobs[repo_name].add(changed_file.new_blob)
                all_needed_blobs.add(f'{repo_name}_{changed_file.new_blob}.java')
        if len(all_needed_blobs & repo_vs_blobs[repo_name]) != 0:
            repos_with_collisions += 1
            collisions_blobs.extend(all_needed_blobs & repo_vs_blobs[repo_name])


    print(f'Total blobs number = {total_blobs_count}')
    print(f'collisions in blobs hash list = {len(list_blobs_hash)}, set = {len(set(list_blobs_hash))}')
    print('collisions blobs')
    print(set(collisions_blobs))
    print(len(collisions_blobs))
    print(len(set(collisions_blobs)))
    print(f'repos with collisions number {repos_with_collisions}')

    sorted = collections.Counter(list_blobs_hash)
    i = 0
    for hash, count in sorted.items():
        if count > 2:
            # print(f'{hash} - {count}')
            i += 1

    print(f"with java  = {len([item for item in all_downloaded_blobs if item.endswith('.java')])}")
    print(f"not with java  = {len([item for item in all_downloaded_blobs if not item.endswith('.java')])}")
    not_with_java = [item for item in all_downloaded_blobs if not item.endswith('.java')]
    blob_hash_len = len('87601ba3a5911c5d38d426baa530e414d32cc027')
    for file_ in not_with_java:
        blob_hash = file_[-blob_hash_len:]
        if blob_hash in collisions_blobs:
            print(f'blob from collision')
        else:
            print(blob_hash)
    repo_name = [name[:-blob_hash_len] for name in not_with_java]

    print(list(set(all_downloaded_blobs) - all_needed_blobs)[:10])
    repos_names_that_bugs = [blob[:-len('87601ba3a5911c5d38d426baa530e414d32cc027')]
                             for blob in (set(all_downloaded_blobs) - all_needed_blobs)]
    print(set(repos_names_that_bugs))
    for repo in failed_repo_vs_count.keys():
        print(f'{repo} - in common {len(must_be_repo_vs_count[repo] & failed_repo_vs_count[repo])}'
              f' len must be {len(must_be_repo_vs_count[repo])}'
              f' len failed {len(failed_repo_vs_count[repo])}')


def get_downloaded_blobs_stat_collisions(blobs_dir: Path, common_blobs_file: Path) -> None:
    repo_vs_full_log_lines: Mapping[str, List[FullLogLine]] = collections.defaultdict(list)
    full_log_line_list = []
    total_blobs_count: int = 0
    with open(common_blobs_file, 'r') as common_blobs_f:
        for line in common_blobs_f:
            total_blobs_count += 2
            [repo_name, *full_line] = line.split(COMMON_SEP)
            full_log_line_list.append(COMMON_SEP.join(full_line))
            repo_vs_full_log_lines[repo_name].append(FullLogLine.parse_from_line(COMMON_SEP.join(full_line),
                                                                                 COMMON_SEP))

    common_blobs = set()
    sorted = collections.Counter(full_log_line_list)
    for line, count in sorted.items():
        if count > 1:
            # print(f'{count} - {line}')
            fll = FullLogLine.parse_from_line(line, COMMON_SEP)
            common_blobs.add(fll.old_blob)
            common_blobs.add(fll.new_blob)

    print(f'count of common blobs is {len(common_blobs)}')

    all_blobs_hashes = set()
    blobs_hashes_collisions = set()
    repo_vs_blobs_hashes = collections.defaultdict(set)
    for repo_name in tqdm(repo_vs_full_log_lines.keys()):
        for changed_file in repo_vs_full_log_lines[repo_name]:
            if changed_file.old_blob != '0000000000000000000000000000000000000000':
                repo_vs_blobs_hashes[repo_name].add(changed_file.old_blob)
            if changed_file.new_blob != '0000000000000000000000000000000000000000':
                repo_vs_blobs_hashes[repo_name].add(changed_file.new_blob)

        # check there is no collision for this repo
        possible_collisions = all_blobs_hashes & repo_vs_blobs_hashes[repo_name]
        if len(possible_collisions) != 0:
            blobs_hashes_collisions.update(possible_collisions)
        all_blobs_hashes.update(repo_vs_blobs_hashes[repo_name])

    print(f'Collisions number {len(blobs_hashes_collisions)}')
    print(blobs_hashes_collisions - common_blobs)

    print(f'Intersection = {len(blobs_hashes_collisions & common_blobs)}')
    print(list(blobs_hashes_collisions)[:10])
    print(f'all blobs hashes {len(all_blobs_hashes)}')
    # with open(common_blobs_file.parent.joinpath('blobs_collisions.pickle'), 'wb') as f:
    #     pickle.dump(blobs_hashes_collisions, f)
    all_downloaded_files = os.listdir(blobs_dir)
    blob_hash_len_with_java, len_java = len('e6a92d4554046b88461778b99dcce88040aeb6a7.java'), len('.java')
    for downloaded_file in all_downloaded_files:
        blob_hash = downloaded_file[-blob_hash_len_with_java:-len_java]
        if blob_hash in common_blobs:
            print(downloaded_file)



def rename_already_downloaded(blobs_dir: Path, common_blob_log: Path) -> None:
    repo_vs_full_l_lines: Mapping[str, List[FullLogLine]] = collections.defaultdict(list)
    blob_hash_vs_repo: Dict[str, str] = {}
    total_blobs_count: int = 0
    with open(common_blob_log, 'r') as common_blobs_f:
        for line in common_blobs_f:
            total_blobs_count += 2
            [repo_name, *full_line] = line.split(COMMON_SEP)
            log_line = FullLogLine.parse_from_line(COMMON_SEP.join(full_line), COMMON_SEP)
            repo_vs_full_l_lines[repo_name].append(log_line)
            blob_hash_vs_repo[log_line.old_blob] = repo_name
            blob_hash_vs_repo[log_line.new_blob] = repo_name


    with open(common_blob_log.parent.joinpath('blobs_collisions.pickle'), 'rb') as f:
        blobs_hashes_collisions = pickle.load(f)

    all_downloaded_blobs: List[str] = os.listdir(blobs_dir)
    blob_hash_len = len('e6a92d4554046b88461778b99dcce88040aeb6a7')
    blob_hash_len_with_java = len('e6a92d4554046b88461778b99dcce88040aeb6a7.java')
    i = 0
    for downloaded_file in tqdm(all_downloaded_blobs):
        if downloaded_file.endswith('.java'):
            blob_hash = downloaded_file[-blob_hash_len_with_java:-len('.java')]
        else:
            blob_hash = downloaded_file[-blob_hash_len:]


        if blob_hash == '048a922456c7502b508ad50e0ab1735af4aa1beb':
            print(downloaded_file)
            print(f'{blob_hash_vs_repo[blob_hash]}_{blob_hash}.java')
        if blob_hash_vs_repo[blob_hash] == 'kickstarter_android-oss':
            correct_file_name = f'{blob_hash_vs_repo[blob_hash]}_{blob_hash}.java'
            (blobs_dir / downloaded_file).rename(blobs_dir / correct_file_name)
        continue

        # если повторяющийся блоб, то надо будет сто пудово его перекачивать
        if blob_hash in blobs_hashes_collisions:
            (blobs_dir / downloaded_file).unlink()
        else:
            # как должен называться файл
            correct_file_name = f'{blob_hash_vs_repo[blob_hash]}_{blob_hash}.java'
            # если его не было, значит мы скачали новый, но неправильно его назвали
            if correct_file_name not in all_downloaded_blobs:
                pass
                # if downloaded_file.endswith('.java'):
                #     if downloaded_file != correct_file_name:
                #         # rename
                #         (blobs_dir / downloaded_file).rename(blobs_dir / correct_file_name)
                # else:
                #     if downloaded_file != correct_file_name[:-len('.java')]:
                #         # rename
                #         (blobs_dir / downloaded_file).rename(blobs_dir / correct_file_name)
            else:
                if downloaded_file != correct_file_name:
                    i += 1
                    # print(downloaded_file)
                    # (blobs_dir / downloaded_file).unlink()


    print(i)







if __name__ == '__main__':
    raw_data: Path = Path('../../../new_data/raw_data/')
    filtered_diff_dir: Path = Path('../../../new_data/processed_data/two_inputs_200')
    blobs_dir: Path = Path('../../../new_data/raw_data/blobs_200')
    repos_file: Path = filtered_diff_dir.parent.joinpath('repos.json')
    common_blobs_log: Path = filtered_diff_dir.parent.joinpath('common_blobs_200.log')
    empty_blobs_log: Path = filtered_diff_dir.parent.joinpath('empty_blobs.log')
    # double_download_some_empty_blobs(repos_file, empty_blobs_log, blobs_dir, filtered_diff_dir.parent)
    # collect_all_needed_blobs(filtered_diff_dir, raw_data)
    # download_blobs(filtered_diff_dir.parent, blobs_dir, common_blobs_log)

    download_blobs_parallel(common_blobs_log)
    # check_downloaded_blobs(blobs_dir, common_blobs_log)
    # get_downloaded_blobs_stat_collisions(blobs_dir, common_blobs_log)
    # rename_already_downloaded(blobs_dir, common_blobs_log)
