import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties


def plot():
    plt.figure(dpi=320, figsize=(15, 7))
    font = FontProperties()
    font.set_family('serif')
    font.set_name('Times New Roman')

    x = [0,
         1, 1, 1,
         2, 2,
         3, 3, 3,
         4, 4, 4,
         5, 5]
    bleu = [43.33,
            9.1, 27.6, 32.05,
            31, 33,
            14, 15, 16.42,
            3.19, 5.33, 33.63,
            0.87, 2.16]
    x_coord = [0, 1, 2, 3, 4, 5]
    x_labels = ['[2]\n2017',
                '[5]\n2017',
                '[6]\n2019',
                '[1]\n2019',
                '[3]\n2019',
                '[4]\n2019']
    plt.text(x[0] + 0.1, bleu[0] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[1] + 0.1, bleu[1] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[2] + 0.1, bleu[2] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[3] + 0.1, bleu[3] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[4] + 0.1, bleu[4] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[5] + 0.1, bleu[5] - 1, 'HMM', {'color': 'black', 'fontsize': 22})
    plt.text(x[6] + 0.1, bleu[6] - 2, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[7] + 0.1, bleu[7] - 1, 'HMM', {'color': 'black', 'fontsize': 22})
    plt.text(x[8] + 0.1, bleu[8], 'NNGen', {'color': 'black', 'fontsize': 22})
    plt.text(x[9] + 0.1, bleu[9] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[10] + 0.1, bleu[10] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[11] + 0.1, bleu[11] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[12] + 0.1, bleu[12] - 1, 'NMT', {'color': 'black', 'fontsize': 22})
    plt.text(x[13] + 0.1, bleu[13], 'NNGen', {'color': 'black', 'fontsize': 22})

    colors = ['darkred',
              'green', 'green', 'green',
              'red', 'red',
              'lightsalmon', 'lightsalmon', 'lightsalmon',

              'peachpuff', 'blue', 'darkred',
              'silver', 'silver'
              ]

    scale = np.array([450 for _ in range(len(x))])
    plt.scatter(x=x, y=bleu, s=scale, c=colors, marker='^')
    plt.yticks(fontsize=20)
    plt.xlim(-0.3, 5.7)
    plt.xticks(x_coord, x_labels, fontsize=20)
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel("Статьи", fontsize=25)
    plt.ylabel("BLEU", fontsize=28)
    plt.show()


if __name__ == '__main__':
    plot()