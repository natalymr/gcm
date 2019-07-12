## Dataset structure
* `gcm_<dataset-name>_com_com_msg_author_date.log` contains info about each commit 
    * parent commit-file hash 
    * current commit-file hash
    * message
    * author
    * date 
* `gcm_<dataset-name>_full.log` contains info about each changed file during every commit
    * current commit-file hash
    * author 
    * status (_A_, _M_, _D_)
    * file path
    * file name that contains previous file version (blob-file) 
    * file name that contains current file version (blob-file)
    * commit message
* `<dataset-name>_blobs` directory contains all blob-files with original content

------

### Statistic for `aurora` dataset

| **Description** |  **Number** |
|---|---|
| Expected commits count |  37077 |
|  Actual commits count | 37078  |
| Total blob-files count  | 153411 |

Link to tar.gz with blobs
https://drive.google.com/file/d/17rfe-r1gB0RizZ85coqSNVlPRXMH3beo/view?usp=sharing

### Statistic for `intellij` dataset

| **Description** |  **Number** |
|---|---|
|Since|2004-01-01|
|Before|2006-07-01|
|  Commits number | 18487  |
|With no message commits number|1723|
| Total blob-files count  | 89795 |
|Commits for train|--|

Link to tar.gz with blobs from intellij
https://drive.google.com/file/d/1_N1ugDOPpAaItDzK9LcQDiWJfsJgVW2O/view?usp=sharing