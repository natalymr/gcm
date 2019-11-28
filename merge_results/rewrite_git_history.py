import sys
from typing import Dict

if __name__ == '__main__':
    commit_hash = sys.argv[1]
    commits_vs_message: Dict[str, str] = {}
    with open('/Users/natalia.murycheva/PycharmProjects/gitCommitMessageCollector/merge_results/merge_results_result_FINAL.csv', 'r') as f:
        for line in f:
            [commit, message, _] = line.split('^')
            commits_vs_message[commit] = message
    print(f'{commits_vs_message[commit_hash] if commit_hash in commits_vs_message else ""}\n\nOriginal Commit Hash: {commit_hash}')