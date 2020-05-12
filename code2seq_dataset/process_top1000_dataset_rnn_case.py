import collections
import numpy as np
from time import time
from pathlib import Path
from typing import Dict, List, Tuple, DefaultDict, Set

from tqdm import tqdm

from code2seq_dataset.common import get_blobs_positions, compare_two_blobs
from code2seq_dataset.global_vars import Blob, Commit, SEPARATOR, Message
from code2seq_dataset.info_classes import FullLogLine, FunctionInfo, BlobPositions
from code2seq_dataset.process_dataset_rnn_case import write_commit_message_and_all_changed_functions
from common_dataset.logs import COMMON_SEP


def get_repo_commit_vs_repo_blobs(full_log: Path, sep: str = SEPARATOR) -> Dict[Commit, List[FullLogLine]]:
    repo_commit_vs_repo_blobs: DefaultDict[Commit, List[FullLogLine]] = collections.defaultdict(list)

    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            [repo_name, *full_line] = line.split(COMMON_SEP)
            full_log_line = FullLogLine.parse_from_line(COMMON_SEP.join(full_line), separator=sep)
            full_log_line.old_blob = repo_name + '_' + full_log_line.old_blob
            full_log_line.new_blob = repo_name + '_' + full_log_line.new_blob
            repo_commit_vs_repo_blobs[repo_name + '_' + full_log_line.commit].append(full_log_line)

    return repo_commit_vs_repo_blobs


def replace_target_with_message(paths_file, common_log_file, output_dir):
    print('Start parsing paths file')
    a = time()
    blobs_positions: Dict[Blob, List[Tuple[int, int]]] = get_blobs_positions(paths_file)
    b = time()
    print('Finished parsing paths file')
    print(f'Number of blobs is {len(blobs_positions)}, Time {b - a}')
    repo_commit_vs_repo_blobs: Dict[Commit, List[FullLogLine]] = get_repo_commit_vs_repo_blobs(common_log_file,
                                                                                               sep=COMMON_SEP)
    output_file: Path = output_dir.joinpath('full_dataset.txt')
    output_log: Path = output_dir.joinpath('c2s_commits.log')
    len_changed_functions: List[int] = []
    i = 0
    with open(output_file, 'w') as out_f, open(output_log, 'w') as out_l, open(paths_file, 'rb') as paths_f:
        for commit, changed_files in tqdm(repo_commit_vs_repo_blobs.items()):
            i += 1
            if i % 1000 == 0:
                print(f"mean = {np.mean(len_changed_functions)}, "
                      f"median = {np.median(len_changed_functions)}\n"
                      f"60 percentile = {np.percentile(np.array(len_changed_functions), 60)}\n"
                      f"70 percentile = {np.percentile(np.array(len_changed_functions), 70)}\n"
                      f"80 percentile = {np.percentile(np.array(len_changed_functions), 80)}\n"
                      f"90 percentile = {np.percentile(np.array(len_changed_functions), 90)}")
            changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()
            for changed_file in changed_files:
                changed_functions |= compare_two_blobs(BlobPositions(changed_file.old_blob,
                                                                     blobs_positions[changed_file.old_blob]),
                                                       BlobPositions(changed_file.new_blob,
                                                                     blobs_positions[changed_file.new_blob]),
                                                       paths_f)
                # if '0000000000000000000000000000000000000000' in changed_file.new_blob or \
                #         '0000000000000000000000000000000000000000' in changed_file.old_blob:
                #     print(f'Commit: {commit}, #changed functions {len(changed_functions)}')

            len_changed_functions.append(len(changed_functions))

            if len(changed_functions) > 0:
                message = Message(repo_commit_vs_repo_blobs[commit][0].message)
                if write_commit_message_and_all_changed_functions(message, changed_functions, 4, out_f):
                    out_l.write(f'{commit}\n')


if __name__ == '__main__':
    process_data_dir: Path = Path('../../new_data/processed_data/')
    path_file: Path = process_data_dir.joinpath('c2s_paths/data/top1000_200_tokens/all_paths.txt')
    output_dir: Path = process_data_dir.joinpath('c2s_paths/data/top1000_200_tokens/top1000_200_tokens_400_context_size')
    common_log_file: Path = process_data_dir.joinpath('common_blobs_200.log')

    replace_target_with_message(path_file, common_log_file, output_dir)
