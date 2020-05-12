from pathlib import Path


def process_file(input_file: Path) -> None:
    with open(input_file, 'r') as f:
        lines = f.readlines()

    with open(input_file, 'w') as f:
        for line in lines:
            f.write(line.replace('camel|<num>|', ''))


def main():
    dataset_name = 'camel'
    train_file = Path(f'{dataset_name}.train.c2s')
    val_file = Path(f'{dataset_name}.val.c2s')

    process_file(train_file)
    process_file(val_file)


if __name__ == '__main__':
    main()
