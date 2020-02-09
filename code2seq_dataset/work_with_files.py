import os
from pathlib import Path
from shutil import copyfile
from typing import List, Mapping, Set

from code2seq_dataset.common import parse_dataset_line
from code2seq_dataset.global_vars import Message, Code2SeqPath


def add_java_in_file_name():
    dir_name: str = '/Users/natalia.murycheva/PycharmProjects/new_data/raw_data/blobs'
    all_files: List[str] = os.listdir(dir_name)
    for file in all_files:
        if not file.endswith(".java"):
            old_name = os.path.join(dir_name, file)
            new_name = os.path.join(dir_name, file + ".java")
            os.rename(old_name, new_name)


def remove_java_in_file_name():
    dir_name: str = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/camel_blobs"
    all_files: List[str] = os.listdir(dir_name)

    for file in all_files:
        if file.endswith(".java"):
            old_name = os.path.join(dir_name, file)
            new_name = os.path.join(dir_name, file[:len(file) - len(".java")])
            os.rename(old_name, new_name)


def copy_blobs():
    dir_name = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/intellij_blobs"
    other_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/intellij_test"
    all_files = os.listdir(dir_name)
    i = 0
    for file in all_files:
        i += 1
        src = os.path.join(dir_name, file)
        dst = os.path.join(other_dir, file)
        if i < 3500:
            copyfile(src, dst)
        else:
            break


def test():
    dir_name = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/intellij_blobs"
    all_files = os.listdir(dir_name)
    i = 0
    for file in all_files:
        if file.endswith(".java"):
            i += 1

    print(f"All files {i}")


def split_blobs_in_several_dirs(src_dir: str, dst_root_dir: str, num_parts: int):
    all_files: List[str] = os.listdir(src_dir)
    part_size: int = len(all_files) // num_parts
    k = 0

    for i in range(num_parts):
        print(f"Start {i}")
        files_to_copy = all_files[i * part_size: (i + 1) * part_size]
        if i == num_parts - 1:
            files_to_copy = all_files[i * part_size:]
        # make a dir
        dst_dir = os.path.join(dst_root_dir, str(i))
        for file in files_to_copy:
            k += 1
            if k % 100 == 0:
                print(f"{k}")
            old_path = os.path.join(src_dir, file)
            new_path = os.path.join(dst_dir, file)
            copyfile(old_path, new_path)

    check_all_files_is_copied(
        src_dir,
        dst_root_dir,
        num_parts
    )


def check_all_files_is_copied(src_dir: str, dst_root_dir: str, num_parts: int):
    all_files = set(os.listdir(src_dir))
    copied_files = set()
    for i in range(num_parts):
        new_dir = os.path.join(dst_root_dir, str(i))
        copied_files |= set(os.listdir(new_dir))

    if all_files != copied_files:
        print("Smth went wrong")


def concat_files(dst_file: str, input_files: List[str]):
    with open(dst_file, "w") as output:
        for input_file in input_files:
            print(input_file)
            with open(input_file, "r") as f:
                for line in f:
                    output.write(line)


def delete_no_message_commits(input_file: str, tmp_file: str):
    from shutil import copyfile
    with open(input_file, "r") as in_f, open(tmp_file, "w") as out_f:
        for line in in_f:
            if not line.startswith("no|message"):
                out_f.write(line)
    copyfile(tmp_file, input_file)


def analyze_train_file(input_file: str):
    with open(input_file, 'r') as f:
        for line in f:
            l = line.split(" ")
            print(l[1])
            print(l[2])
            print(l[999])
            print(len(l))


def copy_blob_in_needed_dirs(data_dict: Mapping[str, List[str]], blobs_dir: Path, output_dir_parent: Path):
    for set, blobs in data_dict.items():
        for blob in blobs:
            src = blobs_dir.joinpath(blob)
            dst = output_dir_parent.joinpath(set).joinpath(blob + ".java")
            copyfile(src, dst)


def read_dataset_file(file: Path) -> Set[str]:
    result: Set[str] = set()

    with open(file, 'r') as f:
        for line in f:
            result.add(line)

    return result


def datasets_intersection():
    dataset_small_dir: Path = Path("/Users/natalia.murycheva/Documents/code2seq/data/camel_small")
    dataset_big_dir: Path = Path("/Users/natalia.murycheva/Documents/code2seq/data/camel")
    train_small: Path = dataset_small_dir.joinpath("camel.train.c2s")
    train_big: Path = dataset_big_dir.joinpath("camel.train.all.c2s")
    val_small: Path = dataset_small_dir.joinpath("camel.val.c2s")
    val_big: Path = dataset_big_dir.joinpath("camel.val.c2s")
    test_small: Path = dataset_small_dir.joinpath("camel.test.c2s")
    test_big: Path = dataset_big_dir.joinpath("camel.test.c2s")

    small_dataset_lines: Set[str] = set()
    big_dataset_lines: Set[str] = set()

    small_dataset_lines |= read_dataset_file(train_small)
    small_dataset_lines |= read_dataset_file(val_small)
    small_dataset_lines |= read_dataset_file(test_small)

    big_dataset_lines |= read_dataset_file(train_big)
    big_dataset_lines |= read_dataset_file(val_big)
    big_dataset_lines |= read_dataset_file(test_big)

    print(f"Small size = {len(small_dataset_lines)}")
    print(f"Big size = {len(big_dataset_lines)}")
    print(f"inter len = {len(small_dataset_lines & big_dataset_lines)}")


def read_dataset_messages(file: Path) -> Set[Message]:
    result: Set[Message] = set()

    with open(file, 'r') as f:
        for line in f:
            message, _ = parse_dataset_line(line)
            result.add(message)

    return result


def datasets_messages_intersection():
    dataset_small_dir: Path = Path("/Users/natalia.murycheva/Documents/code2seq/data/camel_small")
    dataset_big_dir: Path = Path("/Users/natalia.murycheva/Documents/code2seq/data/camel")
    train_small: Path = dataset_small_dir.joinpath("camel.train.c2s")
    train_big: Path = dataset_big_dir.joinpath("camel.train.all.c2s")
    val_small: Path = dataset_small_dir.joinpath("camel.val.c2s")
    val_big: Path = dataset_big_dir.joinpath("camel.val.c2s")
    test_small: Path = dataset_small_dir.joinpath("camel.test.c2s")
    test_big: Path = dataset_big_dir.joinpath("camel.test.c2s")

    small_dataset_lines: Set[Message] = set()
    big_dataset_lines: Set[Message] = set()

    small_dataset_lines |= read_dataset_messages(train_small)
    small_dataset_lines |= read_dataset_messages(val_small)
    small_dataset_lines |= read_dataset_messages(test_small)

    big_dataset_lines |= read_dataset_messages(train_big)
    big_dataset_lines |= read_dataset_messages(val_big)
    big_dataset_lines |= read_dataset_messages(test_big)

    print(f"Small size = {len(small_dataset_lines)}")
    print(f"Big size = {len(big_dataset_lines)}")
    print(f"inter len = {len(small_dataset_lines & big_dataset_lines)}")


def not_retrieved_blobs():
    failed_blobs_file: Path = Path('../../new_data/failed_blob.log')
    blobs_dir: Path = Path('../../new_data/raw_data/blobs')
    new_blobs_dir: Path = Path('../../new_data/raw_data/again_blobs')
    failed_blobs: List[str] = []
    with open(failed_blobs_file, 'r') as failed_blobs_f:
        for line in failed_blobs_f:
            line = line.strip('\n')
            failed_blobs.append(line)

    failed_blobs: Set[str] = set(failed_blobs)
    print(f'Number of failed blobs {len(failed_blobs)}')
    for blob in failed_blobs:
        src = blobs_dir.joinpath(f'{blob}.java')
        dst = new_blobs_dir.joinpath(f'{blob}.java')
        try:
            copyfile(src, dst)
        except FileNotFoundError as e:
            print(f'For blob {blob}, {str(e)}')


if __name__ == '__main__':
    add_java_in_file_name()
    # not_retrieved_blobs()
    # remove_java_in_file_name()
    # datasets_intersection()
    # datasets_messages_intersection()
    # copy_blobs()
    # split_blobs_in_several_dirs(
    #     "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/aurora_blobs",
    #     "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/aurora_blobs_splitted",
    #     5
    # )
    # concat_files(
    #     "/Users/natalia.murycheva/Documents/code2seq/aurora.all.test.raw.txt",
    #     [f"/Users/natalia.murycheva/Documents/code2seq/aurora.all.{i}.train.raw.txt"
    #      for i in range(5)]
    # )
    # concat_files(
    #     "/Users/natalia.murycheva/Documents/code2seq/union.val.raw.txt",
    #     ["/Users/natalia.murycheva/Documents/code2seq/intellij.val.raw.txt",
    #      "/Users/natalia.murycheva/Documents/code2seq/aurora.val.raw.txt"]
    # )

    # analyze_train_file("/Users/natalia.murycheva/Documents/code2seq/data/union/union.train.c2s")
