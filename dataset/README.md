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
| Total blob-files count  | 150525

Link to tar.gz with blobs

https://drive.google.com/file/d/1XRvoul13ZL2pBLAzQ-JVYD6V65YMQcLl/view?usp=sharing
