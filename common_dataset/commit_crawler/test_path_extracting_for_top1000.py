from pathlib import Path
from typing import Dict, List, Tuple, Set

from code2seq_dataset.common import get_blobs_positions
from code2seq_dataset.global_vars import Blob
from code2seq_dataset.process_top1000_dataset_rnn_case import get_repo_commit_vs_repo_blobs
from common_dataset.logs import COMMON_SEP


def test_all_blobs_was_extracted():
    parent_dir: Path = Path('../../../new_data/')
    common_log_changed_files: Path = parent_dir.joinpath('common_blobs.log')
    path_file: Path = parent_dir.joinpath('processed_data/c2s_paths/top1000_dataset_v2.train.raw.txt')
    repo_commit_vs_repo_blobs = get_repo_commit_vs_repo_blobs(common_log_changed_files, sep=COMMON_SEP)
    blobs_positions: Dict[Blob, List[Tuple[int, int]]] = get_blobs_positions(path_file)
    print('Finished parsing path file')

    failed_count: int = 0
    total_count = 0
    failed_blobs = parent_dir.joinpath('new_failed_blob.log')
    with open(failed_blobs, 'w') as ff:
        for commit, changed_files in repo_commit_vs_repo_blobs.items():
            for changed_file in changed_files:
                total_count += 2
                if changed_file.old_blob not in blobs_positions:
                    failed_count += 1
                    ff.write(f'{changed_file.old_blob}\n')
                if changed_file.new_blob not in blobs_positions:
                    failed_count += 1
                    ff.write(f'{changed_file.new_blob}\n')
    print(f'Total count {total_count} , count of fails: {failed_count}')


def failed_path_extracting_blobs_is_ok():
    parent_dir: Path = Path('../../../new_data/')
    failed_blobs = parent_dir.joinpath('new_failed_blob.log')
    parse_error_files: Path = Path('/Users/natalia.murycheva/Documents/code2seq/filesThatWasFailedToBeParsed.log')

    def get_parse_error_blobs(fpath: Path) -> List[str]:
        failed_blobs_: List[str] = []
        with open(fpath, 'r') as f:
            for line in f:
                if line.startswith('Number of'):
                    continue
                [path, blob_file] = line.rsplit('/', 1)
                blob_file = blob_file.replace('.java', '')
                failed_blobs_.append(blob_file)

        return failed_blobs_
    parse_error_blobs = get_parse_error_blobs(parse_error_files)

    def get_blob_hash_from_name(fpath: str) -> str:
        [repo_name, hash_] = fpath.rsplit('_', 1)
        return hash_

    total_parse_error: int = 0
    total_empty: int = 0
    total_zeros: int = 0
    total_fail: int = 0
    all_failed_blobs: List[str] = []
    with open(failed_blobs, 'r') as f:
        for blob_name in f:
            all_failed_blobs.append(blob_name)
    all_failed_blobs: Set[str] = set(all_failed_blobs)
    for blob_name in all_failed_blobs:
        blob_hash = get_blob_hash_from_name(blob_name).strip('\n')
        if blob_name in parse_error_blobs:
            total_parse_error += 1
        elif blob_hash == '0000000000000000000000000000000000000000':
            total_zeros += 1
        elif blob_hash == 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391':
            total_empty += 1
        else:
            total_fail += 1

    print(f'Total parse error: {total_parse_error}, Total zeros: {total_zeros}, '
          f'Total empties {total_empty}, Total Fail: {total_fail}')


if __name__ == '__main__':
    # test_all_blobs_was_extracted()
    failed_path_extracting_blobs_is_ok()