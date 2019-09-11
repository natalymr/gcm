import os
import pickle
import re
from typing import Dict, List, Tuple, Set


def add_to_my_dict(key: str, value: Tuple[str, str, str], dict: Dict[str, List[Tuple[str, str, str]]]):
    if key in dict:
        dict[key].append(value)
    else:
        dict[key] = [value]


def parse_full_log(full_log: str) -> (Dict[str, List[Tuple[str, str, str]]], Set[str]):
    from commit_message_tokenizer import SEPARATOR
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


# def is_splittable(token: str) -> bool:
#     for i, letter in enumerate(token):
#         if letter.isupper() and i != 0:
#             return True
#
#     return False
#
#
# def split_by_sub_tokens(token: str) -> List[str]:
#     result = []
#     start = 0
#
#     for cur, letter in enumerate(token):
#         if letter.isupper() and cur != 0:
#             subtoken = token[start: cur]
#             result.append(subtoken.lower())
#             start = cur
#         if cur == len(token) - 1:
#             subtoken = token[start:]
#             result.append(subtoken.lower())
#
#     return result
#
#
# def all_letters_is_upper(token: str) -> bool:
#     for letter in token:
#         if letter.islower():
#             return False
#
#     return True


def split_commit_message(message: str) -> [str]:
    message_tokenized = re.findall(r"[A-Z]*[a-z]*", message)
    return [x.lower() for x in message_tokenized if x != '']
    # message_tokenized = text_to_word_sequence(message, lower=False)
    # for token in message_tokenized:
    #     if all_letters_is_upper(token):  #  скорее всего, это аббревиатура
    #         result.append(token.lower())
    #         continue
    #     if is_splittable(token):
    #         result.extend(split_by_sub_tokens(token))
    #     else:
    #         result.append(token.lower())


def find_method_path_by_blob_and_name(data_file: str, needed_blob: str, needed_method_name: str) -> str:
    with open(data_file, 'r') as file:
        for line in file:
            method_in_paths = line.split(" ")
            method_name = method_in_paths[0]
            method_name_list = method_name.split("|")
            blob_file_name = method_name_list[0][:-5]
            if needed_blob == blob_file_name:
                method_name = " ".join(method_name_list[1:])
                if needed_method_name == method_name:
                    return " ".join(method_in_paths[1:])
    return ""


def remove_method_name_with_commit_message_and_split_dataset(data_file: str,
                                                             full_log_dict: Dict[str, List[Tuple[str, str, str]]],
                                                             train: str, test: str, val: str,
                                                             splitted_dataset_file: str):
    global lasts_blobs
    print(data_file)
    with open(splitted_dataset_file, 'rb') as f:
        splitted_dataset = pickle.load(f)
    i = 0
    with open(train, 'w') as train_file, open(test, 'w') as test_file, open(val, 'w') as val_file:
        with open(data_file, 'r') as data:
            # для каждого метода в каждом блобе
            for line in data:
                i += 1
                if i % 20 == 0:
                    print(f"{i} from ~281185")
                cur_method_in_paths = line.split(" ")
                cur_method_name = cur_method_in_paths[0]
                cur_method_name_list = cur_method_name.split("|")
                cur_blob_name = cur_method_name_list[0][:-5]
                cur_method_name = " ".join(cur_method_name_list[1:])
                # смотрим, в какие блобы переходил этот блоб
                # и в этих "следующих" блобах смотрим
                try:
                    for commit_info in full_log_dict[cur_blob_name]:
                        new_blob_name, commit_message, commit_hash = commit_info[0], commit_info[1], commit_info[2]
                        if commit_message == "no message":
                            print(f"MESSAGE: {commit_message}")

                        # print(f"{cur_blob_name} {new_blob_name}")

                        cur_paths_str = " ".join(cur_method_in_paths[1:])
                        # ищем метод с таким же именем в каждом "следующем" блобе
                        # и сравниваем пути для этого метода (изменился ли метод во время коммита)
                        new_paths_str = find_method_path_by_blob_and_name(data_file, cur_blob_name, cur_method_name)
                        if cur_paths_str != new_paths_str:
                            # если изменился, значит надо записать разность путей + сообщение коммита
                            cur_paths_set = set(cur_method_in_paths[1:])
                            new_paths_set = set(new_paths_str.split(" "))
                            diff_paths_set = (cur_paths_set.difference(new_paths_set)).union(
                                new_paths_set.difference(cur_paths_set))
                            splitted_message = "|".join(split_commit_message(commit_message))
                            print(f"if: {commit_message} == {splitted_message}")
                            one_line_paths = set()
                            for path in diff_paths_set:
                                if '\n' in path:
                                    path = path[: path.index('\n')] + path[(path.index('\n') + 1):]
                                one_line_paths.add(path)

                            if commit_hash in splitted_dataset['train']:
                                train_file.write(f"{splitted_message} {' '.join(one_line_paths)}\n")
                            elif commit_hash in splitted_dataset['test']:
                                test_file.write(f"{splitted_message} {' '.join(one_line_paths)}\n")
                            elif commit_hash in splitted_dataset['val']:
                                val_file.write(f"{splitted_message} {' '.join(one_line_paths)}\n")

                except KeyError:
                    if cur_blob_name not in lasts_blobs:
                        print(f"Smth went wrong for {cur_blob_name}")

    # copyfile(tmp_file, data_file)


if __name__ == '__main__':
    train_data_path = "/Users/natalia.murycheva/Documents/code2seq/aurora.train.raw.txt"
    test_data_path = "/Users/natalia.murycheva/Documents/code2seq/aurora.test.raw.txt"
    val_data_path = "/Users/natalia.murycheva/Documents/code2seq/aurora.val.raw.txt"

    datasets_parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"

    datasets = ["aurora"]
    dicts = []
    all_blobs_pairs = []
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
    for data in ["/Users/natalia.murycheva/Documents/code2seq/aurora.all.train.raw.txt"]:
        remove_method_name_with_commit_message_and_split_dataset(data, merged_full_log,
                                                                 train_data_path, test_data_path, val_data_path,
                                                                 splitted_commits)
