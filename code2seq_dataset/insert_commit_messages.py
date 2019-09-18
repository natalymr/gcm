from code2seq_dataset.common import clean_function_body_from_new_line_characters
from code2seq_dataset.common import get_blobs_positions, parse_full_log
from code2seq_dataset.common import split_commit_message, compare_two_blobs
from code2seq_dataset.info_classes import FunctionInfo, NextBlobMetaInfo, BlobInfo, dataset_line
from pathlib import Path
import pickle
from typing import Dict, DefaultDict, Mapping, List, Tuple, Set, TextIO


def write_commit_message_and_path_difference(message: str,
                                             changed_functions: Set[Tuple[FunctionInfo, FunctionInfo]],
                                             output_file: TextIO):
    message: List[str] = split_commit_message(message)
    for function, other_function in changed_functions:
        diff_paths: Set[str] = function.path_difference(other_function)
        diff_paths: Set[str] = clean_function_body_from_new_line_characters(diff_paths)
        output_file.write(dataset_line.substitute(target_message='|'.join(message),
                                                  paths=' '.join(diff_paths)))


def remove_method_name_with_commit_message_and_split_dataset(data: Path,
                                                             blobs_history: Mapping[str, List[NextBlobMetaInfo]],
                                                             train: Path, test: Path, val: Path,
                                                             splitted_dataset_file: Path):
    with open(splitted_dataset_file, 'rb') as sdf:
        splitted_dataset: Dict[str, Set[str]] = pickle.load(sdf)
    blobs_positions: DefaultDict[str, List[Tuple[int, int]]] = get_blobs_positions(data)
    print("Finish parsing file .all.")

    with open(train, 'w') as train_f, open(test, 'w') as test_f, open(val, 'w') as val_f, open(data, 'rb') as data_f:
        i = 0

        for blob, next_blobs in blobs_history.items():
            for commit, next_blob, message in next_blobs:
                i += 1
                if i % 20 == 0:
                    print(f"{i}")
                    changed_functions = compare_two_blobs(BlobInfo(blob, blobs_positions[blob]),
                                                          BlobInfo(next_blob, blobs_positions[next_blob]),
                                                          data_f)
                    if commit in splitted_dataset['train']:
                        output_f = train_f
                    elif commit in splitted_dataset['test']:
                        output_f = test_f
                    elif commit in splitted_dataset['val']:
                        output_f = val_f
                    else:
                        continue

                    write_commit_message_and_path_difference(message, changed_functions, output_f)


def main():
    dataset_name = "aurora"
    datasets_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")
    full_log_file: Path = datasets_dir.joinpath(f"gcm_{dataset_name}_full.log")
    splitted_commits = datasets_dir.joinpath(f"{dataset_name}_splitted_commits_set_train_val_test.pickle")

    all_paths_file: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.raw.txt")
    train_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.correct.train.raw.txt")
    test_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.correct.test.raw.txt")
    val_data_path: Path = Path("/Users/natalia.murycheva/Documents/code2seq/aurora.correct.val.raw.txt")

    blobs_history: DefaultDict[str, List[NextBlobMetaInfo]] = parse_full_log(full_log_file)
    remove_method_name_with_commit_message_and_split_dataset(all_paths_file,
                                                             blobs_history,
                                                             train_data_path, test_data_path, val_data_path,
                                                             splitted_commits)


if __name__ == '__main__':
    main()
