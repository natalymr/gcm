import os
import random
import string

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from parse import parse
from pathlib import Path
from typing import List, Optional

from code2seq_dataset.global_vars import Message


@dataclass
class BleuResults:
    bleu: float
    ngram1: float
    ngram2: float
    ngram3: float
    ngram4: float
    BP: float
    ratio: float
    hyp_len: int
    ref_len: int

    @staticmethod
    def from_perl_script_output(output: str) -> Optional['BleuResults']:
        parsed = parse('BLEU = {bleu}, {ngr1}/{ngr2}/{ngr3}/{ngr4} '
                       '(BP={bp}, ratio={ratio}, hyp_len={h_l}, ref_len={r_l})',
                       output)
        if parsed is None:
            print(f'We got an error on this perl output: .{output}.')
            return None

        return BleuResults(bleu=float(parsed['bleu']),
                           ngram1=float(parsed['ngr1']),
                           ngram2=float(parsed['ngr2']),
                           ngram3=float(parsed['ngr3']),
                           ngram4=float(parsed['ngr4']),
                           BP=float(parsed['bp']),
                           ratio=float(parsed['ratio']),
                           hyp_len=int(parsed['h_l']),
                           ref_len=int(parsed['r_l']))


@dataclass
class TranslationResults:
    ref: Message
    pred: Message
    result: BleuResults

    @staticmethod
    def is_bleu_not_almost_zero(elem: 'TranslationResults') -> bool:
        return elem.result.bleu > 0.1

    @staticmethod
    def is_bleu_is_zero(elem: 'TranslationResults') -> bool:
        return 0 == elem.result.bleu


def sort_by_bleu(elements: List[TranslationResults]) -> List[TranslationResults]:
    return sorted(elements, key=lambda elem: elem.result.bleu)


def plot_bleu(elements: List[TranslationResults], title: str, percentiles: List[int], offset: int) -> None:
    fig, ax = plt.subplots(figsize=(20, 10))
    elements_numbers = range(len(elements))
    elements_value = [elem.result.bleu for elem in elements]

    ax.plot(elements_numbers,
            elements_value,
            linewidth=3)
    ax.set(xlabel='pair number', ylabel='bleu score', title=title)
    for percentile in percentiles:
        perc_value = np.percentile(elements_numbers, percentile)
        ax.vlines(x=perc_value, ymin=0, ymax=np.max(elements_value),
                  colors='k', linestyles='--', label=f'{percentile} percentile')
        ax.text(perc_value - offset, np.max(elements_value) // 2, f'{percentile} percentile',
                fontsize=15,
                rotation=90)
    ax.grid()
    plt.show()


def get_data(ref_file: Path, pred_file: Path) -> (List[Message], List[Message]):
    all_ref: List[Message] = []
    with open(ref_file, 'r') as r:
        for line in r:
            all_ref.append(Message(line))

    all_pred: List[Message] = []
    with open(pred_file, 'r') as pr:
        for line in pr:
            all_pred.append(Message(line))

    return all_ref, all_pred


def write_to_file(file: Path, to_write: str) -> None:
    with open(file, 'w') as f:
        f.write(to_write)


def run_perl_script_and_parse_result(ref: Message, pred: Message, perl_script_path: str) -> Optional[BleuResults]:
    # write pair to file
    ref_tmp_file: Path = Path.cwd().joinpath(''.join(random.sample(string.ascii_lowercase, 3)))  # (random file name)
    pred_tmp_file: Path = Path.cwd().joinpath(''.join(random.sample(string.ascii_lowercase, 3)))  # (random file name)
    write_to_file(ref_tmp_file, ref)
    write_to_file(pred_tmp_file, pred)

    # run script
    output = os.popen(f'perl {perl_script_path} {ref_tmp_file} < {pred_tmp_file}').read()

    # delete tmp files
    try:
        ref_tmp_file.unlink()
        pred_tmp_file.unlink()
    except FileNotFoundError:
        pass

    # parse results
    return BleuResults.from_perl_script_output(output)


def get_bleu_score_for_each_pair(references: List[Message], predictions: List[Message],
                                 perl_script_path: str) -> List[TranslationResults]:
    """
    Получаем два списка, zip(list1, list2) дает нам пары: что должно было быть, что перевелось.
    Для получения bleu score будем запускать скрипт на перле, для этого необходимо
    - положить каждую пару в свои файлы
    - запустить скрипт
    - распарсить результаты скрипта (сохраняются в dataclass BleuResults)
    Вспомогательные функции: run_perl_script_and_parse_result()
    """
    result: List[TranslationResults] = []

    for ref, pred in zip(references, predictions):
        bleu_result = run_perl_script_and_parse_result(ref, pred, perl_script_path)
        if bleu_result:
            result.append(TranslationResults(ref, pred, bleu_result))
        else:
            print(f'Smth went wrong for ref: {ref}, pred: {pred}')

    return result
