import json
from operator import itemgetter

import numpy as np
import pickle
from pathlib import Path
from random import shuffle
from typing import List, Set, TypeVar, Tuple

from code2seq_dataset.common import parse_dataset_line
from code2seq_dataset.global_vars import Commit, Message, Code2SeqPath, dataset_line
from code2seq_dataset.info_classes import FullLogLine, DatasetPart
from common_dataset.diffs import CommitDiff

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


def split_from_filtered_json(json_file: Path, output_file: Path):
    with open(json_file, 'r') as f:
        commits = json.load(f)
    commits: List[CommitDiff] = [CommitDiff.from_dict(commit) for commit in commits]

    def is_messages_sets_intersected(one: List[CommitDiff], other: List[CommitDiff]) -> bool:
        return 0 != len({c.message for c in one} & {c.message for c in other})

    def split(input_list: List[CommitDiff], part_size: float) -> (List[CommitDiff], List[CommitDiff]):
        size: int = len(input_list)
        first_part_size: int = int(size * part_size)
        return input_list[:first_part_size], input_list[first_part_size:]

    def fix_messages_sets_intersections(train_list: List[CommitDiff],
                                        test_list: List[CommitDiff]) -> (List[CommitDiff], List[CommitDiff]):
        new_train_list: List[CommitDiff] = []
        new_test_list: List[CommitDiff] = []
        train_messages_set: Set[Message] = {c.message for c in train_list}

        new_train_list.extend(train_list)
        for commit in test_list:
            if commit.message in train_messages_set:
                new_train_list.append(commit)
            else:
                new_test_list.append(commit)

        print(f'New part size is {len(new_train_list) / (len(new_train_list) + len(new_test_list))}')
        return new_train_list, new_test_list

    # COPY-PASTE
    print(f"Len of all commits = {len(commits)}")
    shuffle(commits)

    # split dataset
    commits_train, commits_tmp = split(commits, 0.7)
    # wait while test-val messages won't be in train messages
    if is_messages_sets_intersected(commits_train, commits_tmp):
        commits_train, commits_tmp = fix_messages_sets_intersections(commits_train, commits_tmp)

    print(f"All size = {len(commits)}. Train size = {len(commits_train)}.")
    print(f"But train should be (.6){0.6 * len(commits)}")
    print(f"But train should be (.7){0.7 * len(commits)}")
    print(f"Part size is {len(commits_train) / len(commits)}")

    commits_val, commits_test = split(commits_tmp, 0.5)

    print(f"train: {len(commits_train)}, test: {len(commits_test)}, val: {len(commits_val)}")

    splitted_commits = {'TRAIN': commits_train,
                        'TEST': commits_test,
                        'VAL': commits_val}

    with open(output_file, 'w') as output_file:
        output_file.write(json.dumps(splitted_commits, default=CommitDiff.to_json, indent=2))


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

    """
    In the case of intellij dataset we should do some message-content filtering.
    In other case just comment code below
    
    """

    def delete_key_words_in_message(message: Message, key_word: str) -> Message:
        raw_message = ' '.join(message.split('|'))
        cleaned_message = raw_message.replace(key_word, '')
        return Message('|'.join(cleaned_message.split(' ')))

    data_to_split = [(delete_key_words_in_message(message, 'scr <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'idea <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'idea cr <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'junit <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'ruby <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'web <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'cpp <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'dbe <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'py <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'wi <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'ux <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'ea <num>'), paths) for message, paths in data_to_split]
    data_to_split = [(delete_key_words_in_message(message, 'oc <num>'), paths) for message, paths in data_to_split]



    # split dataset
    commits_train, commits_tmp = split_in_two_parts(data_to_split, 0.65)
    if is_messages_intersected(commits_train, commits_tmp):
        commits_train, commits_tmp = fix_intersection(commits_train, commits_tmp)
    commits_val, commits_test = split_in_two_parts(commits_tmp, 0.5)

    paths_max_number: int = 200
    function_per_commit: int = 2
    print(f"train: {len(commits_train)}, test: {len(commits_test)}, val: {len(commits_val)}")

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


def split_dataset_when_only_paths_are_given(paths_file: Path, commits_log: Path, output_dir: Path) -> None:
    """
    This function split dataset into three parts: train, test and val
    :param paths_file: file, where each line is <target> <paths-diff>
    :param commits_log: file, where each line is repo_name_<commit_hash> which corresponds to line from paths_file
    :param output_dir: where train, test and val files will be created
    """
    commits: List[Commit] = []
    with open(commits_log, 'r') as commit_f:
        for line in commit_f:
            commits.append(Commit(line.strip('\n')))

    data_to_split: List[Tuple[Message, List[Code2SeqPath], Commit]] = []
    with open(paths_file, 'r') as input_f:
        for ind, line in enumerate(input_f):
            message, paths = parse_dataset_line(line)
            data_to_split.append((message, paths, commits[ind]))

    def split_list_in_two_parts(input_list, part_size: float):
        size: int = len(input_list)
        first_part_size: int = int(size * part_size)

        return input_list[:first_part_size], input_list[first_part_size:]

    def is_messages_intersected(set_1, set_2) -> bool:
        return 0 != len({message for message, _, _ in set_1} & {message for message, _, _ in set_2})

    def fix_intersection(list_1, list_2):
        messages_set_1: List[Message] = [message for message, _, _ in list_1]
        messages_set_2: List[Message] = [message for message, _, _ in list_2]
        new_list_1: List[Tuple[Message, List[Code2SeqPath], Commit]] = []
        new_list_2: List[Tuple[Message, List[Code2SeqPath], Commit]] = []
        new_list_1.extend(list_1)
        for message, paths, commit in list_2:
            if message in messages_set_1 and message in messages_set_2:
                new_list_1.append((message, paths, commit))
            else:
                new_list_2.append((message, paths, commit))
        return new_list_1, new_list_2

    commits_train, commits_tmp = split_list_in_two_parts(data_to_split, 0.6)
    if is_messages_intersected(commits_train, commits_tmp):
        commits_train, commits_tmp = fix_intersection(commits_train, commits_tmp)

    print(f"All size = {len(commits)}. Train size = {len(commits_train)}.")
    print(f"But train should be (.6){0.6 * len(commits)}")
    print(f"But train should be (.7){0.7 * len(commits)}")
    print(f"Part size is {len(commits_train) / len(commits)}")

    commits_val, commits_test = split_in_two_parts(commits_tmp, 0.5)

    def write_dataset_part(items: List[Tuple[Message, List[Code2SeqPath], Commit]], output_dir: Path,
                           dataset_part: DatasetPart):
        output_file: Path = output_dir.joinpath(str(dataset_part.value) + '.c2s')
        output_log: Path = output_dir.joinpath(str(dataset_part.value) + '_commits.log')
        with open(output_file, 'w') as out_f, open(output_log, 'w') as out_l:
            for message, paths, commit in items:
                out_f.write(dataset_line.substitute(target_message=message,
                                                    paths=' '.join(paths)))
                out_l.write(f'{commit}\n')
    write_dataset_part(commits_train, output_dir, DatasetPart.TRAIN)
    write_dataset_part(commits_test, output_dir, DatasetPart.TEST)
    write_dataset_part(commits_val, output_dir, DatasetPart.VAL)


if __name__ == '__main__':
    dataset = 'intellij'
    parent_dir: Path = Path('/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage')

    full_log_file = parent_dir.joinpath(f'gcm_{dataset}_full.log')
    needed_commits_pickle_file: Path = parent_dir.joinpath(f'{dataset}_commits_for_train.pickle')
    splitted_commits_file: Path = parent_dir.joinpath(f'{dataset}_splitted_commits_set_train_val_test.pickle')

    # split_dataset_with_no_file_commits_for_train(full_log_file, splitted_commits_file)
    # split_dataset(needed_commits_pickle_file, splitted_commits_file)

    # data_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath('processed_data').joinpath(dataset)
    # filtered_json: Path = data_dir.joinpath('diff_filtered.json')
    # splitted_commits: Path = data_dir.joinpath('splitted_dataset.pickle')
    # split_from_filtered_json(filtered_json, splitted_commits)

    # split_exact_changed_functions_number_per_commit_dataset(
    #     full_data=Path('/Users/natalia.murycheva/PycharmProjects/data/processed_data/intellij/c2s/2/intellij.all.2.txt'),
    #     train=Path('/Users/natalia.murycheva/PycharmProjects/data/processed_data/intellij/c2s/2/int.2.train.txt'),
    #     test=Path('/Users/natalia.murycheva/PycharmProjects/data/processed_data/intellij/c2s/2/int.2.test.txt'),
    #     val=Path('/Users/natalia.murycheva/PycharmProjects/data/processed_data/intellij/c2s/2/int.2.val.txt')
    # )

    # split_dataset_when_only_paths_are_given(
    #     paths_file=Path('../../new_data/processed_data/c2s_paths/data/'
    #                     'top1000_200_tokens/top1000_200_tokens_400_context_size/full_dataset.txt'),
    #     commits_log=Path('../../new_data/processed_data/c2s_paths/data/'
    #                      'top1000_200_tokens/top1000_200_tokens_400_context_size/c2s_commits.log'),
    #     output_dir=Path('../../new_data/processed_data/c2s_paths/data/'
    #                     'top1000_200_tokens/top1000_200_tokens_400_context_size/top1000_200_tokens')
    # )

    split_from_filtered_json(Path('../../new_data/camel/diffs_context_size_2.json'),
                             Path('../../new_data/camel/splitted_diffs.json'))
