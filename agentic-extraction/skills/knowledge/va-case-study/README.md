# VA Case Study Knowledge

## Experience Candidates

Store candidate experience records under `experience-candidates/`.

Naming rule:

- use one JSONL file per paper
- name the file `<paper>.jsonl`
- use the paper slug consistently, for example `conceptviz.jsonl`

Update rule:

- if a file for the paper already exists, append new candidate records to that file
- if no file exists yet, create `<paper>.jsonl`
- do not create a new file for every review or revision round unless a separate workflow explicitly requires it

Each record should continue to store finer-grained provenance inside the JSON object itself, such as:

- `paper`
- `skill`
- `stage`
- `source`
- `timestamp`
