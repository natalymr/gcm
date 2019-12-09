import json
import re
from typing import List
from pathlib import Path
from nltk.parse.corenlp import CoreNLPDependencyParser

from code2seq_dataset.common import split_commit_message
from common_dataset.diffs import CommitDiff, FileDiff

num = '<num>'


# messages
def first_splitter_filter(commit: CommitDiff) -> CommitDiff:
    commit.message = " ".join(split_commit_message(commit.message))
    return commit


def delete_key_words_in_commit_messages(commit: CommitDiff, key_word: str) -> CommitDiff:
    commit.message = commit.message.replace(key_word, "")
    return commit


def delete_pattern_in_commit_message(commit: CommitDiff, pattern: str) -> CommitDiff:
    commit.message = re.sub(pattern, '', commit.message)
    return commit


def filter_by_commit_message_len(commit: CommitDiff, max_len: int) -> bool:
    return len(split_commit_message(commit.message)) <= max_len


def filter_rollback_or_merge(commit: CommitDiff, keywords: str) -> bool:
    return keywords not in commit.message


def filter_by_pattern(commit: CommitDiff, pattern: str) -> bool:
    return not re.findall(pattern, commit.message)


def find_dobj_dependency_in_commit_message(commit: CommitDiff) -> CommitDiff:
    dep_parser = CoreNLPDependencyParser(url='http://localhost:9000')
    parse, = dep_parser.raw_parse(commit.message)
    commit.is_there_dobj = bool(parse.get_by_address(1)['deps']['dobj'])  # the first word is a verb and has dobj
    return commit


def filter_empty_messages(commit: CommitDiff) -> bool:
    return commit.message != " " and commit.message != ""


# diff
def process_diff_and_filter_by_diff_len(commit: CommitDiff, context_size_in_lines: int, max_diff_len: int) -> bool:
    """
    Pipeline:
    1. left only needed context
    2. code tokenize
    3. diff size filter
    4. CamelCase tokenize
    :param commit: item
    :param context_size_in_lines: number of lines before and after +/-
    :param max_diff_len: diff max len
    :return: is diff len <= max_diff_len
    """
    total_tokens_number: int = 0
    for file_diff in commit.changed_java_files:
        if not file_diff.diff_body:  # empty change file
            return False
        file_diff.delete_useless_git_diff_output()
        if file_diff.status == 'M':
            file_diff.keep_only_needed_number_of_line_around_changes(context_size_in_lines)
        total_tokens_number += file_diff.tokenize_each_line_of_diff_body()
        file_diff.tokenize_camel_case()
    return total_tokens_number <= max_diff_len


def filter_commit_messages(json_file: Path, max_message_len: int, context_size_in_lines: int,
                           max_diff_len: int, output_file: Path) -> None:
    with open(json_file, 'r') as f:
        commits = json.load(f)
    commits: List[CommitDiff] = [CommitDiff.from_dict(commit) for commit in commits]
    # commits = commits[200:500]
    print(f'At the beginning we have {len(commits)} commits.')

    # diff
    commits = list(filter(lambda c: process_diff_and_filter_by_diff_len(c, context_size_in_lines, max_diff_len),
                          commits))

    # messages
    commits = list(map(first_splitter_filter, commits))  # must be first
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'issue <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'camel <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'scr <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'idea <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'idea cr <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, '#<num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'junit <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'ruby <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'web <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'cpp <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'dbe <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'py <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'wi <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'ux <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'ea <num>'), commits))
    commits = list(map(lambda c: delete_key_words_in_commit_messages(c, 'oc <num>'), commits))
    commits = list(map(lambda c: delete_pattern_in_commit_message(c, 'provided by \\w+'), commits))
    commits = list(filter(lambda c: filter_by_pattern(c, r'upgrade [\w ]+ to version'), commits))
    commits = list(filter(lambda c: filter_by_commit_message_len(c, max_message_len), commits))
    # commits = list(filter(lambda c: filter_rollback_or_merge(c, 'this commit was manufactured by cvs2svn'), commits))
    commits = list(filter(filter_empty_messages, commits))  # must be last
    print('Start dobj finding')
    commits = list(map(find_dobj_dependency_in_commit_message, commits))
    print('Finished filtering messages')

    print(f'At the end we have {len(commits)} commits.')
    # write to output file
    with open(output_file, 'w') as output_f:
        output_f.write(json.dumps(commits, default=CommitDiff.to_json, indent=2))


if __name__ == '__main__':
    git_dir_name: str = 'intellij'
    input_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath('raw_data').joinpath(git_dir_name)
    all_diffs: Path = input_dir.joinpath('diffs_context_size_10.json')
    output_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath('processed_data').joinpath(git_dir_name)
    if not output_dir.exists():
        output_dir.mkdir()
    output_file: Path = output_dir.joinpath('diff_filtered.json')

    filter_commit_messages(all_diffs, 20, 2, 200, output_file)
