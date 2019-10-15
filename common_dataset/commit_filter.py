import json
import re
import subprocess
from pathlib import Path

from code2seq_dataset.common import split_commit_message
from common_dataset.diffs import CommitDiff

num = "<num>"


# messages
def first_splitter_filter(commit: CommitDiff) -> CommitDiff:
    commit.message = " ".join(split_commit_message(commit.message))
    return commit


def delete_key_words_in_commit_messages(commit: CommitDiff, key_word: str) -> CommitDiff:
    commit.message = commit.message.replace(key_word, "")
    return commit


def delete_pattern_in_commit_message(commit: CommitDiff, pattern: str) -> CommitDiff:
    commit.message = re.sub(pattern, '', commit.message)
    return commit


def filter_by_commit_message_len(commit: CommitDiff, max_len: int) -> bool:
    return len(split_commit_message(commit.message)) <= max_len


def filter_rollback_or_merge(commit: CommitDiff, keywords: str) -> bool:
    return keywords not in commit.message


def filter_empty_messages(commit: CommitDiff) -> bool:
    return commit.message != " " and commit.message != ""


# diff
def filter_by_diff_len(commit: CommitDiff, max_len: int) -> bool:
    pass


def filter_commit_messages(json_file: Path, context_size: int, max_message_len: int, max_diff_len: int):
    with open(json_file, 'r') as f:
        commits = json.load(f)
    commits = [CommitDiff.from_dict(commit) for commit in commits]

    # messages
    commits = list(map(first_splitter_filter, commits))  # must be first
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, "issue <num>"), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, "camel <num>"), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, "scr <num>"), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, "idea <num>"), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, "#<num>"), commits))

    commits = list(map(lambda c: delete_pattern_in_commit_message(c, 'provided by \\w+'), commits))

    commits = list(filter(lambda c: filter_by_commit_message_len(c, max_message_len), commits))
    commits = list(filter(lambda c: filter_rollback_or_merge(c, ""), commits))
    commits = list(filter(filter_empty_messages, commits))  # must be last




if __name__ == '__main__':
    git_dir_name: str = 'camel'
    output_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath("raw_data").joinpath(git_dir_name)
    all_diffs: Path = output_dir.joinpath("diffs_context_size_10.json")

    # filter_commit_messages(all_diffs, 3, 20, 200)
