from string import Template
from typing import NewType

Blob = NewType('Blob', str)
Commit = NewType('Commit', str)
Message = NewType('Message', str)
Code2SeqPath = NewType('Code2SeqPath', str)

SEPARATOR: str = 'THIS_STRING_WILL_NEVER_APPEAR_IN_DATASET_AND_IT_WILL_BE_USED_AS_SEPARATOR'
dataset_line = Template('$target_message $paths\n')
changed_files_log_line = Template('$commit_hash$sep$author$sep$status$sep$file_name$sep'
                                  '$old_blob$sep$new_blob$sep$message$sep\n')

PAD: str = '<PAD>'
padded_path: Code2SeqPath = Code2SeqPath("{},{},{}".format(PAD, PAD, PAD))
