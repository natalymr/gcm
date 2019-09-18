from pathlib import Path
from typing import List
import unittest


class DatasetManyToOneLine:
    def __init__(self, commit_message: str, paths: List[str] = None,
                 paths_per_function: int = 200, functions_per_commit: int = 8):
        self.commit_message: str = commit_message
        self.functions_paths: List[List[str]] = [
            [paths[i * paths_per_function + j] for j in range(paths_per_function)] for i in range(functions_per_commit)
        ]

    @staticmethod
    def parse_from_str(line: str, paths_per_function: int, functions_per_commit: int) -> 'DatasetManyToOneLine':
        [commit_header, *paths] = line.split(" ")
        commit_message = commit_header.replace('|', ' ')

        return DatasetManyToOneLine(commit_message, paths, paths_per_function, functions_per_commit)


class ManyToOneDataset(unittest.TestCase):
    functions_per_commit: int = 8
    all_data = [{
                    'file': Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.val.raw.txt"),
                    'paths_per_function': 200
                },
                {
                    'file': Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.test.raw.txt"),
                    'paths_per_function': 200
                },
                {
                    'file': Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.train.raw.txt"),
                    'paths_per_function': 1000
                }]

    def test_padding_per_commit(self):
        """
        Check that in every commit there are 8 functions
        """

        for data in self.all_data:
            print(f"{data['file']}")
            with open(data['file'], 'r') as file:
                for line in file:
                    with self.subTest(line = line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(
                            line,
                            data['paths_per_function'],
                            self.functions_per_commit
                        )

                        self.assertEqual(len(dataset_line.functions_paths), self.functions_per_commit)

    def test_padding_per_function(self):
        """
        Check that every function is right padded

        """
        for data in self.all_data:
            print(f"{data['file']}")
            with open(data['file'], 'r') as file:
                for line in file:
                    with self.subTest(line=line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(
                            line,
                            data['paths_per_function'],
                            self.functions_per_commit
                        )

                        for func in dataset_line.functions_paths:
                            self.assertEqual(len(func), data['paths_per_function'])

    def test_no_message(self):
        """
        Check that there is no inappropriate messages in dataset
        """
        for data in self.all_data:
            print(f"{data['file']}")
            with open(data['file'], 'r') as file:
                for line in file:
                    with self.subTest(line=line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(
                            line,
                            data['paths_per_function'],
                            self.functions_per_commit
                        )
                        self.assertNotEqual(dataset_line.commit_message, 'no message')
                        self.assertNotEqual(dataset_line.commit_message, 'empty log message')