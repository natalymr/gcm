from pathlib import Path
from typing import List
import unittest

from code2seq_dataset.global_vars import padded_path, Message, Code2SeqPath


class DatasetManyToOneLine:
    def __init__(self, commit_message: str, paths: List[str] = None):
        self.commit_message: Message = Message(commit_message)
        self.functions_paths: List[Code2SeqPath] = [Code2SeqPath(path) for path in paths]

    @staticmethod
    def parse_from_str(line: str) -> 'DatasetManyToOneLine':
        [commit_header, *paths] = line.split(" ")
        commit_message = commit_header.replace('|', ' ')
        paths[-1] = paths[-1].strip()

        return DatasetManyToOneLine(commit_message, paths)


def check_all_paths_is_padded(paths: List[Code2SeqPath]) -> bool:
    for path in paths:
        if path != padded_path:
            return False

    return True


class ManyToOneDataset(unittest.TestCase):
    functions_per_commit: int = 4
    paths_per_function: int = 200
    all_data = [
        Path("/Users/natalia.murycheva/Documents/code2seq/data/camel/camel.train.c2s"),
        # Path("/Users/natalia.murycheva/Documents/code2seq/camel.1.test.raw.txt"),
        # Path("/Users/natalia.murycheva/Documents/code2seq/camel.1.val.raw.txt")
    ]

    def test_paths_count_per_commit(self):
        """
        Check that in every commit there are 8 functions with paths_per_function for each function
        """

        for data_file in self.all_data:
            with open(data_file, 'r') as f:
                for line in f:
                    with self.subTest(line = line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(line)

                        self.assertEqual(len(dataset_line.functions_paths),
                                         self.functions_per_commit * self.paths_per_function)

    def test_padding_per_commit(self):
        """
        Check that every commit is right padded

        """
        def check_every_commit(paths: List[Code2SeqPath]):
            for ind, path in enumerate(paths):
                if path == padded_path:
                    return check_all_paths_is_padded(paths[ind:])

            return True

        for data_file in self.all_data:
            with open(data_file, 'r') as f:
                for line in f:
                    with self.subTest(line=line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(line)
                        self.assertEqual(True, check_every_commit(dataset_line.functions_paths))

    def test_no_message(self):
        """
        Check that there is no inappropriate messages in dataset
        """
        for data_file in self.all_data:
            with open(data_file, 'r') as f:
                for line in f:
                    with self.subTest(line=line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(line)

                        self.assertNotEqual(dataset_line.commit_message, 'no message')
                        self.assertNotEqual(dataset_line.commit_message, 'empty log message')
