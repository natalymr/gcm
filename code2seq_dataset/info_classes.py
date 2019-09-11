from dataclasses import dataclass
from typing import List, Tuple, Set, BinaryIO, Optional


@dataclass
class BlobInfo:
    hash: str
    functions_positions: List[Tuple[int, int]]


class FunctionInfo:
    def __init__(self, function_name: str, blob_hash: str, function_body: List[str] = None):
        self.function_name: str = function_name
        self.blob_hash: str = blob_hash
        self.function_body: Set[str] = set(function_body)

    def __eq__(self, other: "FunctionInfo"):
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
    def parse_from_str(line: str) -> "FunctionInfo":
        [method_header, *function_body] = line.split(" ")
        [blob_hash, method_name] = method_header.split("|", 1)
        blob_hash = blob_hash.replace(".java", "")

        return FunctionInfo(method_name, blob_hash, function_body)

    @staticmethod
    def read_from_file(file: BinaryIO, start: int, length: int) -> "FunctionInfo":
        file.seek(start, 0)
        decoded = file.read(length).decode("utf-8")
        return FunctionInfo.parse_from_str(decoded)

    def find_method_with_the_same_name(self, file: BinaryIO,
                                       other_blob: BlobInfo) -> Optional["FunctionInfo"]:
        for start, len_ in other_blob.functions_positions:
            other_function = FunctionInfo.read_from_file(file, start, len_)
            if self.function_name == other_function.function_name:
                return other_function

        return None

    def path_difference(self, other: "FunctionInfo") -> Set[str]:
        return self.function_body.symmetric_difference(other.function_body)