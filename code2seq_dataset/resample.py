from operator import itemgetter
from pathlib import Path
from typing import List, Tuple
import numpy as np

from code2seq_dataset.common import parse_dataset_line
from code2seq_dataset.global_vars import Message, Code2SeqPath, dataset_line


def create_dataset_with_exact_number_of_elements(input_file: Path, number_to_get: int, output_file: Path):
    dataset: List[Tuple[Message, List[Code2SeqPath]]] = []
    with open(input_file, 'r') as input:
        for line in input:
            dataset.append(parse_dataset_line(line))

    ind = np.random.choice(len(dataset), number_to_get, replace=False)
    new_dataset: List[Tuple[Message, List[Code2SeqPath]]] = list(itemgetter(*ind)(dataset))

    with open(output_file, 'w') as output:
        for message, paths in new_dataset:
            output.write(dataset_line.substitute(target_message=message,
                                                 paths=' '.join(paths)))


if __name__ == '__main__':
    data: Path = Path("/Users/natalia.murycheva/Documents/code2seq/data/camel/camel.train.all.c2s")
    output: Path = Path("/Users/natalia.murycheva/Documents/code2seq/data/camel/camel.train.c2s")
    number_to_get: int = 1259
    create_dataset_with_exact_number_of_elements(data, number_to_get, output)