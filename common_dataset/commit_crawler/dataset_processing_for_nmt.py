import json
import os
import re
from pathlib import Path
from typing import List, Set

from tqdm import tqdm

from code2seq_dataset.common import split_commit_message
from code2seq_dataset.global_vars import Message
from common_dataset.commit_crawler.get_blobs import get_commits_from_json
from common_dataset.diffs import CommitDiff, FileDiffWithTwoInput


def is_messages_sets_intersected(one: List[CommitDiff], other: List[CommitDiff]) -> bool:
    return 0 != len({c.message for c in one} & {c.message for c in other})


def split_list_in_two_parts(input_list: List[CommitDiff], part_size: float) -> (List[CommitDiff], List[CommitDiff]):
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


def split_top1000_dataset(filtered_diff_dir: Path, train_diffs: Path, train_msg: Path,
                          test_diffs: Path, test_msg: Path, split_log: Path) -> None:
    all_diffs_files: List[str] = os.listdir(filtered_diff_dir)
    commits: List[CommitDiff] = []
    for diff in all_diffs_files:
        print(diff)
        commits.extend(get_commits_from_json(filtered_diff_dir / diff))

    # we have empty commit that has a lot <nl> tokens, so, remove it
    commits_to_delete: List[CommitDiff] = []
    for commit in commits:
        if len(commit.diff_in_one_line().split(' ')) > 300:
            commits_to_delete.append(commit)
    for c_2_d in commits_to_delete:
        commits.remove(c_2_d)

    train_commits, test_commits = split_list_in_two_parts(commits, 0.67)
    if is_messages_sets_intersected(train_commits, test_commits):
        train_commits, test_commits = fix_messages_sets_intersections(train_commits, test_commits)
    with open(train_diffs, 'w') as diff_f, open(train_msg, 'w') as msg_f:
        for commit in train_commits:
            diff_f.write(f'{commit.diff_in_one_line()}\n')
            msg_f.write(f'{commit.message}\n')

    with open(test_diffs, 'w') as diff_f, open(test_msg, 'w') as msg_f:
        for commit in test_commits:
            diff_f.write(f'{commit.diff_in_one_line()}\n')
            msg_f.write(f'{commit.message}\n')

    with open(split_log, 'w') as split_f:
        split_f.write(json.dumps({'TRAIN': train_commits, 'TEST': test_commits},
                                 default=CommitDiff.to_json, indent=2))


def split_top1000_dataset_two_inputs(filtered_diff_dir: Path, train_file: Path, test_file: Path,
                                     split_log: Path) -> None:
    all_diffs_files: List[str] = os.listdir(filtered_diff_dir)
    commits: List[CommitDiff] = []
    for diff in all_diffs_files:
        print(diff)
        commits.extend(get_commits_from_json(filtered_diff_dir / diff))
    print(f'Number of commits {len(commits)}')

    train_commits, test_commits = split_list_in_two_parts(commits, 0.67)
    if is_messages_sets_intersected(train_commits, test_commits):
        train_commits, test_commits = fix_messages_sets_intersections(train_commits, test_commits)

    print(f'Train {len(train_commits)}, Test {len(test_commits)}')
    # with open(train_file, 'w') as f:
    #     for commit in train_commits:
    #         deleted, added = commit.two_diffs_in_one_line()
    #         f.write(f'{deleted}\t{added}\t{commit.message}\n')
    #
    # with open(test_file, 'w') as f:
    #     for commit in test_commits:
    #         deleted, added = commit.two_diffs_in_one_line()
    #         f.write(f'{deleted}\t{added}\t{commit.message}\n')
    #
    # with open(split_log, 'w') as split_f:
    #     split_f.write(json.dumps({'TRAIN': train_commits, 'TEST': test_commits},
    #                              default=CommitDiff.to_json,
    #                              indent=2))


def split_top1000_dataset_two_inputs_three_part(filtered_diff_dir: Path,
                                                train_file: Path, test_file: Path, val_file: Path,
                                                split_log: Path) -> None:
    all_diffs_files: List[str] = os.listdir(filtered_diff_dir)
    commits: List[CommitDiff] = []
    for diff in all_diffs_files:
        commits.extend(get_commits_from_json(filtered_diff_dir / diff))
    print(f'Number of commits {len(commits)}')

    train_commits, test_commits = split_list_in_two_parts(commits, 0.67)
    if is_messages_sets_intersected(train_commits, test_commits):
        train_commits, test_commits = fix_messages_sets_intersections(train_commits, test_commits)
    test_commits, val_commits = split_list_in_two_parts(test_commits, 0.5)
    if is_messages_sets_intersected(test_commits, val_commits):
        test_commits, val_commits = fix_messages_sets_intersections(test_commits, val_commits)

    print(f'Train {len(train_commits)}, Test {len(test_commits)}, Val {len(val_commits)}')
    with open(train_file, 'w') as f:
        for commit in train_commits:
            deleted, added = commit.two_diffs_in_one_line()
            f.write(f'{deleted}\t{added}\t{commit.message}\n')

    with open(test_file, 'w') as f:
        for commit in test_commits:
            deleted, added = commit.two_diffs_in_one_line()
            f.write(f'{deleted}\t{added}\t{commit.message}\n')

    with open(val_file, 'w') as f:
        for commit in val_commits:
            deleted, added = commit.two_diffs_in_one_line()
            f.write(f'{deleted}\t{added}\t{commit.message}\n')

    with open(split_log, 'w') as split_f:
        split_f.write(json.dumps({'TRAIN': train_commits, 'TEST': test_commits, 'VAL': val_commits},
                                 default=CommitDiff.to_json,
                                 indent=2))


def keep_only_needed_number_of_line_around_changes(diff_body, context_size_in_lines=2):
    """
    This function will keep only those line that are related to changes or its context
    :param context_size_in_lines: what number of lines will be saved around changes
    """
    mask: List[int] = [0] * len(diff_body)
    for i, line in enumerate(diff_body):
        if line.startswith('@@'):
            mask[i] = 1
        if line.startswith('+') or line.startswith('-'):
            min_ind = max(0, i - context_size_in_lines)
            max_ind = min(i + context_size_in_lines, len(diff_body) - 1)
            for j in range(min_ind, max_ind + 1):
                mask[j] = 1
    return [diff_body[i] for i, v in enumerate(mask) if v]


def tokenize_line(line) -> (str, int):
    line = re.sub(r'\"([^\\\"]|\\.)*\"', 'str_variable', line)
    line = re.sub(r'(\w)(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
    line = re.sub(r'([^a-zA-Z0-9_ ])(?=\w)', r'\1 ', line)
    line = re.sub(r'([^a-zA-Z0-9_ ])(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
    line = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', line)

    return line


def tokenize_common_diff(diff_body):
    for i in range(len(diff_body)):
        diff_body[i] = tokenize_line(diff_body[i])
    return diff_body


def get_common_diff_from_two_input(split_log: Path, output_file: Path) -> None:
    with open(split_log, 'r') as f:
        data = json.load(f)
    print(data['TRAIN'][0])
    train_data = [CommitDiff.from_dict(commit) for commit in data['TRAIN']]
    test_data = [CommitDiff.from_dict(commit) for commit in data['TEST']]
    val_data = [CommitDiff.from_dict(commit) for commit in data['VAL']]

    print(f'train {len(train_data)}, test {len(test_data)}, val {len(val_data)}')

    for commit in tqdm(train_data):
        for i, changed_file in enumerate(commit.changed_java_files):
            commit.message = " ".join(split_commit_message(commit.message))
            commit.changed_java_files[i].diff_body_common = keep_only_needed_number_of_line_around_changes(commit
                                                                                                           .changed_java_files[i]
                                                                                                           .diff_body_common)
            commit.changed_java_files[i].diff_body_common = tokenize_common_diff(commit.changed_java_files[i].diff_body_common)

    for commit in tqdm(test_data):
        for i, changed_file in enumerate(commit.changed_java_files):
            commit.message = " ".join(split_commit_message(commit.message))
            commit.changed_java_files[i].diff_body_common = keep_only_needed_number_of_line_around_changes(commit
                                                                                                           .changed_java_files[i]
                                                                                                           .diff_body_common)
            commit.changed_java_files[i].diff_body_common = tokenize_common_diff(
                commit.changed_java_files[i].diff_body_common)

    for commit in tqdm(val_data):
        for i, changed_file in enumerate(commit.changed_java_files):
            commit.message = " ".join(split_commit_message(commit.message))
            commit.changed_java_files[i].diff_body_common = keep_only_needed_number_of_line_around_changes(commit
                                                                                                           .changed_java_files[i]
                                                                                                           .diff_body_common)
            commit.changed_java_files[i].diff_body_common = tokenize_common_diff(
                commit.changed_java_files[i].diff_body_common)

    with open(output_file, 'w') as f:
        f.write(json.dumps({'TRAIN': train_data, 'TEST': test_data, 'VAL': val_data},
                           default=CommitDiff.to_json,
                           indent=2))


def get_data_for_one_input_nmt_from_split_log():
    # all_data = Path('../../../new_data/processed_data/nematus_data/split.log')
    all_data = Path('../../../new_data/processed_data/splitted_two_input_200/for_nngen.log')
    # train_output = Path('../../NMT/natalymr/pytorch-seq2seq/data/diffs/train/nmt_1_input_train_200.txt')
    train_output = all_data.parent.parent.joinpath('nmt_1_input_train_200.txt')
    test_output = all_data.parent.parent.joinpath('nmt_1_input_test_200.txt')
    # test_output = Path('../../NMT/natalymr/pytorch-seq2seq/data/diffs/test/nmt_1_input_test_200.txt')
    with open(all_data, 'r') as f:
        all_data_dict = json.load(f)
    train_data = [CommitDiff.from_dict(commit) for commit in all_data_dict['TRAIN']]
    test_data = [CommitDiff.from_dict(commit) for commit in all_data_dict['TEST']]

    with open(train_output, 'w') as f:
        for i, commit in enumerate(train_data):
            com_diff_list = []
            for changed_file in commit.changed_java_files:
                for line in changed_file.diff_body_common:
                    line = re.sub(r"[\n\t\r]*", "", line)
                    com_diff_list.append(line.strip())

            com_diff = ' <nl> '.join(com_diff_list)
            f.write(f'{com_diff}\t{commit.message}\n')

    with open(test_output, 'w') as f:
        for commit in test_data:
            com_diff_list = []
            for changed_file in commit.changed_java_files:
                for line in changed_file.diff_body_common:
                    line = re.sub(r"[\n\t\r]*", "", line)
                    com_diff_list.append(line.strip())

            com_diff = ' <nl> '.join(com_diff_list)
            f.write(f'{com_diff}\t{commit.message}\n')

    print(f'train {len(train_data)}, test {len(test_data)}')


if __name__ == '__main__':
    filtered_diff_dir: Path = Path('../../../new_data/processed_data/two_inputs_200')
    output_parent_dir: Path = Path('../../../new_data/processed_data/splitted_two_input_200')
    # train_diffs, test_diffs = output_parent_dir.joinpath('train.diffs'), output_parent_dir.joinpath('test.diffs')
    # train_msg, test_msg = output_parent_dir.joinpath('train.msg'), output_parent_dir.joinpath('test.msg')
    split_log: Path = output_parent_dir.joinpath('split.log')

    # split_top1000_dataset(filtered_diff_dir, train_diffs, train_msg, test_diffs, test_msg, split_log)
    # split_top1000_dataset_two_inputs(filtered_diff_dir,
    #                                  output_parent_dir / 'train_100.data',
    #                                  output_parent_dir / 'test_100.data',
    #                                  split_log)

    # split_top1000_dataset_two_inputs_three_part(filtered_diff_dir,
    #                                             output_parent_dir / 'train_200.data',
    #                                             output_parent_dir / 'test_200.data',
    #                                             output_parent_dir / 'val_200.data',
    #                                             split_log)
    #
    # get_common_diff_from_two_input(split_log, output_parent_dir.joinpath('for_nngen.log'))
    # get_data_for_one_input_nmt_from_split_log()
