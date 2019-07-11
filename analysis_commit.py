import os
from get_commits import parse_diff_tree_command


def collect_statistics_no_changing_commits(com_com_log: str, output_file: str, git_dir: str):
    author_vs_number = {}
    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue
            line_list = line.split()
            parent_commit, cur_commit, message, author = line_list[0], line_list[1], line_list[2], line_list[3]
            changed_files = parse_diff_tree_command(parent_commit, cur_commit, "tmp", git_dir)
            if not changed_files:
                if author not in author_vs_number:
                    author_vs_number[author] = 1
                else:
                    author_vs_number[author] += 1
    with open(output_file, 'w') as file:
        file.write("Author \t Number of commits that does not change any file")
        for author, number in author_vs_number.items():
            file.write(f"{author} \t {number}")


if __name__ == "__main__":
    # values
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    no_change_commit_log_file = f"gcm_{git_dir_name}_no_files_change_commits.log"
    no_change_commit_log_file = os.path.join(parent_dir, no_change_commit_log_file)
