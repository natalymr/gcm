import collections
import json
from typing import Dict, Tuple, List

from matplotlib.path import Path

from code2seq_dataset.commit_message_tokenizer import invert_dict
from code2seq_dataset.common import split_commit_message
from code2seq_dataset.global_vars import Message
from code2seq_dataset.info_classes import CommitLogLine
from common_dataset.diffs import CommitDiff
from common_dataset.logs import COMMON_SEP


def get_messages_from_log(commits_log: Path) -> List[Message]:
    result: List[Message] = []

    with open(commits_log, 'r') as f:
        for line in f:
            commits_log_line: CommitLogLine = CommitLogLine.parse_from_line(line, separator=COMMON_SEP)
            result.append(commits_log_line.message)

    return result


def get_messages_from_json(json_file: Path) -> List[Message]:
    with open(json_file, 'r') as f:
        commits = json.load(f)
    return [CommitDiff.from_dict(commit).message for commit in commits]


def messages_frequency(messages: List[Message]) -> Dict[int, Message]:
    message_vs_count: Dict[Message, int] = collections.defaultdict(int)

    for message in messages:
        message_vs_count[Message(" ".join(split_commit_message(message)))] += 1

    count_vs_msg = invert_dict(message_vs_count)
    return collections.OrderedDict(sorted(count_vs_msg.items(), reverse=True))


def messages_vs_author(commits_log: Path) -> Dict[int, Tuple[str, Message]]:
    message_vs_author_count: Dict[Tuple[str, Message], int] = collections.defaultdict(int)

    with open(commits_log, 'r') as f:
        for line in f:
            commits_log_line: CommitLogLine = CommitLogLine.parse_from_line(line, separator=COMMON_SEP)
            author = commits_log_line.author
            message = Message(" ".join(split_commit_message(commits_log_line.message)))
            message_vs_author_count[(author, message)] += 1

    count_vs_pair = invert_dict(message_vs_author_count)
    return collections.OrderedDict(sorted(count_vs_pair.items(), reverse=True))
