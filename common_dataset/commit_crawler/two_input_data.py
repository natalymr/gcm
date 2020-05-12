import json
import os
from pathlib import Path
from typing import List

from tqdm import tqdm

from common_dataset.commit_crawler.tests_for_downloaded_data import get_repo_name
from common_dataset.commit_filter import first_splitter_filter, \
    filter_empty_messages, find_dobj_dependency_in_commit_message
from common_dataset.commit_filter import delete_key_words_in_commit_messages
from common_dataset.diffs import CommitDiff, FileDiffWithTwoInput
from common_dataset.commit_crawler.filter_downloaded_data import filter_by_clipping_commit_message_len, \
    is_there_dobj_dependency


# diff
def split_diff_in_two_input_and_filter_by_diff_len(commit: CommitDiff,
                                                   context_size_in_lines: int,
                                                   max_diff_len: int) -> bool:
    """
    Pipeline:
    1. delete useless diff diff lines
    2. convert to diff with two inputs
    3. code tokenize
    4. CamelCase tokenize
    5. diff size filter
    """
    total_tokens_number: int = 0
    for i, file_diff in enumerate(commit.changed_java_files):
        if not file_diff.diff_body:  # empty change file
            return False
        file_diff.delete_useless_git_diff_output()

        # change common diff with diff with two inputs, keep only needed number of context around
        commit.changed_java_files[i] = FileDiffWithTwoInput.from_FileDiff_keep_needed_context(file_diff,
                                                                                              context_size_in_lines)
        total_tokens_number += commit.changed_java_files[i].tokenize_both_diff_body()
        commit.changed_java_files[i].tokenize_camel_case_both_diffs()
    return total_tokens_number <= max_diff_len


def filter_commits(raw_dir: Path, processed_dir: Path,
                   min_message_tokens: int, max_message_tokens: int,
                   loc: int, max_diff_tokens: int) -> None:
    all_downloaded_files: List[str] = os.listdir(raw_dir)
    repo_names: List[str] = [get_repo_name(f, '.commits') for f in all_downloaded_files if f.endswith('.commits.logs')]
    error_file: Path = processed_dir.joinpath('errors.log')
    total_repos_count: int = len(repo_names)
    total_commits_count, filtered_commits_count = 0, 0

    with tqdm(total=total_repos_count) as pbar:
        for repo_name in repo_names:
            pbar.update(1)
            input_diff: Path = raw_dir.joinpath(repo_name + '.diffs.LOC_10.json')
            output_diff: Path = processed_dir.joinpath(repo_name + '.filtered_diff.json')

            try:
                with open(input_diff, 'r') as f:
                    commits = json.load(f)
                commits = [CommitDiff.from_dict(commit) for commit in commits]
                total_commits_count += len(commits)
                # diff
                commits = filter(lambda c: split_diff_in_two_input_and_filter_by_diff_len(c, loc, max_diff_tokens),
                                 commits)

                # messages
                commits = map(first_splitter_filter, commits)  # must be first
                commits = map(lambda c: delete_key_words_in_commit_messages(c, 'issue <num>'), commits)
                commits = filter(lambda c: filter_by_clipping_commit_message_len(c, min_message_tokens, max_message_tokens),
                                 commits)
                commits = filter(filter_empty_messages, commits)  # must be last
                commits = map(find_dobj_dependency_in_commit_message, commits)
                commits = list(filter(is_there_dobj_dependency, commits))
                filtered_commits_count += len(commits)

                with open(output_diff, 'w') as output_f:
                    output_f.write(json.dumps(commits, default=CommitDiff.to_json, indent=2))
            except Exception as e:
                with open(error_file, 'a') as error_f:
                    error_f.write(f'We have as exception for this repo {repo_name}.\n')
                    error_f.write(f'{str(e)}.\n')

    print(f'Number of filtered commits is {filtered_commits_count}, Total commits count is {total_commits_count}')


if __name__ == '__main__':
    raw_dir: Path = Path('../../../new_data/raw_data/')
    processed_dir: Path = Path('../../../new_data/processed_data/two_inputs_200')
    # filter_commits(raw_dir, processed_dir, min_message_tokens=2, max_message_tokens=30, loc=2, max_diff_tokens=200)
