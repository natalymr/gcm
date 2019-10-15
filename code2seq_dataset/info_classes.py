from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple, Set, BinaryIO, Optional

from code2seq_dataset.global_vars import SEPARATOR, Commit, Blob, Message, Code2SeqPath

NextBlobMetaInfo = namedtuple('NextBlobMetaInfo', ['commit', 'new_blob', 'message'])
BlobPositions = namedtuple('BlobInfo', ['hash', 'functions_positions'])


class DatasetPart(Enum):
    TRAIN = auto()
    TEST = auto()
    VAL = auto()


@dataclass
class FullLogLine:
    commit: Commit
    author: str
    status: str
    file: str
    old_blob: Blob
    new_blob: Blob
    message: Message

    @staticmethod
    def parse_from_line(line: str, separator: str = SEPARATOR) -> 'FullLogLine':
        list_ = line.split(separator)

        return FullLogLine(commit=Commit(list_[0]),
                           author=list_[1],
                           status=list_[2],
                           file=list_[3],
                           old_blob=Blob(list_[4]),
                           new_blob=Blob(list_[5]),
                           message=Message(list_[6]))


@dataclass
class CommitLogLine:
    parent_commit: Commit
    current_commit: Commit
    author: str
    date: str
    message: Message

    @staticmethod
    def parse_from_line(line: str, separator: str = SEPARATOR) -> 'CommitLogLine':
        list_ = line.split(separator)

        return CommitLogLine(parent_commit=Commit(list_[0]),
                             current_commit=Commit(list_[1]),
                             author=list_[2],
                             date=list_[3],
                             message=Message(list_[4]))


class FunctionInfo:
    def __init__(self, function_name: str, blob_hash: str, function_body: List[str] = None):
        self.function_name: str = function_name
        self.blob_hash: Blob = Blob(blob_hash)
        self.function_body: Set[Code2SeqPath] = set([Code2SeqPath(fb) for fb in function_body])

    def __eq__(self, other: 'FunctionInfo'):
        if isinstance(other, FunctionInfo):
            # there is a formula for comparing two lists:
            # set(b) == set(a)  & set(b) and set(a) == set(a) & set(b)
            is_paths_equals: bool = self.function_body == other.function_body & self.function_body and \
                other.function_body == other.function_body & self.function_body

            return self.function_name == other.function_name and is_paths_equals

        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.function_name) ^ hash(tuple(self.function_body))

    @staticmethod
    def parse_from_str(line: str) -> 'FunctionInfo':
        [method_header, *function_body] = line.split(" ")
        [blob_hash, method_name] = method_header.split("|", 1)
        blob_hash = blob_hash.replace(".java", "")

        return FunctionInfo(method_name, blob_hash, function_body)

    @staticmethod
    def read_from_file(file: BinaryIO, start: int, length: int) -> 'FunctionInfo':
        file.seek(start, 0)
        decoded = file.read(length).decode("utf-8")
        return FunctionInfo.parse_from_str(decoded)

    def find_method_with_the_same_name(self, file: BinaryIO,
                                       other_blob: BlobPositions) -> List['FunctionInfo']:
        result: List['FunctionInfo'] = []

        for start, len_ in other_blob.functions_positions:
            other_function = FunctionInfo.read_from_file(file, start, len_)
            if self.function_name == other_function.function_name:
                result.append(other_function)

        return result

    def path_difference(self, other: 'FunctionInfo') -> Set[Code2SeqPath]:
        return self.function_body.symmetric_difference(other.function_body)


@dataclass
class PredictedResults:
    commit: Commit
    old_blob: Blob
    new_blob: Blob
    function_name: str
    predicted_message: Message

    @staticmethod
    def parse_from_str(line: str) -> Optional['PredictedResults']:
        line_list = line.split(",")
        if len(line_list) == 2:
            original, predicted = line_list[0], line_list[1]

            # original
            original_list = original.split(":")
            meta_info = original_list[1].split("|")
            if len(meta_info) > 2:
                commit, old_blob, new_blob, function_name = meta_info[0], meta_info[1], meta_info[2], meta_info[3:]
                commit = commit.strip()

                # predicted
                predicted_list = predicted.split(":")
                predicted_message = predicted_list[1].strip("\n").split("|")

                return PredictedResults(commit=Commit(commit),
                                        old_blob=Blob(old_blob),
                                        new_blob=Blob(new_blob),
                                        function_name=" ".join(function_name),
                                        predicted_message=Message(" ".join(predicted_message)))

        return None

    @staticmethod
    def read_from_line(file: BinaryIO, start: int, length: int) -> Optional['PredictedResults']:
        file.seek(start, 0)
        decoded = file.read(length).decode("utf-8")
        return PredictedResults.parse_from_str(decoded)

    @staticmethod
    def find_results_for_commit_and_blobs(commit_predictions_positions: List[Tuple[int, int]],
                                          old_blob: Blob,
                                          new_blob: Blob,
                                          file: BinaryIO) -> List['PredictedResults']:
        result: List['PredictedResults'] = []

        for start, len_ in commit_predictions_positions:
            predicted: PredictedResults = PredictedResults.read_from_line(file, start, len_)
            if predicted and predicted.old_blob == old_blob and predicted.new_blob == new_blob:
                result.append(predicted)

        return result
