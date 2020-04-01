import collections
import difflib
import json
import re
import subprocess
from itertools import islice
from pathlib import Path
from typing import List, Dict, DefaultDict, TypeVar, Set
from dataclasses import dataclass, asdict

from code2seq_dataset.global_vars import Commit, Message, Blob, SEPARATOR
from code2seq_dataset.info_classes import FullLogLine
from common_dataset.logs import COMMON_SEP

new_line = ' <nl> '
add_symbol = '+'
delete_symbol = '-'
context_symbol = 'c'


# Copy-Paste
def get_commit_vs_blobs(full_log: Path, sep: str = SEPARATOR) -> Dict[Commit, List[FullLogLine]]:
    commit_vs_blobs: DefaultDict[Commit, List[FullLogLine]] = collections.defaultdict(list)
    with open(full_log, 'r', encoding='utf-8') as full_log_file:
        for line in full_log_file:
            if line.startswith("commit_hash"):
                continue
            full_log_line = FullLogLine.parse_from_line(line, separator=sep)
            commit_vs_blobs[full_log_line.commit].append(full_log_line)
    return commit_vs_blobs


@dataclass
class FileDiff:
    file_name: str
    status: str
    diff_body: List[str]

    @staticmethod
    def from_dict(input_):
        return FileDiff(file_name=input_['file_name'],
                        status=input_['status'],
                        diff_body=input_['diff_body'])

    def diff_body_in_one_line(self) -> str:
        global new_line
        return new_line.join([' '.join(line.split()) for line in self.diff_body])

    def delete_useless_git_diff_output(self):
        """
        Delete some useless output from git diff command,
        This lines will be deleted:
         'diff --git a / b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef b / 6f2f19b981c9fbc66138807b4d199851a2fd13e9'
         'index b5cb9bb9bf2 . . 6f2f19b981c 100644'
         '--- a / b5cb9bb9bf246fbd3f6bc957b5a538ea97de15ef'
         '+++ b / 6f2f19b981c9fbc66138807b4d199851a2fd13e9'
        """
        new_diff_body: List[str] = []
        for line in self.diff_body:
            # if '@@' in line:
            #     splitted_line = line.split('@@')
            #     if len(splitted_line) >= 3:
            #         line = splitted_line[2]
            #         new_diff_body.append(line)
            if not line.startswith('diff --git') and not line.startswith('index') and \
                    not line.startswith('---') and not line.startswith('+++') and not line.startswith('@@'):
                new_diff_body.append(line)
        self.diff_body = new_diff_body

    def keep_only_needed_number_of_line_around_changes(self, context_size_in_lines: int):
        """
        This function will keep only those line that are related to changes or its context
        :param context_size_in_lines: what number of lines will be saved around changes
        """
        mask: List[int] = [0] * len(self.diff_body)
        for i, line in enumerate(self.diff_body):
            if line.startswith('@@'):
                mask[i] = 1
            if line.startswith('+') or line.startswith('-'):
                min_ind = max(0, i - context_size_in_lines)
                max_ind = min(i + context_size_in_lines, len(self.diff_body) - 1)
                for j in range(min_ind, max_ind + 1):
                    mask[j] = 1
        self.diff_body = [self.diff_body[i] for i, v in enumerate(mask) if v]

    def tokenize_each_line_of_diff_body(self) -> int:
        new_diff_body: List[str] = []
        total_tokens_count: int = 0
        for line in self.diff_body:
            line = re.sub(r'\"([^\\\"]|\\.)*\"', 'str_variable', line)
            line = re.sub(r'(\w)(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
            line = re.sub(r'([^a-zA-Z0-9_ ])(?=\w)', r'\1 ', line)
            line = re.sub(r'([^a-zA-Z0-9_ ])(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
            line = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', line)
            if line == '' or line == ' ':
                continue
            splitted_line = line.split(' ')
            total_tokens_count += len(splitted_line)
            new_diff_body.append(' '.join(splitted_line))
        self.diff_body = new_diff_body
        return total_tokens_count

    def tokenize_camel_case(self):
        new_diff_body: List[str] = []
        for line in self.diff_body:
            line = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', line)).lower()
            new_diff_body.append(line)
        self.diff_body = new_diff_body

    @staticmethod
    def __my_git_diff(old_blob: Blob, new_blob: Blob, status: str, context_size: int, git_dir: Path) -> List[str]:
        if status == 'M' or status == 'R060':
            try:
                return subprocess.check_output(f'git diff {old_blob} {new_blob} -U{context_size}'.split(),
                                               cwd=git_dir,
                                               stderr=subprocess.PIPE).decode('utf-8').split('\n')
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []
        if status == 'A':
            try:
                lines = subprocess.check_output(f'git cat-file -p {new_blob}'.split(),
                                                cwd=git_dir).decode('utf-8').split('\n')
                return list(difflib.ndiff([], lines))
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []
        if status == 'D':
            try:
                lines = subprocess.check_output(f'git cat-file -p {old_blob}'.split(),
                                                cwd=git_dir).decode('utf-8').split('\n')
                return list(difflib.ndiff(lines, []))
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError {old_blob} -> {new_blob}")
                return []

    @staticmethod
    def from_git_diff(changed_files_log_line: FullLogLine, context_size: int, git_dir: Path) -> 'FileDiff':
        return FileDiff(file_name=changed_files_log_line.file,
                        status=changed_files_log_line.status,
                        diff_body=FileDiff.__my_git_diff(changed_files_log_line.old_blob,
                                                         changed_files_log_line.new_blob,
                                                         changed_files_log_line.status,
                                                         context_size,
                                                         git_dir))


@dataclass
class FileDiffWithTwoInput:
    file_name: str
    status: str
    diff_body_added: List[str]
    diff_body_deleted: List[str]
    diff_body_common: List[str]
    mask_add: List[str]
    mask_delete: List[str]

    @staticmethod
    def from_dict(input_) -> 'FileDiffWithTwoInput':
        return FileDiffWithTwoInput(file_name=input_['file_name'],
                                    status=input_['status'],
                                    diff_body_added=input_['diff_body_added'],
                                    diff_body_deleted=input_['diff_body_deleted'],
                                    diff_body_common=input_['diff_body_common'],
                                    mask_add=input_['mask_add'],
                                    mask_delete=input_['mask_delete'])

    @staticmethod
    def from_common_mask_to_specialized(common_mask: List[str],
                                        spec_symbol: str,
                                        context_size: int) -> List[str]:
        global add_symbol, delete_symbol, context_symbol

        result: List[str] = ['.'] * len(common_mask)
        if spec_symbol not in common_mask:
            return result

        def is_this_context_enough_close_to_spec_symbol(ind: int) -> bool:
            symbol_to_remove = add_symbol if spec_symbol == delete_symbol else delete_symbol
            any_left = any(
                key == spec_symbol
                for key in islice(
                    filter(lambda key: key != symbol_to_remove, reversed(common_mask[0:ind])),
                    context_size
                )
            )

            if any_left:
                return True

            any_right = any(
                key == spec_symbol
                for key in islice(
                    filter(lambda key: key != symbol_to_remove, islice(common_mask, ind + 1, None)),
                    context_size
                )
            )

            return any_right
            # # go to right
            # is_close_enough = True
            # context_count = 0
            # for k in range(ind + 1, len(common_mask)):
            #     if common_mask[k] == spec_symbol:
            #         return True
            #     elif common_mask[k] == context_symbol:
            #         context_count += 1
            #         if context_count == context_size or k == len(common_mask) - 1:
            #             is_close_enough = False
            #             break
            #     elif k == len(common_mask) - 1:
            #         is_close_enough = False
            # if ind == len(common_mask) - 1 and is_close_enough:
            #     is_close_enough = False
            #
            # # go to left
            # context_count = 0
            # for k in range(ind - 1, 0, -1):
            #     if common_mask[k] == spec_symbol:
            #         return True
            #     elif common_mask[k] == context_symbol:
            #         context_count += 1
            #         if context_count == context_size:
            #             if not is_close_enough:  # from right is not close enough
            #                 return False
            #     elif k == 0:
            #         return False

        for j, item in enumerate(common_mask):
            if item == spec_symbol:
                result[j] = spec_symbol
            elif item == context_symbol:
                if is_this_context_enough_close_to_spec_symbol(j):
                    result[j] = context_symbol

        return result

    @staticmethod
    def from_FileDiff_keep_needed_context(diff: FileDiff, context_size_in_lines: int = 2) -> 'FileDiffWithTwoInput':
        n: int = len(diff.diff_body)
        mask_common = ['.'] * n

        for i, line in enumerate(diff.diff_body):
            if line.startswith(add_symbol):
                mask_common[i] = add_symbol
            elif line.startswith(delete_symbol):
                mask_common[i] = delete_symbol
            else:
                mask_common[i] = context_symbol

        mask_delete = FileDiffWithTwoInput.from_common_mask_to_specialized(mask_common, delete_symbol,
                                                                           context_size=context_size_in_lines)
        mask_add = FileDiffWithTwoInput.from_common_mask_to_specialized(mask_common, add_symbol,
                                                                        context_size=context_size_in_lines)

        def get_from_common_diff_specialized(common_diff: List[str], mask: List[str]) -> List[str]:
            result: List[str] = []
            for j, m in enumerate(mask):
                if m != '.':
                    result.append(common_diff[j])
            return result

        return FileDiffWithTwoInput(
            file_name=diff.file_name,
            status=diff.status,
            diff_body_added=get_from_common_diff_specialized(diff.diff_body, mask_add),
            diff_body_deleted=get_from_common_diff_specialized(diff.diff_body, mask_delete),
            diff_body_common=diff.diff_body,
            mask_add=mask_add,
            mask_delete=mask_delete
        )

    @staticmethod
    def tokenize_line(line) -> (str, int):
        line = re.sub(r'\"([^\\\"]|\\.)*\"', 'str_variable', line)
        line = re.sub(r'(\w)(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
        line = re.sub(r'([^a-zA-Z0-9_ ])(?=\w)', r'\1 ', line)
        line = re.sub(r'([^a-zA-Z0-9_ ])(?=[^a-zA-Z0-9_ ])', r'\1 ', line)
        line = re.sub(r'[-+]?[0-9]*\.?[0-9]+', '<num>', line)

        return line, len(line.split())

    @staticmethod
    def from_mask_to_its_indexes(mask: List[str]) -> List[int]:
        result: List[int] = []
        for l, m in enumerate(mask):
            if m != '.':
                result.append(l)

        return result

    def tokenize_both_diff_body(self) -> int:
        total_tokens_count: int = 0
        considered_indexes: Set[int] = set()

        def process(elements: List[str], mask: List[str]):
            nonlocal total_tokens_count, considered_indexes
            mask_indexes = FileDiffWithTwoInput.from_mask_to_its_indexes(mask)
            for i, (line, orig_ind) in enumerate(zip(elements, mask_indexes)):
                tokenized_line, tokens_count = FileDiffWithTwoInput.tokenize_line(line)
                elements[i] = tokenized_line
                if orig_ind not in considered_indexes:
                    total_tokens_count += tokens_count
                    considered_indexes.add(orig_ind)

        process(self.diff_body_added, self.mask_add)
        process(self.diff_body_deleted, self.mask_delete)
        return total_tokens_count

        # added_indexes = FileDiffWithTwoInput.from_mask_to_its_indexes(self.mask_add)
        # for i, line, orig_ind in enumerate(zip(self.diff_body_added, added_indexes)):
        #     tokenized_line, tokens_count = FileDiffWithTwoInput.tokenize_line(line)
        #     self.diff_body_added[i] = tokenized_line
        #     if orig_ind not in considered_indexes:
        #         total_tokens_count += tokens_count
        #         considered_indexes.add(orig_ind)
        #
        # deleted_indexes = FileDiffWithTwoInput.from_mask_to_its_indexes(self.mask_delete)
        # for i, line, orig_ind in enumerate(zip(self.diff_body_deleted, deleted_indexes)):
        #     tokenized_line, tokens_count = FileDiffWithTwoInput.tokenize_line(line)
        #     self.diff_body_deleted[i] = tokenized_line
        #     if orig_ind not in considered_indexes:
        #         total_tokens_count += tokens_count
        #         considered_indexes.add(orig_ind)

    def tokenize_camel_case_both_diffs(self):
        def tokenize_diff(diff: List[str]) -> List[str]:
            new_diff: List[str] = []
            for line in diff:
                new_diff.append(re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', line)).lower())
            return new_diff

        self.diff_body_added = tokenize_diff(self.diff_body_added)
        self.diff_body_deleted = tokenize_diff(self.diff_body_deleted)

    # @staticmethod
    # def from_dict(input_):
    #     return FileDiff(file_name=input_['file_name'], status=input_['status'], diff_body=input_['diff_body'])
    #
    @staticmethod
    def diff_body_in_one_line(diff: List[str]) -> str:
        global new_line
        diff = list(filter(lambda line: line != ' ' and line != '+ ' and line != '- ', diff))
        return new_line.join([' '.join(line.split()) for line in diff])


MetaFileDiff = TypeVar('MetaFileDiff', FileDiff, FileDiffWithTwoInput)


@dataclass
class CommitDiff:
    commit: Commit
    message: Message
    author: str
    changed_java_files: List[MetaFileDiff]
    is_there_dobj: bool = False

    @staticmethod
    def to_json(self) -> None:
        return asdict(self)

    @staticmethod
    def from_dict(input_) -> 'CommitDiff':
        if 'diff_body_common' in input_['changed_java_files'][0]:
            return CommitDiff(commit=Commit(input_['commit']),
                              message=Message(input_['message']),
                              author=input_['author'],
                              changed_java_files=[FileDiffWithTwoInput.from_dict(file)
                                                  for file in input_['changed_java_files']],
                              is_there_dobj=input_['is_there_dobj'])
        else:
            return CommitDiff(commit=Commit(input_['commit']),
                              message=Message(input_['message']),
                              author=input_['author'],
                              changed_java_files=[FileDiff.from_dict(file) for file in input_['changed_java_files']],
                              is_there_dobj=input_['is_there_dobj'])

    def diff_in_one_line(self) -> str:
        global new_line
        if isinstance(self.changed_java_files[0], FileDiff):
            return new_line.join([
                changed_file.diff_body_in_one_line() for changed_file in self.changed_java_files
            ])

    def two_diffs_in_one_line(self) -> (str, str):
        global new_line
        if isinstance(self.changed_java_files[0], FileDiffWithTwoInput):
            return new_line.join([
                FileDiffWithTwoInput.diff_body_in_one_line(changed_file.diff_body_deleted)
                for changed_file in self.changed_java_files
            ]), new_line.join([
                FileDiffWithTwoInput.diff_body_in_one_line(changed_file.diff_body_added)
                for changed_file in self.changed_java_files
            ])


    def from_common_diff_to_two_diff(self):
        for i, file in enumerate(self.changed_java_files):
            self.changed_java_files[i] = FileDiffWithTwoInput.from_FileDiff_keep_needed_context(
                self.changed_java_files[i])


def get_all_diffs_per_commit(changed_files: List[FullLogLine], context_size: int, git_dir: Path) -> List[FileDiff]:
    return [
        FileDiff.from_git_diff(changed_file, context_size, git_dir)
        for changed_file in changed_files
    ]


def get_diffs(changed_files_log: Path, output: Path, context_size: int, git_dir: Path):
    commits_diffs: List[CommitDiff] = []
    commit_vs_blobs: Dict[Commit, List[FullLogLine]] = get_commit_vs_blobs(changed_files_log, sep=COMMON_SEP)
    print(len(commit_vs_blobs.keys()))
    i = 0
    for commit, changed_files in commit_vs_blobs.items():
        i += 1
        # if i % 1000 == 0:
        #     print(f"At {i}")
        # if i > 100:
        #     break
        message = Message(changed_files[0].message)
        author = changed_files[0].author
        files_diffs = get_all_diffs_per_commit(changed_files, context_size, git_dir)
        commits_diffs.append(CommitDiff(commit=commit, message=message, author=author, changed_java_files=files_diffs))
    with open(output, 'w', encoding='utf-8') as output_f:
        output_f.write(json.dumps(commits_diffs, default=CommitDiff.to_json, indent=2))


if __name__ == '__main__':
    git_dir_name: str = 'aurora'
    git_dir: Path = Path(f'/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage/{git_dir_name}')
    output_dir: Path = Path.cwd().parent.parent.joinpath('data').joinpath('raw_data').joinpath(git_dir_name)
    if not output_dir.exists():
        output_dir.mkdir()
    changed_files_log: Path = output_dir.joinpath('changed_java_files.log')
    context_size: int = 10
    all_diffs: Path = output_dir.joinpath(f'diffs_context_size_{context_size}.json')

    get_diffs(changed_files_log, all_diffs, context_size, git_dir)
