import os
from subprocess import call


def collect_statistics_no_msg_commits(com_com_log: str):
    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            line_list = line.split(";")
            cur_commit, message, date = line_list[1], line_list[2], line_list[4]


def collect_statistics_msg_frequency(com_com_log: str, output_file: str):
    msg_vs_count = {}
    total_commit_count = 0
    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue
            total_commit_count += 1
            line_list = line.split(";")
            message = line_list[2]
            if message in msg_vs_count:
                msg_vs_count[message] += 1
            else:
                msg_vs_count[message] = 1
    count_vs_message = {}
    for key, value in msg_vs_count.items():
        if value not in count_vs_message:
            count_vs_message[value] = [key]
        else:
            count_vs_message[value].append(key)
    counts_list = list(count_vs_message.keys())
    counts_list.sort(reverse=True)
    with open(output_file, 'w') as file:
        file.write(f"Total commit count: {total_commit_count}\n")
        file.write(f"Number of unique messages: {len(msg_vs_count)}\n")
        file.write(f"Message occurrence: {counts_list}\n")
        file.write(f"Number of occurence \t Number of messages \t Messages\n")
        for c in counts_list:
            file.write(f"{c} \t {len(count_vs_message[c])} \t {count_vs_message[c]}\n")


def create_com_com_log_file_for_one_author(com_com_log: str, git_dir: str):
    # logic
    call(f'echo "parent_commit_file_hash; current_commit_file_hash; message; author; date;" > {com_com_log}', shell=True)
    cd_command = f"cd {git_dir}"
    git_log_command = f'git log --pretty="%P;%H;%s;%an;%cd;" --author="builder" --branches --all'
    write_to_file_command = f" >> {com_com_log}"
    call(cd_command + " && " + git_log_command + write_to_file_command, shell=True)


if __name__ == "__main__":
    # values
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    tmp_file = os.path.join(parent_dir, "messages_statistics.txt")
    builder_com_com_log = "builder_com_com_msg_author_date.log"
    builder_com_com_log = os.path.join(parent_dir, builder_com_com_log)
    builder_statistics_file = os.path.join(parent_dir, "builder_messages_statistics.txt")
