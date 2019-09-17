from code2seq_dataset.common import clean_function_body_from_new_line_characters
from code2seq_dataset.common import compare_two_blobs, parse_full_log, get_blobs_positions
from code2seq_dataset.info_classes import FunctionInfo, BlobInfo, NextBlobMetaInfo
from pathlib import Path
from typing import Mapping, List, Tuple, Set, TextIO, DefaultDict


def write_meta_info_and_path_diff(commit: str,
                                  changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]],
                                  output_file: TextIO):
    for function, other_function in changed_functions:
        diff_paths: Set[str] = function.path_difference(other_function)
        diff_paths: Set[str] = clean_function_body_from_new_line_characters(diff_paths)

        output_file.write(f"{commit}|{function.blob_hash}|{other_function.blob_hash}|{function.function_name} "
                          f"{' '.join(diff_paths)}\n")


def remove_method_name_with_meta_info(data: Path, blobs_history: Mapping[str, List[NextBlobMetaInfo]], output: Path):
    blobs_positions: DefaultDict[str, List[Tuple[int, int]]] = get_blobs_positions(data)

    with open(output, 'w') as output_file, open(data, 'rb') as data_file:
        for blob, next_blobs in blobs_history.items():
            for commit, next_blob, _ in next_blobs:
                changed_functions = compare_two_blobs(BlobInfo(blob, blobs_positions[blob]),
                                                      BlobInfo(next_blob, blobs_positions[next_blob]),
                                                      data_file)
                write_meta_info_and_path_diff(commit, changed_functions, output_file)


def main():
    dataset_name = "aurora"
    datasets_parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")
    full_log_file = datasets_parent_dir.joinpath(f"gcm_{dataset_name}_full.log")
    data_file: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.raw.txt")
    output_file: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.test.raw.txt")

    blobs_history: DefaultDict[str, List[NextBlobMetaInfo]] = parse_full_log(full_log_file)
    print(f"FULL LOG size = {len(blobs_history)}")
    total_size: int = 0
    for key in blobs_history:
        total_size += len(blobs_history[key])
    print(f"Total number of blobs = {total_size}")

    remove_method_name_with_meta_info(data_file, blobs_history, output_file)


if __name__ == '__main__':
    main()
