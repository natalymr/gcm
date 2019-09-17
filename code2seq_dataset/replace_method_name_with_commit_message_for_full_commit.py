from pathlib import Path

from code2seq_dataset.common import clean_function_body_from_new_line_characters, get_blobs_positions
from code2seq_dataset.common import split_commit_message, compare_two_blobs
from code2seq_dataset.info_classes import FunctionInfo, FullLogLine, BlobInfo
import collections
import numpy as np
import os
import pickle
from typing import Dict, List, Tuple, Set, TextIO, DefaultDict, Mapping


def uniform_paths(paths: Set[str], paths_max_number: int) -> List[str]:
    size: int = len(paths)
    PAD: str = '<PAD>'
    padded_path: str = "{},{},{}".format(PAD, PAD, PAD)

    if size <= paths_max_number:
        result: List[str] = list(paths)
        for _ in range(paths_max_number - size):
            result.append(padded_path)
    else:
        result: List[str] = list(np.random.choice(list(paths), paths_max_number, replace=False))

    return result


def write_commit_message_and_all_changed_functions(message: str,
                                                   changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]],
                                                   file_role: str,
                                                   output_file: TextIO):
    message: List[str] = split_commit_message(message)
    all_functions_path: List[str] = []
    paths_max_number = 1000 if file_role == "train" else 200

    for function, other_function in changed_functions:
        diff_paths = function.path_difference(other_function)
        diff_paths = clean_function_body_from_new_line_characters(diff_paths)
        diff_paths = uniform_paths(diff_paths, paths_max_number)
        all_functions_path.extend(diff_paths)

    output_file.write(f"{'|'.join(message)} {' '.join(all_functions_path)}\n")


def get_commit_vs_blobs(full_log: Path) -> DefaultDict[str, List[FullLogLine]]:
    commit_vs_blobs: DefaultDict[str, List[FullLogLine]] = collections.defaultdict(list)

    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            if line.startswith("commit_hash"):
                continue

            full_log_line = FullLogLine.parse_from_line(line)
            commit_vs_blobs[full_log_line.commit].append(full_log_line)

    return commit_vs_blobs


def remove_method_name_with_commit_message_and_split_dataset(data: Path,
                                                             full_log: Path,
                                                             train: Path, test: Path, val: Path,
                                                             splitted_dataset_file: Path):
    print(data)
    with open(splitted_dataset_file, 'rb') as sdf:
        splitted_dataset: Dict[str, Set[str]] = pickle.load(sdf)

    blobs_positions: Dict[str, List[Tuple[int, int]]] = get_blobs_positions(data)
    print("Finish parsing file .all.")
    commit_vs_blobs: Dict[str, List[FullLogLine]] = get_commit_vs_blobs(full_log)

    i = 0
    len_changed_functions: List[int] = []
    with open(train, 'w') as train_f, open(test, 'w') as test_f, open(val, 'w') as val_f, open(data, 'rb') as data_f:
        for commit, changed_files in commit_vs_blobs.items():
            changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()
            i += 1
            if i % 20 == 0:
                print(f"At {i}")
                print(len_changed_functions)
            for changed_file in changed_files:
                changed_functions |= compare_two_blobs(BlobInfo(changed_file.old_blob, blobs_positions[changed_file.old_blob]),
                                                       BlobInfo(changed_file.new_blob, blobs_positions[changed_file.new_blob]),
                                                       data_f)
            if len(changed_functions) > 0:
                print(f"Size changed_functions = {len(changed_functions)}")
                if commit in splitted_dataset['train']:
                    file = train_f
                    file_role = "train"
                elif commit in splitted_dataset['test']:
                    file = test_f
                    file_role = "test"
                else:
                    file = val_f
                    file_role = "val"

                message = commit_vs_blobs[commit][0].message
                len_changed_functions.append(len(changed_functions))
                # write_commit_message_and_all_changed_functions(message,
                #                                                changed_functions,
                #                                                file_role,
                #                                                file)

    print(len_changed_functions)
    import numpy as np
    print(np.mean(len_changed_functions))
    print(np.median(len_changed_functions))


def main():
    print("here")
    dataset = "aurora"
    all_paths_file: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.raw.txt")
    train_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.train.raw.txt")
    test_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.test.raw.txt")
    val_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.val.raw.txt")
    datasets_parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")

    full_log_file = datasets_parent_dir.joinpath(f"gcm_{dataset}_full_log_for_train_commits.log")
    splitted_commits: Path = datasets_parent_dir.joinpath(f"aurora_splitted_commits_set_train_val_test.pickle")

    remove_method_name_with_commit_message_and_split_dataset(all_paths_file,
                                                             full_log_file,
                                                             train_data_path, test_data_path, val_data_path,
                                                             splitted_commits)


if __name__ == '__main__':
    main()
