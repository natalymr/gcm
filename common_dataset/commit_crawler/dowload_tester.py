from pathlib import Path
from typing import List, Set
from itertools import groupby

if __name__ == '__main__':
    parent_dir: Path = Path('../../../new_data/raw_data/')
    already_downloaded: Path = parent_dir.joinpath('downloaded.log')
    all_files: List[str] = []
    with open(already_downloaded, 'r') as f:
        for line in f:
            all_files.append(line)

    all_files_set: Set[str] = set(all_files)
    if len(all_files) == len(all_files_set):
        print('Everything is fine')
    else:
        print('We are runing in circle')
        for x, y in groupby(sorted(all_files)):
            if len(list(y)) > 1:
                print(f'We twice downloaded {x}')
