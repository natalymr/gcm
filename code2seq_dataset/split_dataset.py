import pickle
from pathlib import Path
from random import shuffle
from typing import List, Set


def split_list_in_two_parts(input_list: List[str], part_size: float) -> (List[str], List[str]):
    size: int = len(input_list)
    first_part_size: int = int(size * part_size)

    return input_list[:first_part_size], input_list[first_part_size + 1:]


def split_dataset(commits_for_train: Path, output: Path):
    with open(commits_for_train, 'rb') as cftf:
        needed_commits: Set[str] = pickle.load(cftf)
    needed_commits: List[str] = list(needed_commits)
    shuffle(needed_commits)

    # split dataset
    commits_train, commits_tmp = split_list_in_two_parts(needed_commits, 0.7)
    commits_val, commits_test = split_list_in_two_parts(commits_tmp, 0.5)

    print(f"train: {len(commits_train)}, test: {len(commits_test)}, val: {len(commits_val)}")

    splitted_commits = {'train': set(commits_train), 'test': set(commits_test), 'val': set(commits_val)}

    with open(output, 'wb') as output_file:
        pickle.dump(splitted_commits, output_file)


if __name__ == "__main__":
    git_dir_name = "intellij"
    parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")

    needed_commits_pickle_file: Path = parent_dir.joinpath(f"{git_dir_name}_commits_for_train.pickle")
    splitted_commits: Path = parent_dir.joinpath(f"{git_dir_name}_splitted_commits_set_train_val_test.pickle")

    split_dataset(needed_commits_pickle_file, splitted_commits)
