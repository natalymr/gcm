import os
from typing import Dict, Tuple, List, Optional, BinaryIO
import collections

from code2seq_dataset.commit_message_tokenizer import SEPARATOR


def parse_result_file(results: str) -> Dict[str, List[Tuple[int, int]]]:
    commits_vs_positions: Dict[str, List[Tuple[int, int]]] = collections.defaultdict(list)

    with open(results, "r") as results_file:
        start_pos = 0
        for line in results_file:
            line_len = len(bytes(line.encode("utf-8")))

            line_list = line.split(",")
            if len(line_list) == 2:
                original, predicted = line_list[0], line_list[1]
                # original
                original_list = original.split(":")
                meta_info = original_list[1].split("|")
                if len(meta_info) > 2:
                    commit = meta_info[0]
                    commit = commit.strip()
                    commits_vs_positions[commit].append((start_pos, line_len))

            start_pos += line_len

    return commits_vs_positions


class PredictedResults:
    def __init__(self, commit: str, old_blob: str, new_blob: str, function_name: str, predicted_annotation: str):
        self.commit = commit
        self.old_blob = old_blob
        self.new_blob = new_blob
        self.function_name = function_name
        self.predicted_annotation = predicted_annotation

    @staticmethod
    def parse_from_str(line: str) -> Optional["PredictedResults"]:
        line_list = line.split(",")
        if len(line_list) == 2:
            original, predicted = line_list[0], line_list[1]

            # original
            original_list = original.split(":")
            meta_info = original_list[1].split("|")
            if len(meta_info) > 2:
                commit, old_blob, new_blob, function_name = meta_info[0], meta_info[1], meta_info[2], meta_info[3:]
                commit = commit.strip()

                # predicted
                predicted_list = predicted.split(":")
                annotation = predicted_list[1].strip("\n").split("|")

                return PredictedResults(commit,
                                        old_blob,
                                        new_blob,
                                        " ".join(function_name),
                                        " ".join(annotation))

        return None

    @staticmethod
    def read_from_line(file: BinaryIO, start: int, length: int) -> Optional["PredictedResults"]:
        file.seek(start, 0)
        decoded = file.read(length).decode("utf-8")
        return PredictedResults.parse_from_str(decoded)

    @staticmethod
    def find_results_for_commit_and_blobs(commit_predictions_positions: List[Tuple[int, int]],
                                          old_blob: str, new_blob: str,
                                          file: BinaryIO) -> List["PredictedResults"]:
        result = []

        for start, len in commit_predictions_positions:
            predicted: PredictedResults = PredictedResults.read_from_line(file, start, len)
            if predicted and predicted.old_blob == old_blob and predicted.new_blob == new_blob:
                result.append(predicted)

        return result


def insert_result_in_common_csv(full_log: str, code2seq_results: str, output: str):
    processed_commits = set()
    i, k = 0, 0

    commits_vs_positions = parse_result_file(code2seq_results)
    print(f"Finishe parse file {code2seq_results}")

    with open(full_log, 'r') as full_log_file, \
            open(output, 'w') as output_file, \
            open(code2seq_results, 'rb') as code2seq_results_file:
        for line in full_log_file:
            i += 1
            if i % 20 == 0:
                print(f"{i} line in full log")

            if line.startswith("commit_hash"):
                continue
            line_list = line.split(SEPARATOR)
            commit, author, status, file, old_blob, new_blob, message = line_list[0], line_list[1], line_list[2], \
                                                                        line_list[3], line_list[4], line_list[5], \
                                                                        line_list[6]

            if message.startswith("This commit was manufactured by cvs2svn"):
                if commit not in processed_commits:
                    output_file.write(f"{commit}^{file}^"
                                      f"{status}^{message}^^^\n")
                    processed_commits.add(commit)
                else:
                    output_file.write(f"^{file}^"
                                      f"{status}^{message}^^^\n")
                continue

            results: List[PredictedResults] = PredictedResults.find_results_for_commit_and_blobs(commits_vs_positions[commit],
                                                                                                 old_blob,
                                                                                                 new_blob,
                                                                                                 code2seq_results_file)

            if message == "no message" or message == "*** empty log message ***":
                message = " "
            if len(results) == 0:
                if commit not in processed_commits:
                    output_file.write(f"{commit}^{file}^"
                                      f"{status}^{message}^^^\n")
                    processed_commits.add(commit)
                else:
                    output_file.write(f"^{file}^"
                                      f"{status}^{message}^^^\n")
            else:
                for prediction in results:
                    k += 1
                    if k % 10 == 0:
                        print(f"write {k} generated annotation")
                    if commit not in processed_commits:
                        output_file.write(f"{commit}^{file}^"
                                          f"{status}^{message}^{prediction.function_name}^{prediction.predicted_annotation}^\n")
                    else:
                        output_file.write(f"^{file}^"
                                          f"{status}^{message}^{prediction.function_name}^{prediction.predicted_annotation}^\n")
                    processed_commits.add(commit)


def main():
    datasets_parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    full_log_file = f"gcm_aurora_full.log"
    full_log_file = os.path.join(datasets_parent_dir, full_log_file)

    results_file = "/Users/natalia.murycheva/Documents/code2seq/result.aurora.correct.txt"
    output_file = "/Users/natalia.murycheva/Documents/code2seq/result.aurora.correct.csv"

    insert_result_in_common_csv(full_log_file, results_file, output_file)


if __name__ == '__main__':
    main()
