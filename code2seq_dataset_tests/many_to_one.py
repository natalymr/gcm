from pathlib import Path
from typing import List
import unittest

from code2seq_dataset.process_dataset_rnn_case import padded_path


class DatasetManyToOneLine:
    def __init__(self, commit_message: str, paths: List[str] = None):
        self.commit_message: str = commit_message
        self.functions_paths: List[str] = paths

    @staticmethod
    def parse_from_str(line: str) -> 'DatasetManyToOneLine':
        [commit_header, *paths] = line.split(" ")
        commit_message = commit_header.replace('|', ' ')
        paths[-1] = paths[-1].strip()

        return DatasetManyToOneLine(commit_message, paths)


def check_all_paths_is_padded(paths: List[str]) -> bool:
    for path in paths:
        if path != padded_path:
            return False

    return True


class ManyToOneDataset(unittest.TestCase):
    functions_per_commit: int = 8
    file_path: str = 'file_path'
    paths_per_function: str = 'paths_per_function'
    all_data = [{
                    file_path: Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.val.raw.txt"),
                    paths_per_function: 200
                },
                {
                    file_path: Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.test.raw.txt"),
                    paths_per_function: 200
                },
                {
                    file_path: Path("/Users/natalia.murycheva/Documents/code2seq/aurora.many.to.one.correct.train.raw.txt"),
                    paths_per_function: 1000
                }]

    def test_paths_count_per_commit(self):
        """
        Check that in every commit there are 8 functions with paths_per_function for each function
        """

        for data in self.all_data:
            with open(data[self.file_path], 'r') as file:
                for line in file:
                    with self.subTest(line = line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(line)

                        self.assertEqual(len(dataset_line.functions_paths),
                                         self.functions_per_commit * data[self.paths_per_function])

    def test_functions_padding_per_commit(self):
        """
        Check that if there is full padded function, next functions will be padded too
        """
        for data in self.all_data:
            with open(data[self.file_path], 'r') as file:
                for line in file:
                    with self.subTest(line=line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(line)
                        d_line_functions: List[List[str]] = [
                            [
                                dataset_line.functions_paths[data[self.paths_per_function] * i + j]
                                for j in range(data[self.paths_per_function])
                            ]
                            for i in range(self.functions_per_commit)
                        ]

                        there_is_padded_function = False
                        for function in d_line_functions:
                            if there_is_padded_function:
                                self.assertEqual(True, check_all_paths_is_padded(function))
                            elif function[0] == padded_path:
                                there_is_padded_function = True
                                self.assertEqual(True, check_all_paths_is_padded(function))

    def test_padding_per_function(self):
        """
        Check that every function is right padded

        """
        def check_every_function(paths: List[str]):
            for ind, path in enumerate(paths):
                if path == padded_path:
                    return check_all_paths_is_padded(paths[ind:])

            return True

        for data in self.all_data:
            with open(data[self.file_path], 'r') as file:
                for line in file:
                    with self.subTest(line=line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(line)
                        d_line_functions: List[List[str]] = [
                            [
                                dataset_line.functions_paths[data[self.paths_per_function] * i + j]
                                for j in range(data[self.paths_per_function])
                            ]
                            for i in range(self.functions_per_commit)
                        ]

                        for function in d_line_functions:
                            self.assertEqual(True, check_every_function(function))

    def test_no_message(self):
        """
        Check that there is no inappropriate messages in dataset
        """
        for data in self.all_data:
            with open(data[self.file_path], 'r') as file:
                for line in file:
                    with self.subTest(line=line):
                        dataset_line: DatasetManyToOneLine = DatasetManyToOneLine.parse_from_str(line)

                        self.assertNotEqual(dataset_line.commit_message, 'no message')
                        self.assertNotEqual(dataset_line.commit_message, 'empty log message')
