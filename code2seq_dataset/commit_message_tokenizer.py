import collections
from collections import OrderedDict
import itertools
from keras.preprocessing.text import Tokenizer
from pathlib import Path
from typing import Dict, List, Mapping, DefaultDict, Set

from code2seq_dataset.info_classes import CommitLogLine, FullLogLine
from code2seq_dataset.global_vars import Message, Commit


def invert_dict(input_dict: Mapping[str, int]) -> DefaultDict[int, List[str]]:
    output_dict: DefaultDict[int, List[str]] = collections.defaultdict(list)

    for key, value in input_dict.items():
        output_dict[value].append(key)

    return output_dict


def commit_msg_tokenizing_aurora(com_log: Path):
    msg_vs_counts: Dict[Message, int] = {}
    msgs: List[Message] = []

    with open(com_log, 'r') as f:
        for line in f:
            if line.startswith("parent_commit_file_hash"):
                continue

            com_line: CommitLogLine = CommitLogLine.parse_from_line(line)
            message: Message = com_line.message
            if message == "no message" or \
                    message == "New version" or \
                    message == "Build completed" or \
                    message == "Build failed" or \
                    message == "*** empty log message ***":
                continue
            else:
                msgs.append(message)
                message: Message = Message(message.lower())
                if message in msg_vs_counts:
                    msg_vs_counts[message] += 1
                else:
                    msg_vs_counts[message] = 1

    print(f"Unique message number {len(msg_vs_counts)}")

    counts_vs_msg = invert_dict(msg_vs_counts)
    counts_vs_msg_sorted = OrderedDict(sorted(counts_vs_msg.items(), reverse=True))
    top_popular_msg = dict(itertools.islice(counts_vs_msg_sorted.items(), 0, 20))

    for key, value in counts_vs_msg_sorted.items():
        print("{:>3}: {} {}".format(key, len(value), value))

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(msgs)

    counts_vs_word = invert_dict(tokenizer.word_counts)
    counts_vs_word_sorted = OrderedDict(sorted(counts_vs_word.items(), reverse=True))
    top_popular_words = dict(itertools.islice(counts_vs_word_sorted.items(), 0, 20))
    print(top_popular_words)


def get_commits_from_full_log(full_log: Path) -> Set[Commit]:
    result: Set[Commit] = set()

    with open(full_log, 'r') as f:
        for line in f:
            full_log_line: FullLogLine = FullLogLine.parse_from_line(line)
            result.add(full_log_line.commit)

    return result


def commit_msg_tokenizing_camel(com_log: Path, full_log: Path):
    msg_vs_counts: Dict[Message, int] = {}
    msgs: List[Message] = []

    commits_from_full_log: Set[Commit] = get_commits_from_full_log(full_log)

    with open(com_log, 'r') as f:
        for line in f:
            if line.startswith("parent_commit_file_hash"):
                continue

            com_log_line: CommitLogLine = CommitLogLine.parse_from_line(line)
            if com_log_line.current_commit in commits_from_full_log:
                message: Message = com_log_line.message
                msgs.append(message)
                message: Message = Message(message.lower())
                if message in msg_vs_counts:
                    msg_vs_counts[message] += 1
                else:
                    msg_vs_counts[message] = 1

    print(f"Unique message number {len(msg_vs_counts)}")

    counts_vs_msg = invert_dict(msg_vs_counts)
    counts_vs_msg_sorted = OrderedDict(sorted(counts_vs_msg.items(), reverse=True))
    top_popular_msg = dict(itertools.islice(counts_vs_msg_sorted.items(), 0, 20))

    for key, value in counts_vs_msg_sorted.items():
        print("{:>3}: {} {}".format(key, len(value), value))

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(msgs)

    counts_vs_word = invert_dict(tokenizer.word_counts)
    counts_vs_word_sorted = OrderedDict(sorted(counts_vs_word.items(), reverse=True))
    top_popular_words = dict(itertools.islice(counts_vs_word_sorted.items(), 0, 30))
    print(top_popular_words)


if __name__ == "__main__":
    git_dir_name = "hadoop"
    parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")
    com_log_file: Path = parent_dir.joinpath(f"gcm_{git_dir_name}_com_com_msg_author_date.log")
    full_log: Path = parent_dir.joinpath(f"gcm_{git_dir_name}_full.log")

    # commit_msg_tokenizing_aurora(com_log_file)
    commit_msg_tokenizing_camel(com_log_file, full_log)
