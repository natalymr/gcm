import json
import os
from pathlib import Path
from typing import List, Set

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
    with open(train_file, 'w') as f:
        for commit in train_commits:
            deleted, added = commit.two_diffs_in_one_line()
            f.write(f'{deleted}\t{added}\t{commit.message}\n')

    with open(test_file, 'w') as f:
        for commit in test_commits:
            deleted, added = commit.two_diffs_in_one_line()
            f.write(f'{deleted}\t{added}\t{commit.message}\n')

    with open(split_log, 'w') as split_f:
        split_f.write(json.dumps({'TRAIN': train_commits, 'TEST': test_commits},
                                 default=CommitDiff.to_json,
                                 indent=2))


if __name__ == '__main__':
    filtered_diff_dir: Path = Path('../../../new_data/processed_data/two_inputs_100')
    output_parent_dir: Path = Path('../../../new_data/processed_data/splitted_two_input_100')
    # train_diffs, test_diffs = output_parent_dir.joinpath('train.diffs'), output_parent_dir.joinpath('test.diffs')
    # train_msg, test_msg = output_parent_dir.joinpath('train.msg'), output_parent_dir.joinpath('test.msg')
    split_log: Path = output_parent_dir.joinpath('split.log')

    # split_top1000_dataset(filtered_diff_dir, train_diffs, train_msg, test_diffs, test_msg, split_log)
    split_top1000_dataset_two_inputs(filtered_diff_dir,
                                     output_parent_dir / 'train_100.data',
                                     output_parent_dir / 'test_100.data',
                                     split_log)