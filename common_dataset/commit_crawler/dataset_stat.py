import json
import multiprocessing
import os
import subprocess
from collections import OrderedDict
from pathlib import Path, PosixPath
from typing import List, Dict
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

from tqdm import tqdm

from common_dataset.diffs import CommitDiff


class LocalGitRepository:
    def __init__(self, full_name: str, parent_dir: Path):
        self.full_name: str = full_name
        self.git_dir_name: str = full_name.split('/')[1]
        self.parent_repository: Path = parent_dir
        self.path: Path = parent_dir / self.git_dir_name

    def __enter__(self):
        subprocess.call(f'git clone https://github.com/{self.full_name}.git',
                        cwd=self.parent_repository,
                        shell=True)
        if self.path.exists():
            print('Finished cloning')
            return self.path

    def __exit__(self, type, value, traceback):
        subprocess.call(f'rm -rf {self.git_dir_name}',
                        cwd=self.parent_repository,
                        shell=True)


def get_repo_commits(git_dir: PosixPath) -> List[str]:
    return subprocess.check_output('git log --pretty=%H'.split(), cwd=git_dir).decode().split()


def get_commit_number(repo_name: str):
    global counter
    print(f'Start to process {repo_name}')
    dir_for_download_data = Path('../../../new_data/tmp')
    already_downloaded: Path = dir_for_download_data.joinpath('downloaded.log')
    with open(already_downloaded, 'a') as f:
        f.write(f'{repo_name}\n')

    with LocalGitRepository(repo_name, dir_for_download_data) as git_dir:
        try:
            commits_number = len(get_repo_commits(git_dir))
            with counter.get_lock():
                counter.value += commits_number
                print(f'### {counter.value}')
        except Exception as e:
            error_log: Path = dir_for_download_data.joinpath('errors.log')
            with open(error_log, 'a') as error:
                error.write(f'{repo_name}\n')
                error.write(f'{str(e)}\n')


def get_raw_commits_number():
    repos_file_json = Path('../../../new_data/repos.json')
    with open(repos_file_json, 'r') as f:
        repos = json.load(f)
    repos_names: List[str] = [repo['full_name'] for repo in repos['items']][:1000]
    print(repos_names)
    print(len(repos_names))

    with multiprocessing.Pool() as pool:
        pool.map(get_commit_number, repos_names)


def get_filtered_commits_count(processed_dir: Path) -> (Dict[str, float], int):
    total_filtered_commits_number = 0
    repo_vs_commits_number: Dict[str, int] = {}

    processed_files = os.listdir(processed_dir)
    for cur_repo_file in tqdm(processed_files):
        repo_name = cur_repo_file.split('.')[0]
        with open(processed_dir.joinpath(cur_repo_file), 'r') as f:
            commits = json.load(f)
        commits = [CommitDiff.from_dict(commit) for commit in commits]
        repo_vs_commits_number[repo_name] = len(commits)
        total_filtered_commits_number += len(commits)

    return repo_vs_commits_number, total_filtered_commits_number


def plot_percentile(data, percentile_start: int, percentile_end: int, percentile_number: int, title: str) -> None:
    percentiles = np.linspace(percentile_start, percentile_end, num=percentile_number)
    plt.figure(dpi=100, figsize=(12, 10))
    # plt.figure(figsize=(700 / 100, 600 / 100), dpi=100)
    ax = plt.gca()
    y_values = np.percentile(data, percentiles)
    plt.plot(percentiles, y_values,
             # color='black',
             linewidth=3)
    # x axis
    max_x_value = max(percentiles)
    plt.xticks(np.arange(0, max_x_value + 2, 5), fontsize=22)
    ax.set_xticks(np.arange(0, max_x_value + 3, 5), minor=False)
    ax.grid(axis='x', which='major', alpha=1)
    plt.xlabel('Percentile', fontsize=25)
    plt.xlim(percentile_start, percentile_end + 1)

    # y axis
    max_y_value = np.percentile(data, percentile_end)
    plt.yticks(np.arange(0, max_y_value + 2, 1), fontsize=12)
    # plt.yticks(np.arange(0, max_y_value + 0.1, 0.01), fontsize=22)
    ax.set_yticks(np.arange(0, max_y_value + 2, 0.5), minor=True)
    # ax.set_yticks(np.arange(0, max_y_value + 0.1, 0.002), minor=True)
    ax.set_yticks(np.arange(0, max_y_value + 3, 1), minor=False)
    # ax.set_yticks(np.arange(0, max_y_value + 0.1, 0.01), minor=False)
    ax.grid(axis='y', which='minor', alpha=0.4)
    ax.grid(axis='y', which='major', alpha=1)
    plt.ylim(0, max_y_value + 1)
    plt.ylabel('% in final dataset', fontsize=22)

    # fill
    ax.fill_between(percentiles, y_values, [0 for i in range(percentile_number)],
                    alpha=0.1)

    plt.title(title, fontsize=27)
    plt.show()


def plot_hist(data, title: str) -> None:
    # get values for plot
    bins = np.append([np.arange(0, 0.15, 0.05)], [np.array(22)])
    print(bins)
    histo_data = np.histogram(data, bins)[0]
    histo_data_percents = histo_data / histo_data.sum()

    shift = (bins[1] - bins[0]) / 2
    bars_x_coord = bins[:-1] + shift
    bars_x_coord[-1] = bars_x_coord[-2] + 2* shift

    print(bars_x_coord)
    print(len(bars_x_coord))
    print(len(histo_data_percents))
    # plt.figure(figsize=(600 / 100, 400 / 100), dpi=100)
    plt.figure(dpi=100, figsize=(12, 8))
    ax = plt.gca()
    ax.yaxis.set_major_formatter(PercentFormatter(1))

    width = 0.85 * 2 * shift
    rects = ax.bar(bars_x_coord, histo_data_percents,
                   width=width, alpha=0.65, linewidth=1.5,
                   color='#4275D8', edgecolor='black', align='center')
    # n = plt.hist(data, bins=bins,
    #              weights=np.ones(len(data)) / len(data),
    #              edgecolor='black',
    #              rwidth=0.9, color='cornflowerblue', alpha=0.65)
    xticks = bins[:-1] + shift
    print(xticks)
    print(len(xticks))
    print(bins)
    xlabels = ['0-0.05', '0.05-0.1', '>0.1']
    print(len(xlabels))
    plt.xticks(xticks, xlabels, fontsize=22)
    ax.grid(axis='y', which='minor', alpha=0.3)
    ax.grid(axis='y', which='major', alpha=0.7)
    plt.yticks(np.arange(0, max(histo_data_percents) + 0.07, 0.1), fontsize=20)
    # ax.set_yticks(np.arange(0, max(histo_data_percents) + 0.02, 0.01), minor=True)
    # ax.set_yticks(, minor=False)
    plt.title(title, fontsize=25)
    plt.show()


def get_main_stat(raw_dir: Path, processed_dir_100: Path, processed_dir_200: Path, output_file: Path) -> None:
    repos_file_json = Path('../../../new_data/repos.json')

    with open(repos_file_json, 'r') as f:
        repos = json.load(f)
    ordered_repos_vs_stars: Dict[str, int] = OrderedDict({
        repo['full_name']: repo['stargazers_count']
        for i, repo in enumerate(repos['items'])
        if i < 1000
    })

    # get number of raw commits vs repo
    all_files: List[str] = os.listdir(raw_dir)
    raw_commit_files: List[str] = [file for file in all_files if file.endswith('.commits.logs')]
    repo_vs_commit_number: Dict[str, int] = {}
    for cur_repo_file in tqdm(raw_commit_files):
        repo_name = cur_repo_file.split('.')[0]
        with open(raw_dir.joinpath(cur_repo_file), 'r') as f:
            repo_vs_commit_number[repo_name] = len(f.readlines())

    # get number of filtered commits vs repo for 100
    repo_vs_filtered_commits_100, total_filtered_commits_100 = get_filtered_commits_count(processed_dir_100)
    # get number of filtered commits vs repo for 200
    repo_vs_filtered_commits_200, total_filtered_commits_200 = get_filtered_commits_count(processed_dir_200)

    print(f'Total Filtered 100 = {total_filtered_commits_100}')
    print(f'Total Filtered 200 = {total_filtered_commits_200}')

    # write results
    percentiles_100, percentiles_200 = [], []
    with open(output_file, 'w') as f:
        f.write('Repo Name^Stars^Total Commits Number^'
                'Filtered Commits Number (100)^Percents from Current Repo (100)^Percents from Filtered Commits(100)^'
                'Filtered Commits Number (200)^Percents from Current Repo (200)^Percents from Filtered Commits(200)^\n')

        for repo, stars in ordered_repos_vs_stars.items():
            r_name_for_d = repo.replace('/', '_')
            # if r_name_for_d not in repo_vs_commit_number:
            #     continue
            # else:
            #     f.write(f'{repo}^{stars}^{repo_vs_commit_number[r_name_for_d]}^'
            #             f'{repo_vs_filtered_commits_100[r_name_for_d]}^'
            #             f'{(repo_vs_filtered_commits_100[r_name_for_d] / repo_vs_commit_number[r_name_for_d]) * 100}^'
            #             f'{(repo_vs_filtered_commits_100[r_name_for_d] / total_filtered_commits_100) * 100}^'
            #             f'{repo_vs_filtered_commits_200[r_name_for_d]}^'
            #             f'{(repo_vs_filtered_commits_200[r_name_for_d] / repo_vs_commit_number[r_name_for_d]) * 100}^'
            #             f'{(repo_vs_filtered_commits_200[r_name_for_d] / total_filtered_commits_200) * 100}\n')
            if r_name_for_d in repo_vs_commit_number:
                percentiles_100.append((repo_vs_filtered_commits_100[r_name_for_d] / total_filtered_commits_100) * 100)
                percentiles_200.append((repo_vs_filtered_commits_200[r_name_for_d] / total_filtered_commits_200) * 100)

    # plot_percentile(percentiles_100, 80, 100, 100, '100 tokens')
    # plot_percentile(percentiles_200, 80, 100, 100, '200 tokens')

    # plot_hist(percentiles_100, title='100 tokens')
    plot_hist(percentiles_200, title='200 tokens')


def get_percents(processed_dir: Path, output_file: Path) -> None:
    repo_vs_filtered_commits, total_filtered_commits = get_filtered_commits_count(processed_dir)
    repo_vs_percents = {}
    for repo, commits in repo_vs_filtered_commits.items():
        repo_vs_percents[repo] = (commits / total_filtered_commits) * 100
    repo_vs_percents = OrderedDict(sorted(repo_vs_percents.items(), key=lambda t: t[1]))

    with open(output_file, 'w') as f:
        for repo, perc in repo_vs_percents.items():
            f.write(f"{repo.replace('_', '/')}^{perc}\n")




if __name__ == '__main__':
    counter = multiprocessing.Value('i', 0)
    # get_raw_commits_number()
    get_main_stat(raw_dir=Path('../../../new_data/raw_data/'),
                  processed_dir_100=Path('../../../new_data/processed_data/two_inputs_100/'),
                  processed_dir_200=Path('../../../new_data/processed_data/two_inputs_200/'),
                  output_file=Path('../../../new_data/processed_data/stat_filtered_commits_number.csv'))
    # get_percents(processed_dir=Path('../../../new_data/processed_data/two_inputs_100/'),
    #              output_file=Path('../../../new_data/processed_data/stat_filtered_commits_percents_100.csv'))
    # get_percents(processed_dir=Path('../../../new_data/processed_data/two_inputs_200/'),
    #              output_file=Path('../../../new_data/processed_data/stat_filtered_commits_percents_200.csv'))
