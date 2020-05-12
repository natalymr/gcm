# Generate Commit Message

## Results for "N repositories" Dataset

| **Repo Name** |  **Dataset Size (Train, Test, Val)** |**Model Name**|  **BLEU** |
|---|---|---|---|
| aurora |  2256/325/324 |NNGen| [6.97](https://github.com/natalymr/gcm/blob/master/generated_messages_results/NNGen_aurora.txt) |
| aurora | 2024/415/441 |code2seq | [13.50](https://github.com/natalymr/gcm/blob/master/generated_messages_results/code2seq_aurora.txt) |
|apache/camel | 5693/854/854 |NNGen| [21.88](https://github.com/natalymr/gcm/blob/master/generated_messages_results/NNGen_camel.txt) |
| apache/camel  | 5298/1047/1035 |code2seq| [17.65](https://github.com/natalymr/gcm/blob/master/generated_messages_results/code2seq_camel.txt) |
| aurora → camel |  2256/854 |NNGen| [4.93](https://github.com/natalymr/gcm/blob/master/generated_messages_results/NNGen_aurora_camel.txt) |
| aurora → camel | 2024/1047 |code2seq | [9.12](https://github.com/natalymr/gcm/blob/master/generated_messages_results/code2seq_aurora_camel.txt) |
| camel → aurora | 5693/325 |NNGen| [5.28](https://github.com/natalymr/gcm/blob/master/generated_messages_results/NNGen_camel_aurora.txt) |
| camel → aurora | 5298/415 |code2seq| [8.42](https://github.com/natalymr/gcm/blob/master/generated_messages_results/code2seq_camel_aurora.txt) |



## Results for "Top-1000 GitHub Java Repositories" Dataset

| **Tokens Number in Diff** |  **Dataset Size (Train, Test, Val)** |**Model Name**|  **BLEU** |
|---|---|---|---|
| 100 | 47911/9911/9527 | NNGen | [5.51](https://github.com/natalymr/gcm/blob/master/generated_messages_results/NNGen_Top_1000_dataset_100_tokens.txt) |
| 100 | 47911/9911/9527 | NMT | 1.92 |
| 100 | 47911/9911/9527 | NMT-2| [5.33](https://github.com/natalymr/gcm/blob/master/generated_messages_results/nmt_2_Top_1000_100_tokens.txt) |
| 100 | 10283/1994/1994 | code2seq | [14.89](https://github.com/natalymr/gcm/blob/master/generated_messages_results/code2seq_Top_1000_dataset_100_tokens.txt) |
| 200 | 83055/17319/16648 | NNGen | [4.12](https://github.com/natalymr/gcm/blob/master/generated_messages_results/NNGen_Top_1000_dataset_200_tokens.txt) |
| 200 | 83055/17319/16648 | NMT | 1.58 |
| 200 | 83055/17319/16648 | NMT-2 | 4.83 |
| 200 | 56457/10698/10697 | code2seq | [14.68](https://github.com/natalymr/gcm/blob/master/generated_messages_results/code2seq_Top_1000_dataset_200_tokens.txt) |


