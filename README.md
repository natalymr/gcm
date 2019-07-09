# Generate Commit Message

### Statistic for `aurora` dataset

| **Description** |  **Number** |
|---|---|
| Expected commits count |  37077 |
|  Actual commits count | 37078  |
| Total blob-files count  | 150525 |

------

## Papers' metrics

| **Task** | **Title** | **Metric Type** | **Metric Value** | **NB** |
|---|---|---|---|---|
|GCM|Automatically Generating Commit Messages from Diffs using Neural Machine Translation|BLEU|0.319, 0.328|---|
|GCM|Automatic Contextual Commit Message Generation: A Two-phase Conversion Approach|BLEU|0.21 - 0.7|Several projects, smaller than a baseline; on small diff got better results|
|GCM|Neural-machine-translation-based commit message generation: how far are we?|BLEU|38.55 (cleaned 16.42)| analyze dataset and got worse result on cleaned dataset (and NMT) |
|GCM|CoaCor: Code Annotation for Code Retrieval with Reinforcement Learning|MRR|0.429,0.571|Note that we do not target at human language-like annotations; rather, we focus on annotations that can describe/capture the functionality ofa code snippet|
|GCM|On Automatically Generating Commit Messages via Summarization of Source Code Changes|some questions|tables 8, 9,10|---|
|GCM|Content Aware Source Code Change Description Generation|BLEU, METEOR, MEANT|0.01, 0.19, 0.21; 0.03, 0.10, 0.23;|Several datasets|
|Commit Classification|Content Aware Source Code Change Description Generation|Acc, P, R, F1|0.74 - best acc|Several Models|
|Comments Generation|A Neural Model for Generating Natural Language Summaries of Program Subroutines|BLEU|0.196|---|
|Code Summarization|CODE2SEQ: GENERATING SEQUENCES FROM STRUCTURED REPRESENTATIONS OF CODE|BLEU|0.23|code captioning task|
|Code Summarization|STRUCTURED NEURAL SUMMARIZATION|BLEU|0.225|f1, rouge-2, rouge-l|
| GCM |  https://link.springer.com/article/10.1007/s10664-019-09730-9 |


