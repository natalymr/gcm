# Generate Commit Message

## Results for "N repositories" Dataset

| **Repo Name** |  **Dataset Size (Train, Test, Val)** |**Model Name**|  **BLEU** |
|---|---|---|---|
| aurora |  2256/325/324 |NNGen| 6.97 |
| aurora | 2024/415/441 |code2seq | 13.50 |
|apache/camel | 5693/854/854 |NNGen| 21.88 |
| apache/camel  | 5298/1047/1035 |code2seq| 17.65 |
| aurora → camel |  2256/854 |NNGen| 4.93 |
| aurora → camel | 2024/1047 |code2seq | 9.12 |
| camel → aurora | 5693/325 |NNGen| 5.28 |
| camel → aurora | 5298/415 |code2seq| 8.42 |



## Results for "Top-1000 GitHub Java Repositories" Dataset

| **Tokens Number in Diff** |  **Dataset Size (Train, Test, Val)** |**Model Name**|  **BLEU** |
|---|---|---|---|
| 100 | 47911/9911/9527 | NNGen | 5.51|
| 100 | 47911/9911/9527 | NMT ||
| 100 | 47911/9911/9527 | NMT-2||
| 100 | 10283/1994/1994 | code2seq ||
| 200 | 83055/17319/16648 | NNGen | 3.43|
| 200 | 83055/17319/16648 | NMT ||
| 200 | 83055/17319/16648 | NMT-2 | 4.83 |
| 200 | 56457/10698/10697 | code2seq ||


