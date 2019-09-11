from code2seq_dataset.info_classes import FunctionInfo, BlobInfo
import os
from typing import Dict, List, Tuple, Set, TextIO
from code2seq_dataset.common import clean_function_body_from_new_line_characters
from code2seq_dataset.common import compare_two_blobs
from code2seq_dataset.common import parse_full_log


def write_meta_info_and_path_difference(commit: str,
                                        changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]],
                                        output_file: TextIO):
    for function, other_function in changed_functions:
        diff_paths = function.path_difference(other_function)
        diff_paths = clean_function_body_from_new_line_characters(diff_paths)

        output_file.write(f"{commit}|{function.blob_hash}|{other_function.blob_hash}|{function.function_name} "
                          f"{' '.join(diff_paths)}\n")


def remove_method_name_with_commit_message_and_split_dataset(data: str,
                                                             blobs_history: Dict[str, List[Tuple[str, str, str]]],
                                                             test: str):
    blobs_vs_positions = ""

    with open(test, 'w') as test_file, open(data, "rb") as data_file:
        for blob in blobs_vs_positions:
            try:
                for other_blob, _, commit in blobs_history[blob]:

                    changed_functions = compare_two_blobs(BlobInfo(blob, blobs_vs_positions[blob]),
                                                          BlobInfo(other_blob, blobs_vs_positions[other_blob]),
                                                          data_file)
                    write_meta_info_and_path_difference(commit, changed_functions, test_file)

            except KeyError:
                if blob not in lasts_blobs:
                    print(f"Smth went wrong for {blob}")


def main():
    global lasts_blobs
    test_data_path = "/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.test.raw.txt"
    datasets_parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    dataset_name = "aurora"
    full_log_file = f"gcm_{dataset_name}_full.log"
    full_log_file = os.path.join(datasets_parent_dir, full_log_file)

    blobs_history, lasts_blobs = parse_full_log(full_log_file)
    print(f"len FULL LOG {len(blobs_history)}")
    total_size = 0
    for key in blobs_history:
        total_size += len(blobs_history[key])

    print(f"total size {total_size}")

    # for data in [train_data_path, test_data_path, val_data_path]:
    for data in ["/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.raw.txt"]:
        remove_method_name_with_commit_message_and_split_dataset(data,
                                                                 blobs_history,
                                                                 test_data_path)


if __name__ == '__main__':
    main()
