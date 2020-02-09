import collections
import json

import numpy as np
from operator import itemgetter
from pathlib import Path
import pickle
from typing import Dict, List, Tuple, Set, TextIO, DefaultDict

from code2seq_dataset.common import clean_function_body_from_new_line_characters, get_blobs_positions
from code2seq_dataset.common import split_commit_message, compare_two_blobs
from code2seq_dataset.info_classes import FunctionInfo, FullLogLine, BlobPositions, DatasetPart
from code2seq_dataset.global_vars import dataset_line, padded_path, Blob, Code2SeqPath, Message, Commit, SEPARATOR
from common_dataset.diffs import CommitDiff
from common_dataset.logs import COMMON_SEP


def cut_paths_per_function(paths: Set[Code2SeqPath], paths_max_number: int) -> List[Code2SeqPath]:
    lp: List[Code2SeqPath] = list(paths)
    return lp if len(paths) <= paths_max_number else list(np.random.choice(lp, paths_max_number, replace=False))


def pad_paths_per_commit(paths_to_pad: int) -> List[Code2SeqPath]:
    return [padded_path for _ in range(paths_to_pad)]


def get_all_diff_paths(changed_functions: List[Tuple[FunctionInfo, FunctionInfo]],
                       paths_max_number: int) -> List[Code2SeqPath]:

    all_functions_diff_paths: List[Code2SeqPath] = []

    for function, other_function in changed_functions:
        diff_paths: Set[Code2SeqPath] = function.path_difference(other_function)
        diff_paths = clean_function_body_from_new_line_characters(diff_paths)
        diff_paths: List[Code2SeqPath] = cut_paths_per_function(diff_paths, paths_max_number)
        all_functions_diff_paths.extend(diff_paths)

    return all_functions_diff_paths


def write_commit_message_and_all_changed_functions(message: Message,
                                                   changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]],
                                                   max_functions_count_per_commit: int,
                                                   output_file: TextIO) -> bool:
    paths_max_number: int = 200
    max_paths_per_commit: int = paths_max_number * max_functions_count_per_commit
    actual_function_count: int = len(changed_functions)
    changed_functions: List[Tuple[FunctionInfo, FunctionInfo]] = list(changed_functions)

    if actual_function_count > max_functions_count_per_commit:
        ind = np.random.choice(len(changed_functions), max_functions_count_per_commit, replace=False)
        changed_functions = list(itemgetter(*ind)(changed_functions))

    all_functions_paths: List[str] = get_all_diff_paths(changed_functions, paths_max_number)
    all_functions_paths.extend(pad_paths_per_commit(max_paths_per_commit - len(all_functions_paths)))

    splitted_message: List[str] = split_commit_message(message)
    if splitted_message:
        output_file.write(dataset_line.substitute(target_message='|'.join(splitted_message),
                                                  paths=' '.join(all_functions_paths)))
        return True
    return False


def get_commit_vs_blobs(full_log: Path, sep: str = SEPARATOR) -> Dict[Commit, List[FullLogLine]]:
    commit_vs_blobs: DefaultDict[Commit, List[FullLogLine]] = collections.defaultdict(list)

    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            if line.startswith("commit_hash"):
                continue

            full_log_line = FullLogLine.parse_from_line(line, separator=sep)
            if full_log_line.message != "no message":
                commit_vs_blobs[full_log_line.commit].append(full_log_line)

    return commit_vs_blobs


def replace_target_with_message(data: Path,
                                full_log: Path,
                                train: Path, test: Path, val: Path,
                                splitted_dataset_file: Path,
                                max_functions_count_per_commit: int):
    print(data)
    with open(splitted_dataset_file, 'rb') as sdf:
        splitted_dataset: Dict[DatasetPart, Set[Commit]] = pickle.load(sdf)
    print(f"train: {len(splitted_dataset[DatasetPart.TRAIN])}, "
          f"test: {len(splitted_dataset[DatasetPart.TEST])}, "
          f"val: {len(splitted_dataset[DatasetPart.VAL])}")

    blobs_positions: Dict[Blob, List[Tuple[int, int]]] = get_blobs_positions(data)

    commit_vs_blobs: Dict[Commit, List[FullLogLine]] = get_commit_vs_blobs(full_log)

    i = 0
    tr, te, v, contin, z = 0, 0, 0, 0, 0
    len_changed_functions: List[int] = []
    with open(train, 'w') as train_f, open(test, 'w') as test_f, open(val, 'w') as val_f, open(data, 'rb') as data_f:
        for commit, changed_files in commit_vs_blobs.items():
            i += 1
            if i % 100 == 0:
                print(f"At {i}, mean = {np.mean(len_changed_functions)}, "
                      f"median = {np.median(len_changed_functions)}\n"
                      f"60 percentile = {np.percentile(np.array(len_changed_functions), 60)}\n"
                      f"70 percentile = {np.percentile(np.array(len_changed_functions), 70)}\n"
                      f"80 percentile = {np.percentile(np.array(len_changed_functions), 80)}\n"
                      f"90 percentile = {np.percentile(np.array(len_changed_functions), 90)}")

            if commit in splitted_dataset[DatasetPart.TRAIN]:
                file = train_f
                tr += 1
            elif commit in splitted_dataset[DatasetPart.TEST]:
                file = test_f
                te += 1
            elif commit in splitted_dataset[DatasetPart.VAL]:
                file = val_f
                v += 1
            else:
                contin += 1
                continue

            changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()
            for changed_file in changed_files:
                changed_functions |= compare_two_blobs(BlobPositions(changed_file.old_blob,
                                                                     blobs_positions[changed_file.old_blob]),
                                                       BlobPositions(changed_file.new_blob,
                                                                     blobs_positions[changed_file.new_blob]),
                                                       data_f)
            if len(changed_functions) > 0:
                z += 1
                len_changed_functions.append(len(changed_functions))

                message = Message(commit_vs_blobs[commit][0].message)
                write_commit_message_and_all_changed_functions(message, changed_functions,
                                                               max_functions_count_per_commit,
                                                               file)
    print(f"50 percentile: {np.percentile(np.array(len_changed_functions), 50)}")
    print(f"60 percentile: {np.percentile(np.array(len_changed_functions), 60)}")
    print(f"70 percentile: {np.percentile(np.array(len_changed_functions), 70)}")
    print(f"80 percentile: {np.percentile(np.array(len_changed_functions), 80)}")
    print(f"90 percentile: {np.percentile(np.array(len_changed_functions), 90)}")
    print(f"95 percentile: {np.percentile(np.array(len_changed_functions), 95)}")
    print(f"train={tr}, test={te}, val={v}, continue {contin}, nnz = {z}")
    print(f"number of all commits = {len(commit_vs_blobs.keys())}")


def get_commits_with_exact_number_of_changed_functions(data: Path, full_log: Path, output: Path,
                                                       is_filtered: bool = False, filtered_json: Path = None):
    blobs_positions: Dict[Blob, List[Tuple[int, int]]] = get_blobs_positions(data)
    commit_vs_blobs: Dict[Commit, List[FullLogLine]] = get_commit_vs_blobs(full_log, sep=COMMON_SEP)
    if is_filtered:
        with open(filtered_json, 'r') as f:
            filtered_commits_json = json.load(f)
        filtered_commits_messages: Dict[Commit, Message] = {}
        filtered_commits: Set[Commit] = set()
        for raw_commit in filtered_commits_json:
            parsed_commit: CommitDiff = CommitDiff.from_dict(raw_commit)
            filtered_commits_messages[parsed_commit.commit] = parsed_commit.message
            filtered_commits.add(parsed_commit.commit)
    print("finished parsing")

    i = 0
    with open(data, 'rb') as data_f:
        for commit, changed_files in commit_vs_blobs.items():
            if is_filtered:
                if commit not in filtered_commits:
                    continue
            i += 1
            if i % 100 == 0:
                print(f"At {i}")

            changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()
            for changed_file in changed_files:
                changed_functions |= compare_two_blobs(BlobPositions(changed_file.old_blob,
                                                                     blobs_positions[changed_file.old_blob]),
                                                       BlobPositions(changed_file.new_blob,
                                                                     blobs_positions[changed_file.new_blob]),
                                                       data_f)
            changed_functions_number: int = len(changed_functions)
            # print(changed_functions_number)

            if 1 <= changed_functions_number <= 4:
                # print('here')
                output_file: Path = output / f'{changed_functions_number}.txt'
                message = filtered_commits_messages[commit]
                with open(output_file, 'a+') as file:
                    write_commit_message_and_all_changed_functions(message, changed_functions,
                                                                   changed_functions_number,
                                                                   file)
                common_file: Path = output / '1234.txt'
                with open(common_file, 'a+') as file:
                    write_commit_message_and_all_changed_functions(message, changed_functions,
                                                                   4,
                                                                   file)


def main():
    dataset = 'intellij'
    all_paths_file: Path = Path(f"/Users/natalia.murycheva/Documents/code2seq/filtered_intellij.train.raw.txt")
    train_data_path: Path = Path(f"/Users/natalia.murycheva/Documents/code2seq/{dataset}.train.raw.txt")
    test_data_path: Path = Path(f"/Users/natalia.murycheva/Documents/code2seq/{dataset}.test.raw.txt")
    val_data_path: Path = Path(f"/Users/natalia.murycheva/Documents/code2seq/{dataset}.val.raw.txt")
    datasets_parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")

    full_log_file = datasets_parent_dir.joinpath(f"gcm_{dataset}_full.log")
    splitted_commits: Path = datasets_parent_dir.joinpath(f"{dataset}_splitted_commits_set_train_val_test.pickle")

    # replace_target_with_message(all_paths_file,
    #                             full_log_file,
    #                             train_data_path, test_data_path, val_data_path,
    #                             splitted_commits,
    #                             4)

    full_log_file: Path = Path.cwd().parent.parent.joinpath('data')\
        .joinpath('raw_data').joinpath(dataset).joinpath('changed_java_files.log')
    filtered_json: Path = Path.cwd().parent.parent.joinpath('data')\
        .joinpath('processed_data').joinpath(dataset).joinpath('diff_filtered.json')
    get_commits_with_exact_number_of_changed_functions(all_paths_file,
                                                       full_log_file,
                                                       Path('/Users/natalia.murycheva/PycharmProjects/data/'
                                                            f'processed_data/intellij/c2s'),
                                                       True,
                                                       filtered_json)


if __name__ == '__main__':
    main()
