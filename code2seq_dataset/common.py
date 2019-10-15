import re
import collections
from pathlib import Path
from typing import DefaultDict, List, Tuple, Set, BinaryIO

from code2seq_dataset.global_vars import Message, Code2SeqPath, Blob
from code2seq_dataset.info_classes import BlobPositions, FunctionInfo, FullLogLine, NextBlobMetaInfo


def parse_full_log(full_log: Path) -> DefaultDict[Blob, List[NextBlobMetaInfo]]:
    blobs_history: DefaultDict[Blob, List[NextBlobMetaInfo]] = collections.defaultdict(list)

    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            if line.startswith("commit_hash"):
                continue

            full_log_line: FullLogLine = FullLogLine.parse_from_line(line)
            blobs_history[full_log_line.old_blob].append(NextBlobMetaInfo(full_log_line.commit,
                                                                          full_log_line.new_blob,
                                                                          full_log_line.message))

    return blobs_history


def get_blobs_positions(data: Path) -> DefaultDict[Blob, List[Tuple[int, int]]]:
    blobs_positions: DefaultDict[Blob, List[Tuple[int, int]]] = collections.defaultdict(list)
    #  blobName: [(startPos, lineLen), (startPos, lineLen), ... ]

    with open(data, 'r') as data_file:
        start_pos: int = 0
        for line in data_file:
            line_len: int = len(bytes(line.encode("utf-8")))
            function_info: FunctionInfo = FunctionInfo.parse_from_str(line)
            blobs_positions[function_info.blob_hash].append((start_pos, line_len))
            start_pos += line_len

    return blobs_positions


def split_commit_message(message: Message) -> List[str]:
    message = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', message)
    message_tokenized = re.findall(r"[A-Z]*[a-z]*|<num>", message)
    return [x.lower() for x in message_tokenized if x != '']


def clean_function_body_from_new_line_characters(paths: Set[Code2SeqPath]) -> Set[Code2SeqPath]:
    cleaned_paths: Set[Code2SeqPath] = set()

    for path in paths:
        if '\n' in path:
            path: str = path[: path.index('\n')] + path[(path.index('\n') + 1):]
            path: Code2SeqPath = Code2SeqPath(path)
        cleaned_paths.add(path)

    return cleaned_paths


def collect_changed_functions(blob: BlobPositions,
                              other_blob: BlobPositions,
                              data_file: BinaryIO) -> (Set[Tuple[FunctionInfo, FunctionInfo]],
                                                       Set[Tuple[FunctionInfo, FunctionInfo]]):
    changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()
    full_removed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()

    for start, len_ in blob.functions_positions:
        function = FunctionInfo.read_from_file(data_file, start, len_)
        other_functions: List[FunctionInfo] = function.find_method_with_the_same_name(data_file, other_blob)

        if len(other_functions) > 1:  # fix bug about anonymous classes
            continue
        elif len(other_functions) == 1:
            other_function = other_functions[0]
            if other_function != function:
                changed_functions.add((function, other_function))
        else:
            full_removed_functions.add((function,
                                        FunctionInfo(function.function_name,
                                                     other_blob.hash,
                                                     [])))

    return changed_functions, full_removed_functions


def compare_two_blobs(blob: BlobPositions,
                      other_blob: BlobPositions,
                      data_file: BinaryIO) -> Set[Tuple[FunctionInfo, FunctionInfo]]:

    changed_functions, deleted_functions = collect_changed_functions(blob, other_blob, data_file)
    _, added_functions = collect_changed_functions(other_blob, blob, data_file)

    added_functions = {(b, a) for a, b in added_functions}

    return changed_functions | deleted_functions | added_functions


def parse_dataset_line(line: str) -> (Message, List[Code2SeqPath]):
    [message, *function_body] = line.split(" ")
    function_body: List[Code2SeqPath] = [Code2SeqPath(path) for path in function_body]
    function_body[-1] = function_body[-1].strip()

    return Message(message), function_body
