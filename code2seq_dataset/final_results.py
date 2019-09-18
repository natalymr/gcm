from code2seq_dataset.info_classes import PredictedResults, FullLogLine
from pathlib import Path
from string import Template
from typing import DefaultDict, Tuple, List, Set
import collections


def parse_result_file(results: Path) -> DefaultDict[str, List[Tuple[int, int]]]:
    commits_vs_positions: DefaultDict[str, List[Tuple[int, int]]] = collections.defaultdict(list)
    start_pos: int = 0

    with open(results, 'r') as results_file:
        for line in results_file:
            line_len: int = len(bytes(line.encode("utf-8")))
            predicted_result_line: PredictedResults = PredictedResults.parse_from_str(line)
            if predicted_result_line:
                commits_vs_positions[predicted_result_line.commit].append((start_pos, line_len))
            start_pos += line_len

    return commits_vs_positions


def insert_results_in_common_csv(full_log: Path, code2seq: Path, output: Path):
    processed_commits: Set[str] = set()
    i, k = 0, 0

    commits_vs_positions = parse_result_file(code2seq)
    print(f"Finishe parse file {code2seq}")
    output_line_template = Template('$commit$sep$file$sep$status$sep'
                                    '$original_message$sep$function_name$sep$predicted_message$sep\n')

    with open(full_log, 'r') as full_log_file, open(output, 'w') as output_file, open(code2seq, 'rb') as code2seq_file:
        for line in full_log_file:
            i += 1
            if i % 20 == 0:
                print(f"{i} line in full log")
            if line.startswith("commit_hash"):
                continue

            full_log_line: FullLogLine = FullLogLine.parse_from_line(line)
            message: str = full_log_line.message

            if message.startswith("This commit was manufactured by cvs2svn"):
                if full_log_line.commit not in processed_commits:
                    output_file.write(output_line_template.substitute(commit=full_log_line.commit,
                                                                      file=full_log_line.file_,
                                                                      status=full_log_line.status,
                                                                      original_message=message,
                                                                      function_name="",
                                                                      predicted_message="",
                                                                      sep="^"))
                    processed_commits.add(full_log_line.commit)
                else:
                    output_file.write(output_line_template.substitute(commit="",
                                                                      file=full_log_line.file_,
                                                                      status=full_log_line.status,
                                                                      original_message=message,
                                                                      function_name="",
                                                                      predicted_message="",
                                                                      sep="^"))
                continue

            predicted_results: List[PredictedResults] = PredictedResults.find_results_for_commit_and_blobs(
                commits_vs_positions[full_log_line.commit],
                full_log_line.old_blob,
                full_log_line.new_blob,
                code2seq_file
            )

            if message == "no message" or message == "*** empty log message ***":
                message = " "
            if len(predicted_results) == 0:
                if full_log_line.commit not in processed_commits:
                    output_file.write(output_line_template.substitute(commit=full_log_line.commit,
                                                                      file=full_log_line.file_,
                                                                      status=full_log_line.status,
                                                                      original_message=message,
                                                                      function_name="",
                                                                      predicted_message="",
                                                                      sep="^"))
                    processed_commits.add(full_log_line.commit)
                else:
                    output_file.write(output_line_template.substitute(commit="",
                                                                      file=full_log_line.file_,
                                                                      status=full_log_line.status,
                                                                      original_message=message,
                                                                      function_name="",
                                                                      predicted_message="",
                                                                      sep="^"))
            else:
                for prediction in predicted_results:
                    k += 1
                    if k % 10 == 0:
                        print(f"write {k} generated annotation")
                    if full_log_line.commit not in processed_commits:
                        output_file.write(output_line_template.substitute(commit=full_log_line.commit,
                                                                          file=full_log_line.file_,
                                                                          status=full_log_line.status,
                                                                          original_message=message,
                                                                          function_name=prediction.function_name,
                                                                          predicted_message=prediction.predicted_message,
                                                                          sep="^"))
                    else:
                        output_file.write(output_line_template.substitute(commit="",
                                                                          file=full_log_line.file_,
                                                                          status=full_log_line.status,
                                                                          original_message=message,
                                                                          function_name=prediction.function_name,
                                                                          predicted_message=prediction.predicted_message,
                                                                          sep="^"))
                    processed_commits.add(full_log_line.commit)


def main():
    datasets_parent_dir: Path = Path("/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage")
    full_log_file: Path = datasets_parent_dir.joinpath("gcm_aurora_full.log")
    results_file: Path = Path("/Users/natalia.murycheva/Documents/code2seq/result.aurora.correct.txt")
    output_file: Path = Path("/Users/natalia.murycheva/Documents/code2seq/result.aurora.correct.csv")

    insert_results_in_common_csv(full_log_file, results_file, output_file)


if __name__ == '__main__':
    main()
