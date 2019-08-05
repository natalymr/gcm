import collections
import os
import pickle
import re
from typing import Dict, List, Tuple, Set, BinaryIO, TextIO,  Optional


def add_to_my_dict(key: str, value: Tuple[str, str, str], dict: Dict[str, List[Tuple[str, str, str]]]):
    if key in dict:
        dict[key].append(value)
    else:
        dict[key] = [value]


def parse_full_log(full_log: str) -> (Dict[str, List[Tuple[str, str, str]]], Set[str]):
    from get_commits import SEPARATOR
    blob_vs_messages = {}
    last_blobs = set()
    with open(full_log, 'r') as full_log_file:
        for line in full_log_file:
            line_list = line.split(SEPARATOR)
            commit, old_blob, new_blob, message = line_list[0], line_list[4], line_list[5], line_list[6]

            last_blobs.add(new_blob)
            try:
                if old_blob in blob_vs_messages:
                    last_blobs.remove(old_blob)
            except KeyError:
                pass
            add_to_my_dict(old_blob, (new_blob, message, commit), blob_vs_messages)
    return blob_vs_messages, last_blobs


def split_commit_message(message: str) -> List[str]:
    message = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', message)
    message_tokenized = re.findall(r"[A-Z]*[a-z]*|<num>", message)
    return [x.lower() for x in message_tokenized if x != '']


class FunctionInfo:
    def __init__(self, function_name: str, blob_hash: str, function_body: List[str] = None):
        self.function_name: str= function_name
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
                                       other_blob_positions: List[Tuple[int, int]]) -> Optional["FunctionInfo"]:
        for start, len in other_blob_positions:
            other_function = FunctionInfo.read_from_file(file, start, len)
            if self.function_name == other_function.function_name:
                return other_function

        return None

    def path_difference(self, other: "FunctionInfo") -> Set[str]:
        return (self.function_body.difference(other.function_body)).union(
            other.function_body.difference(self.function_body))


def clean_function_body_from_new_line_characters(paths: Set[str]) -> Set[str]:
    result: Set[str] = set()

    for path in paths:
        if '\n' in path:
            path = path[: path.index('\n')] + path[(path.index('\n') + 1):]
        result.add(path)

    return result


def compare_one_blob_vs_other(blob_positions: List[Tuple[int, int]],
                              other_blob_positions: List[Tuple[int, int]],
                              data_file: BinaryIO) -> Set[Tuple[FunctionInfo, FunctionInfo]]:
    changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]] = set()

    for start, len in blob_positions:
        function = FunctionInfo.read_from_file(data_file, start, len)
        other_function = function.find_method_with_the_same_name(data_file, other_blob_positions)
        if other_function:
            if other_function != function:
                changed_functions.add((function, other_function))

    return changed_functions


def compare_two_blobs(blob_positions: List[Tuple[int, int]],
                      other_blob_positions: List[Tuple[int, int]],
                      data_file: BinaryIO) -> Set[Tuple[FunctionInfo, FunctionInfo]]:

    changed_functions = compare_one_blob_vs_other(blob_positions, other_blob_positions, data_file)
    changed_functions |= compare_one_blob_vs_other(other_blob_positions, blob_positions, data_file)

    return changed_functions


def write_commit_message_and_path_difference(message: str,
                                             changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]],
                                             output_file: TextIO):
    message = split_commit_message(message)
    for function, other_function in changed_functions:
        diff_paths = function.path_difference(other_function)
        diff_paths = clean_function_body_from_new_line_characters(diff_paths)
        output_file.write(f"{'|'.join(message)} {' '.join(diff_paths)}\n")


def remove_method_name_with_commit_message_and_split_dataset(data: str,
                                                             full_log_dict: Dict[str, List[Tuple[str, str, str]]],
                                                             train: str, test: str, val: str,
                                                             splitted_dataset_file: str):
    print(data)
    global lasts_blobs
    with open(splitted_dataset_file, 'rb') as file:
        splitted_dataset = pickle.load(file)

    blobs_vs_positions: Dict[Tuple[str, str], List[Tuple[int, int]]] = collections.defaultdict(list)
    #  blobName: [(startPos, lineLen), (startPos, lineLen), ... ]
    with open(data, "r") as data_file:
        start_pos = 0
        for line in data_file:
            line_len = len(bytes(line.encode("utf-8")))
            functionInfo = FunctionInfo.parse_from_str(line)
            blobs_vs_positions[functionInfo.blob_hash].append((start_pos, line_len))
            start_pos += line_len

    print("Finish parsing file all.train")

    with open(train, 'w') as train_file, open(test, 'w') as test_file, open(val, 'w') as val_file:
        with open(data, "rb") as data_file:
            i = 0
            for blob, _ in blobs_vs_positions.copy().items():
                try:
                    for other_blob, commit_message, commit in full_log_dict[blob]:
                        i += 1
                        if i % 20 == 0:
                            print(f"{i} from ~281185")
                        changed_functions = compare_two_blobs(blobs_vs_positions[blob],
                                                              blobs_vs_positions[other_blob],
                                                              data_file)
                        if commit in splitted_dataset['train']:
                            file = train_file
                        elif commit in splitted_dataset['test']:
                            file = test_file
                        else:
                            file = val_file
                        write_commit_message_and_path_difference(commit_message, changed_functions, file)

                except KeyError:
                    if blob not in lasts_blobs:
                        print(f"Smth went wrong for {blob}")


def main():
    global lasts_blobs
    train_data_path = "/Users/natalia.murycheva/Documents/code2seq/s.12280.aurora.train.raw.txt"
    test_data_path = "/Users/natalia.murycheva/Documents/code2seq/s.12280.aurora.test.raw.txt"
    val_data_path = "/Users/natalia.murycheva/Documents/code2seq/s.12280.aurora.val.raw.txt"
    datasets_parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    datasets = ["aurora"]
    dicts = []
    for data in datasets:
        full_log_file = f"gcm_{data}_full_log_for_train_commits.log"
        full_log_file = os.path.join(datasets_parent_dir, full_log_file)

        dict, lasts_blobs = parse_full_log(full_log_file)
        dicts.append(dict)
    merged_full_log = {k: v for d in dicts for k, v in d.items()}
    tmp_file = "/Users/natalia.murycheva/Documents/code2seq/tmp_for_my_script"
    # for data in [train_data_path, test_data_path, val_data_path]:
    splitted_commits = f"aurora_splitted_commits_set_train_val_test.pickle"
    splitted_commits = os.path.join(datasets_parent_dir, splitted_commits)
    for data in ["/Users/natalia.murycheva/Documents/code2seq/s.12280.aurora.all.raw.txt"]:
        remove_method_name_with_commit_message_and_split_dataset(data, merged_full_log,
                                                                 train_data_path, test_data_path, val_data_path,
                                                                 splitted_commits)


if __name__ == '__main__':
    main()
