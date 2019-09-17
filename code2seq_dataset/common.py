import re
from code2seq_dataset.info_classes import BlobInfo, FunctionInfo, FullLogLine, NextBlobMetaInfo
import collections
from pathlib import Path
from typing import DefaultDict, List, Tuple, Set, BinaryIO


def parse_full_log(full_log: Path) -> DefaultDict[str, List[NextBlobMetaInfo]]:
    blob_vs_messages: DefaultDict[str, List[NextBlobMetaInfo]] = collections.defaultdict(list)

    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            if line.startswith("commit_hash"):
                continue

            full_log_line: FullLogLine = FullLogLine.parse_from_line(line)
            blob_vs_messages[full_log_line.old_blob].append(NextBlobMetaInfo(full_log_line.commit,
                                                                             full_log_line.new_blob,
                                                                             full_log_line.message))

    return blob_vs_messages


def get_blobs_positions(data: Path) -> DefaultDict[str, List[Tuple[int, int]]]:
    blobs_positions: DefaultDict[str, List[Tuple[int, int]]] = collections.defaultdict(list)
    #  blobName: [(startPos, lineLen), (startPos, lineLen), ... ]

    with open(data, "r") as data_file:
        start_pos: int = 0
        for line in data_file:
            line_len: int = len(bytes(line.encode("utf-8")))
            function_info: FunctionInfo = FunctionInfo.parse_from_str(line)
            blobs_positions[function_info.blob_hash].append((start_pos, line_len))
            start_pos += line_len

    return blobs_positions


def split_commit_message(message: str) -> List[str]:
    message = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', message)
    message_tokenized = re.findall(r"[A-Z]*[a-z]*|<num>", message)
    return [x.lower() for x in message_tokenized if x != '']


def clean_function_body_from_new_line_characters(paths: Set[str]) -> Set[str]:
    cleaned_paths: Set[str] = set()

    for path in paths:
        if '\n' in path:
            path = path[: path.index('\n')] + path[(path.index('\n') + 1):]
        cleaned_paths.add(path)

    return cleaned_paths


def collect_changed_functions(blob: BlobInfo,
                              other_blob: BlobInfo,
                              data_file: BinaryIO) -> (Set[Tuple[FunctionInfo, FunctionInfo]],
                                                       Set[Tuple[FunctionInfo, FunctionInfo]]):
    changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()
    full_removed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()

    for start, len_ in blob.functions_positions:
        function = FunctionInfo.read_from_file(data_file, start, len_)
        other_function = function.find_method_with_the_same_name(data_file, other_blob)

        if other_function:
            if other_function != function:
                changed_functions.add((function, other_function))
        else:
            full_removed_functions.add((function,
                                        FunctionInfo(function.function_name,
                                                     other_blob.hash,
                                                     [])))

    return changed_functions, full_removed_functions


def compare_two_blobs(blob: BlobInfo,
                      other_blob: BlobInfo,
                      data_file: BinaryIO) -> Set[Tuple[FunctionInfo, FunctionInfo]]:

    changed_functions, deleted_functions = collect_changed_functions(blob, other_blob, data_file)
    _, added_functions = collect_changed_functions(other_blob, blob, data_file)

    added_functions = {(b, a) for a, b in added_functions}

    return changed_functions | deleted_functions | added_functions
