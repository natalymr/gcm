from code2seq_dataset.common import clean_function_body_from_new_line_characters, get_blobs_positions
from code2seq_dataset.common import split_commit_message, compare_two_blobs
from code2seq_dataset.info_classes import FunctionInfo, FullLogLine, BlobInfo, dataset_line
import collections
import numpy as np
from operator import itemgetter
from pathlib import Path
import pickle
import time
from typing import Dict, List, Tuple, Set, TextIO, DefaultDict


PAD: str = '<PAD>'
padded_path: str = "{},{},{}".format(PAD, PAD, PAD)


def pad_paths_per_function(paths: Set[str], paths_max_number: int) -> List[str]:
    global padded_path
    size: int = len(paths)

    if size <= paths_max_number:
        result: List[str] = list(paths)
        for _ in range(paths_max_number - size):
            result.append(padded_path)
    else:
        result: List[str] = list(np.random.choice(list(paths), paths_max_number, replace=False))

    return result


def pad_paths_per_commit(paths_max_number: int, functions_to_pad: int) -> List[str]:
    global padded_path
    return [padded_path for _ in range(paths_max_number * functions_to_pad)]


def get_all_diff_paths(changed_functions: List[Tuple[FunctionInfo, FunctionInfo]], paths_max_number: int) -> List[str]:
    all_functions_diff_paths: List[str] = []

    for function, other_function in changed_functions:
        diff_paths: Set[str] = function.path_difference(other_function)
        diff_paths = clean_function_body_from_new_line_characters(diff_paths)
        diff_paths: List[str] = pad_paths_per_function(diff_paths, paths_max_number)
        all_functions_diff_paths.extend(diff_paths)

    return all_functions_diff_paths


def write_commit_message_and_all_changed_functions(message: str,
                                                   changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]],
                                                   max_functions_count_per_commit: int,
                                                   file_role: str,
                                                   output_file: TextIO):
    paths_max_number = 1000 if file_role == "train" else 200
    actual_function_count: int = len(changed_functions)
    changed_functions: List[Tuple[FunctionInfo, FunctionInfo]] = list(changed_functions)

    if actual_function_count <= max_functions_count_per_commit:
        all_functions_paths: List[str] = get_all_diff_paths(changed_functions, paths_max_number)
        all_functions_paths.extend(pad_paths_per_commit(paths_max_number,
                                                        max_functions_count_per_commit - actual_function_count))
    else:
        ind = np.random.choice(len(changed_functions), max_functions_count_per_commit, replace=False)
        changed_functions = list(itemgetter(*ind)(changed_functions))
        all_functions_paths: List[str] = get_all_diff_paths(changed_functions, paths_max_number)

    message: List[str] = split_commit_message(message)
    output_file.write(dataset_line.substitute(target_message='|'.join(message),
                                              paths=' '.join(all_functions_paths)))


def get_commit_vs_blobs(full_log: Path) -> DefaultDict[str, List[FullLogLine]]:
    commit_vs_blobs: DefaultDict[str, List[FullLogLine]] = collections.defaultdict(list)

    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            if line.startswith("commit_hash"):
                continue

            full_log_line = FullLogLine.\
                parse_from_line(line)
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
        splitted_dataset: Dict[str, Set[str]] = pickle.load(sdf)

    time_1 = time.time()
    blobs_positions: Dict[str, List[Tuple[int, int]]] = get_blobs_positions(data)
    time_2 = time.time()
    print(f"Finish parsing file with paths. Time: {time_2 - time_1}")
    commit_vs_blobs: Dict[str, List[FullLogLine]] = get_commit_vs_blobs(full_log)
    time_3 = time.time()
    print(f"Finish parsing full log. Time: {time_3 - time_2}")

    i = 0
    len_changed_functions: List[int] = []
    with open(train, 'w') as train_f, open(test, 'w') as test_f, open(val, 'w') as val_f, open(data, 'rb') as data_f:
        for commit, changed_files in commit_vs_blobs.items():
            i += 1
            if i % 100 == 0:
                print(f"At {i}, mean = {np.mean(len_changed_functions)}, median = {np.median(len_changed_functions)}")

            if commit in splitted_dataset['train']:
                file = train_f
                file_role = "train"
            elif commit in splitted_dataset['test']:
                file = test_f
                file_role = "test"
            elif commit in splitted_dataset['val']:
                file = val_f
                file_role = "val"
            else:
                continue

            changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()
            for changed_file in changed_files:
                changed_functions |= compare_two_blobs(BlobInfo(changed_file.old_blob,
                                                                blobs_positions[changed_file.old_blob]),
                                                       BlobInfo(changed_file.new_blob,
                                                                blobs_positions[changed_file.new_blob]),
                                                       data_f)
            if len(changed_functions) > 0:
                # print(f"Commit: {commit}, size changed_functions = {len(changed_functions)}")
                # print("{}".format('\n'.join([f.function_name for f, o_f in changed_functions])))

                len_changed_functions.append(len(changed_functions))

                message = commit_vs_blobs[commit][0].message
                write_commit_message_and_all_changed_functions(message, changed_functions,
                                                               max_functions_count_per_commit,
                                                               file_role,
                                                               file)


def main():
    dataset = "aurora"
    all_paths_file: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.raw.txt")
    train_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.train.raw.txt")
    test_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.test.raw.txt")
    val_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.val.raw.txt")
    datasets_parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")

    full_log_file = datasets_parent_dir.joinpath(f"gcm_{dataset}_full.log")
    splitted_commits: Path = datasets_parent_dir.joinpath(f"aurora_splitted_commits_set_train_val_test.pickle")

    replace_target_with_message(all_paths_file,
                                full_log_file,
                                train_data_path, test_data_path, val_data_path,
                                splitted_commits,
                                8)


if __name__ == '__main__':
    main()
