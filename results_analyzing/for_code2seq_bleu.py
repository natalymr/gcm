from collections import OrderedDict
from pathlib import Path
from typing import List


def get_nltk_bleu_score_for_corpora_print(refs: List[str], preds: List[str]) -> float:
    import nltk
    total_bleu = 0.
    msg_vs_bleu = {}
    for ref, pred in zip(refs, preds):
        if len(pred.split()) == 0:
            bleu = 0
        else:
            bleu = nltk.translate.bleu_score.sentence_bleu([ref.split()], pred.split(),
                                                           auto_reweigh=True,
                                                           smoothing_function=nltk.translate.bleu_score.SmoothingFunction().method7) * 100
        msg_vs_bleu[f'{ref.strip()} || {pred.strip()}'] = bleu
        total_bleu += bleu
    msg_vs_bleu = OrderedDict(sorted(msg_vs_bleu.items(), key=lambda t: t[1], reverse=True))
    for msg, bleu in msg_vs_bleu.items():
        if bleu > 1:
            print('{:.3f} || {}'.format(bleu, msg))
    return total_bleu / len(refs)


def get_nltk_bleu_score_for_corpora(refs: List[str], preds: List[str]) -> float:
    import nltk
    total_bleu = 0.
    for ref, pred in zip(refs, preds):
        if len(pred.split()) == 0:
            continue
        total_bleu += nltk.translate.bleu_score.sentence_bleu([ref.split()], pred.split(),
                                                              auto_reweigh=True,
                                                              smoothing_function=nltk.translate.bleu_score.SmoothingFunction().method7) * 100
    return total_bleu / len(refs)


def get_bleu_corpora(refs: List[str], preds: List[str]) -> float:
    import nltk
    for i in range(len(refs)):
        refs[i] = refs[i].split()
        preds[i] = preds[i].split()

    return nltk.translate.bleu_score.corpus_bleu(refs, preds,
                                                 auto_reweigh=True,
                                                 smoothing_function=nltk.translate.bleu_score.SmoothingFunction().method7) * 100


if __name__ == '__main__':
    pred, ref = Path('pred.txt'), Path('ref.txt')
    preds = []
    with open(pred, 'r') as f:
        for line in f:
            line = line.strip()
            if line != '':
                preds.append(line)
        # preds = f.readlines()

    with open(ref, 'r') as f:
        refs = f.readlines()
    get_nltk_bleu_score_for_corpora_print(refs, preds)
    print(get_nltk_bleu_score_for_corpora(refs, preds))
    print(get_bleu_corpora(refs, preds))
