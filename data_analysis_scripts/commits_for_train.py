from keras.preprocessing.text import text_to_word_sequence
import os
import pickle


def get_commits_for_train(com_com_log: str, empty_com_file: str, output_file: str):
    needed_commits = set()
    with open(empty_com_file, 'rb') as file:
        empty_commits = pickle.load(file)

    with open(com_com_log, 'r') as com_com_log_file:
        total_commit_number = 0
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue

            line_list = line.split(";")
            cur_commit, message, author = line_list[1], line_list[2], line_list[3]
            if cur_commit in empty_commits:
                continue
            message = message.lower()
            if author == "builder":
                if message == "new version" or \
                        message == "build completed" or \
                        message == "build failed":
                    continue
            if message == "no message" or \
                    message == "*** empty log message ***":
                continue
            text_list = text_to_word_sequence(message)
            if text_list:
                total_commit_number += 1
                needed_commits.add(cur_commit)

    with open(output_file, 'wb') as file:
        pickle.dump(empty_commits, file)


if __name__ == "__main__":
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    no_files_change_commit_pickle_file = "no_files_change_commits.pickle"
    no_files_change_commit_pickle_file = os.path.join(parent_dir, no_files_change_commit_pickle_file)
    needed_commits_pickle_file = "needed_commits.pickle"
    needed_commits_pickle_file = os.path.join(parent_dir, needed_commits_pickle_file)

    get_commits_for_train(com_com_log_file, no_files_change_commit_pickle_file, needed_commits_pickle_file)
