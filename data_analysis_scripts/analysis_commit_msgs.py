from collections import OrderedDict
import itertools
import os
from typing import Dict, List


def invert_dict(input_dict: Dict[str, int]) -> Dict[int, List[str]]:
    result = dict()

    for key, value in input_dict.items():
        if value not in result:
            result[value] = [key]
        else:
            result[value].append(key)

    return result


def collect_statistics_msg_frequency(com_com_log: str, output_file: str):
    msg_vs_counts = {}
    total_commit_count = 0
    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue
            total_commit_count += 1
            line_list = line.split(";")
            message = line_list[2]
            message = message.lower()
            if message in msg_vs_counts:
                msg_vs_counts[message] += 1
            else:
                msg_vs_counts[message] = 1

    count_vs_msg = invert_dict(msg_vs_counts)
    counts_vs_msg_sorted = OrderedDict(sorted(count_vs_msg.items(), reverse=True))
    top_popular_msg = dict(itertools.islice(counts_vs_msg_sorted.items(), 0, 20))
    print(top_popular_msg)

    with open(output_file, 'w') as file:
        file.write(f"Total commit count: {total_commit_count}\n")
        file.write(f"Number of unique messages: {len(msg_vs_counts)}\n")
        file.write(f"Message occurrence: {counts_vs_msg_sorted.keys()}\n")
        file.write(f"Number of occurence \t Number of messages \t Messages\n")
        for occur_num, msgs in counts_vs_msg_sorted.items():
            file.write(f"{occur_num} \t {len(counts_vs_msg_sorted[occur_num])} \t {counts_vs_msg_sorted[occur_num]}\n")


def analyze_cleanup(com_com_log: str):
    cleanup_vs_author = {}
    total_commit_count = 0
    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue
            total_commit_count += 1
            line_list = line.split(";")
            message, author = line_list[2], line_list[3]
            if message == "cleanup":
                if author not in cleanup_vs_author:
                    cleanup_vs_author[author] = 1
                else:
                    cleanup_vs_author[author] += 1


    count_vs_author = invert_dict(cleanup_vs_author)
    counts_vs_author_sorted = dict(OrderedDict(sorted(count_vs_author.items(), reverse=True)))
    # top_popular_msg = dict(itertools.islice(counts_vs_msg_sorted.items(), 0, 20))
    for n, a in counts_vs_author_sorted.items():
        print("{:>3}: {}".format(n, a))


def analyze_msg_vs_author(com_com_log: str, output_file: str):
    msg_and_author_vs_number = {}
    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue
            line_list = line.split(";")
            message, author = line_list[2], line_list[3]
            message = message.lower()
            if (author, message) not in msg_and_author_vs_number:
                msg_and_author_vs_number[(author, message)] = 1
            else:
                msg_and_author_vs_number[(author, message)] += 1
    print("hell")

    # print(msg_and_author_vs_number)
    count_vs_author_msg = invert_dict(msg_and_author_vs_number)
    count_vs_author_msg_sorted = dict(OrderedDict(sorted(count_vs_author_msg.items(), reverse=True)))
    # top_popular_msg = dict(itertools.islice(counts_vs_msg_sorted.items(), 0, 20))
    with open(output_file, 'w') as file:
        for n, a in count_vs_author_msg_sorted.items():
            file.write("{:>3}: {}\n".format(n, a))


if __name__ == "__main__":
    # values
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    # git_dir_name = "aurora"
    git_dir_name = "intellij"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    all_commits_statistic_file = os.path.join(parent_dir, f"{git_dir_name}_messages_statistics.txt")
    msg_vs_author_file = os.path.join(parent_dir, f"{git_dir_name}_msg_vs_author.txt")

    collect_statistics_msg_frequency(com_com_log_file, all_commits_statistic_file)
    analyze_cleanup(com_com_log_file)
    analyze_msg_vs_author(com_com_log_file, msg_vs_author_file)

    # builder_com_com_log = "builder_com_com_msg_author_date.log"
    # builder_com_com_log = os.path.join(parent_dir, builder_com_com_log)
    # builder_statistics_file = os.path.join(parent_dir, "builder_messages_statistics.txt")
