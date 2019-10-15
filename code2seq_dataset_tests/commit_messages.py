from code2seq_dataset.info_classes import FullLogLine, DatasetPart
import collections
from pathlib import Path
import pickle
from typing import Dict, Set, List
import unittest


class CommitMessages(unittest.TestCase):
    dataset = "camel"
    parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")
    full_log: Path = parent_dir.joinpath(f"gcm_{dataset}_full.log")
    com_log: Path = parent_dir.joinpath(f"gcm_{dataset}_com_com_msg_author_date.log")
    split_commits: Path = parent_dir.joinpath(f"{dataset}_splitted_commits_set_train_val_test.pickle")

    def testTestMessagesNotInTrainMessages(self):
        with open(self.split_commits, 'rb') as sdf:
            splitted_dataset: Dict[DatasetPart, Set[str]] = pickle.load(sdf)

        unique_messages: Dict[DatasetPart, Set[str]] = collections.defaultdict(set)
        all_messages: Dict[DatasetPart, List[str]] = collections.defaultdict(list)

        with open(self.full_log, 'r') as f:
            for line in f:
                full_log_line: FullLogLine = FullLogLine.parse_from_line(line)

                key = [key for key, commits in splitted_dataset.items() if full_log_line.commit in commits]
                if len(key) == 1:
                    key = key[0]
                    unique_messages[key].add(full_log_line.message)
                    all_messages[key].append(full_log_line.message)

        print(f"tr: {len(unique_messages[DatasetPart.TRAIN])}, {len(all_messages[DatasetPart.TRAIN])}")
        print(f"t: {len(unique_messages[DatasetPart.TEST])}, {len(all_messages[DatasetPart.TEST])}")
        print(f"v: {len(unique_messages[DatasetPart.VAL])}, {len(all_messages[DatasetPart.VAL])}")

        print(f"tr & t {len(unique_messages[DatasetPart.TRAIN] & unique_messages[DatasetPart.TEST])}")
        print(f"tr & v {len(unique_messages[DatasetPart.TRAIN] & unique_messages[DatasetPart.VAL])}")
        # self.assertSetEqual(set(), messages[DatasetPart.TRAIN] & messages[DatasetPart.VAL])
        # self.assertSetEqual(set(), messages[DatasetPart.TRAIN] & messages[DatasetPart.TEST])
