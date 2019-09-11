import re
import collections
from code2seq_dataset.info_classes import BlobInfo, FunctionInfo
from typing import Dict, List, Tuple, Set, BinaryIO
from code2seq_dataset.commit_message_tokenizer import SEPARATOR


def parse_full_log(full_log: str) -> (Dict[str, List[Tuple[str, str, str]]], Set[str]):
    blob_vs_messages: Dict[str, List[Tuple[str, str, str]]] = collections.defaultdict(list)
    last_blobs: Set[str] = set()

    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            if line.startswith("commit_hash"):
                continue
            line_list = line.split(SEPARATOR)
            commit, old_blob, new_blob, message = line_list[0], line_list[4], line_list[5], line_list[6]

            last_blobs.add(new_blob)
            try:
                if old_blob in blob_vs_messages:
                    last_blobs.remove(old_blob)
            except KeyError:
                pass
            blob_vs_messages[old_blob].append((new_blob, message, commit))

    return blob_vs_messages, last_blobs


def get_blobs_position_from_file(data_file: str) -> Dict[str, BlobInfo]:
    blobs_info: Dict[str, BlobInfo] = collections.defaultdict(list)
    #  blobName: [(startPos, lineLen), (startPos, lineLen), ... ]

    # @dataclass
    # class BlobInfo:
    #     hash: str
    #     functions_positions: List[Tuple[int, int]]

    with open(data_file, "r") as file:
        start_pos = 0
        for line in file:
            line_len = len(bytes(line.encode("utf-8")))
            function_info = FunctionInfo.parse_from_str(line)
            blobs_info[function_info.blob_hash].append(BlobInfo(function_info.blob_hash, start_pos, line_len))
            start_pos += line_len

    print("Finish parsing file .all.")

    return blobs_info


def split_commit_message(message: str) -> List[str]:
    message = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', message)
    message_tokenized = re.findall(r"[A-Z]*[a-z]*|<num>", message)
    return [x.lower() for x in message_tokenized if x != '']


def clean_function_body_from_new_line_characters(paths: Set[str]) -> Set[str]:
    result: Set[str] = set()

    for path in paths:
        if '\n' in path:
            path = path[: path.index('\n')] + path[(path.index('\n') + 1):]
        result.add(path)

    return result


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
