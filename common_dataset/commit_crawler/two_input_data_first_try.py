import os
import json
import pickle
from pathlib import Path
from typing import List

from common_dataset.diffs import CommitDiff


def get_two_input_for_each_diff(filtered_diffs_path: Path, output_dir: Path) -> None:
    """
    We get all filtered diff, get all added, deleted lines and
    """
    filtered_diffs_files: List[str] = os.listdir(filtered_diffs_path)
    i = 0
    sets_all_diffs = set()
    results = []
    for diff_file in filtered_diffs_files:
        # print(diff_file)
        i += 1
        with open(filtered_diffs_path / diff_file, 'r') as f:
            commits = json.load(f)
        commits = [CommitDiff.from_dict(commit) for commit in commits]
        for commit in commits:
            commit.from_common_diff_to_two_diff()

        for commit in commits:
            for changed_file in commit.changed_java_files:
                if " ".join(changed_file.diff_body_common) not in sets_all_diffs:
                    results.append(changed_file)
                    sets_all_diffs.add(" ".join(changed_file.diff_body_common))

        # if i == 2:
        #     break
    print(len(sets_all_diffs))
    print(sets_all_diffs)
    print(Path.cwd())
    with open('../../common_dataset_tests/data_masks.pickle', 'rb') as f:
        expected_results = pickle.load(f)

    for r in results:
        # for exp_r in expected_results:
        #     if r.diff_body_common == exp_r.diff_body_common:
        #         if r.diff_body_added != exp_r.diff_body_added:
        #             print(f'Common actual: {" ".join(r.diff_body_common)}, expected: {" ".join(exp_r.diff_body_common)}')
        #             print('F: expected added mask:   {:>35}, actual: {:>35}'.format(" ".join(exp_r.diff_body_added),
        #                                                                             " ".join(r.diff_body_added)))
        #         if r.diff_body_deleted != exp_r.diff_body_deleted:
        #             print(f'Common actual: {" ".join(r.diff_body_common)}, expected: {" ".join(exp_r.diff_body_common)}')
        #             print('F: expected deleted mask: {:>35}, actual: {:>35}'.format(" ".join(exp_r.diff_body_deleted),
        #                                                                             " ".join(r.diff_body_deleted)))

        print('common: {:>30}, add: {:>30}, delete: {:>30}'.format(" ".join(r.diff_body_common),
                                                                   " ".join(r.diff_body_added),
                                                                   " ".join(r.diff_body_deleted)))


if __name__ == '__main__':
    """
    We get all filtered diffs and process data to get two input of data,
    for deleted: "-"
    for added: "+"
    and its contest
    """
    parent_dir: Path = Path('../../../new_data/processed_data')
    filtered_diffs_dir: Path = parent_dir.joinpath('filtered_diffs')
    two_input_dir: Path = parent_dir.joinpath('two_inputs')
    get_two_input_for_each_diff(filtered_diffs_dir, two_input_dir)
