from operator import itemgetter

import numpy as np
import pickle
from pathlib import Path
from random import shuffle
from typing import List, Set, TypeVar, Tuple

from code2seq_dataset.common import parse_dataset_line
from code2seq_dataset.global_vars import Commit, Message, Code2SeqPath, dataset_line
from code2seq_dataset.info_classes import FullLogLine, DatasetPart

DatasetUnit = TypeVar('DatasetUnit', Tuple[Message, Commit], Tuple[Message, List[Code2SeqPath]])
CommitExt = TypeVar('CommitExt', Commit, DatasetUnit)


def split_in_two_parts(input_list: List[CommitExt], part_size: float) -> (List[CommitExt], List[CommitExt]):
    size: int = len(input_list)
    first_part_size: int = int(size * part_size)

    return input_list[:first_part_size], input_list[first_part_size:]


def split_dataset(commits_for_train: Path, output: Path):
    with open(commits_for_train, 'rb') as cftr:
        needed_commits: Set[Commit] = pickle.load(cftr)
    needed_commits: List[Commit] = list(needed_commits)
    shuffle(needed_commits)

    # split dataset
    commits_train, commits_tmp = split_in_two_parts(needed_commits, 0.7)
    commits_val, commits_test = split_in_two_parts(commits_tmp, 0.5)

    print(f"train: {len(commits_train)}, test: {len(commits_test)}, val: {len(commits_val)}")

    splitted_commits = {DatasetPart.TRAIN: set(commits_train),
                        DatasetPart.TEST: set(commits_test),
                        DatasetPart.VAL: set(commits_val)}

    with open(output, 'wb') as output_file:
        pickle.dump(splitted_commits, output_file)


def is_messages_intersected(set_1: List[DatasetUnit], set_2: List[DatasetUnit]) -> bool:
    return 0 != len({message for message, _ in set_1} & {message for message, _ in set_2})


def fix_intersection(list_1: List[DatasetUnit], list_2: List[DatasetUnit]) -> (List[DatasetUnit], List[DatasetUnit]):
    messages_set_1: Set[Message] = {message for message, _ in list_1}
    messages_set_2: Set[Message] = {message for message, _ in list_2}
    new_list_1: List[DatasetUnit] = []
    new_list_2: List[DatasetUnit] = []

    new_list_1.extend(list_1)
    for message, smth in list_2:
        if message in messages_set_1 and message in messages_set_2:
            new_list_1.append((message, smth))
        else:
            new_list_2.append((message, smth))

    return new_list_1, new_list_2


def split_dataset_with_no_file_commits_for_train(full_log: Path, output: Path):
    """
    For camel dataset in com_log there is full history of camel repo.
    But for now I use only last 4000 commits
    only needed commits are in full_log.
    """

    commits: Set[Tuple[Message, Commit]] = set()
    with open(full_log, 'r') as f:
        for line in f:
            full_log_line: FullLogLine = FullLogLine.parse_from_line(line)
            commits.add((full_log_line.message, full_log_line.commit))
    commits: List[Tuple[Message, Commit]] = list(commits)
    print(f"Len of all commits = {len(commits)}")
    shuffle(commits)

    # split dataset
    commits_train, commits_tmp = split_in_two_parts(commits, 0.65)
    # wait while test-val messages won't be in train messages
    if is_messages_intersected(commits_train, commits_tmp):
        commits_train, commits_tmp = fix_intersection(commits_train, commits_tmp)

    print(f"All size = {len(commits)}. Train size = {len(commits_train)}.")
    print(f"But train should be {0.7 * len(commits)}")
    print(f"Part size is {len(commits_train) / len(commits)}")

    commits_val, commits_test = split_in_two_parts(commits_tmp, 0.5)

    print(f"train: {len(commits_train)}, test: {len(commits_test)}, val: {len(commits_val)}")

    splitted_commits = {DatasetPart.TRAIN: {commit for _, commit in commits_train},
                        DatasetPart.TEST: {commit for _, commit in commits_test},
                        DatasetPart.VAL: {commit for _, commit in commits_val}}

    with open(output, 'wb') as output_file:
        pickle.dump(splitted_commits, output_file)


def split_exact_changed_functions_number_per_commit_dataset(full_data: Path, train: Path, test: Path, val: Path):
    """
    This dataset has only one file, target-commit message and paths diff.
    So, it will be splitted in train, test and val by messages
    """

    data_to_split: List[Tuple[Message, List[Code2SeqPath]]] = []
    with open(full_data, 'r') as input_f:
        for line in input_f:
            data_to_split.append(parse_dataset_line(line))
            print(len(line.split(" ")))

    print(f"size {len(data_to_split)}")

    # split dataset
    commits_train, commits_tmp = split_in_two_parts(data_to_split, 0.65)
    if is_messages_intersected(commits_train, commits_tmp):
        commits_train, commits_tmp = fix_intersection(commits_train, commits_tmp)
    commits_val, commits_test = split_in_two_parts(commits_tmp, 0.5)

    paths_max_number: int = 200
    function_per_commit: int = 1

    with open(train, 'w') as f:
        for message, paths in commits_train:
            if len(paths) > paths_max_number * function_per_commit:
                ind = np.random.choice(len(paths),
                                       paths_max_number * function_per_commit,
                                       replace=False)
                paths = list(itemgetter(*ind)(paths))
            f.write(dataset_line.substitute(target_message=message, paths=" ".join(paths)))

    with open(test, 'w') as f:
        for message, paths in commits_test:
            if len(paths) > paths_max_number * function_per_commit:
                ind = np.random.choice(len(paths),
                                       paths_max_number * function_per_commit,
                                       replace=False)
                paths = list(itemgetter(*ind)(paths))
            f.write(dataset_line.substitute(target_message=message, paths=" ".join(paths)))

    with open(val, 'w') as f:
        for message, paths in commits_val:
            if len(paths) > paths_max_number * function_per_commit:
                ind = np.random.choice(len(paths),
                                       paths_max_number * function_per_commit,
                                       replace=False)
                paths = list(itemgetter(*ind)(paths))
            f.write(dataset_line.substitute(target_message=message, paths=" ".join(paths)))


if __name__ == "__main__":
    dataset = "dubbo"
    parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")

    full_log_file = parent_dir.joinpath(f"gcm_{dataset}_full.log")
    needed_commits_pickle_file: Path = parent_dir.joinpath(f"{dataset}_commits_for_train.pickle")
    splitted_commits_file: Path = parent_dir.joinpath(f"{dataset}_splitted_commits_set_train_val_test.pickle")

    split_dataset_with_no_file_commits_for_train(full_log_file, splitted_commits_file)
    # split_dataset(needed_commits_pickle_file, splitted_commits_file)

    # split_exact_changed_functions_number_per_commit_dataset(
    #     full_data=Path("/Users/natalia.murycheva/Documents/code2seq/for_data/1.txt"),
    #     train=Path("/Users/natalia.murycheva/Documents/code2seq/camel.1.train.raw.txt"),
    #     test=Path("/Users/natalia.murycheva/Documents/code2seq/camel.1.test.raw.txt"),
    #     val=Path("/Users/natalia.murycheva/Documents/code2seq/camel.1.val.raw.txt")
    # )
