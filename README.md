# obsNotes

> [!WARNING]
> This script "works" but is not tested or complete!
> **Do not run** this script without reading and understanding code!

## What is it?

A simple script to handle a sqlight database file to store notes and a journal.

obsNotes
    One Big Sqlight Notes

The script lets you write to a sqlite database from a cli-menu and your favorite editor.

### Features

- Easy to use CLI menu
- MarkDown export
- Very hackable!

## Installation

### Dependencies

1. ``pytz``
2. ``python-frontmatter``
 * https://github.com/eyeseast/python-frontmatter
3. ``pyyaml`` 

### Process

> [!NOTE]
> This script has a **First run** function!
> First run: (edit settings before this!)
>   - The script will create a folder-structure in the same folder as obsN.py
>   - The script will create a sqlite file and add a first entry.

1. Install dependencies
2. Edit the obsN.py file
    * Edit the "settings" section to your liking.
    * Take a look at the ``first_run()`` function:
        * understand what this does before running the script!
3. Run the script (-h for help)

#### Database Struckture

* "iD"	INTEGER UNIQUE
    * PRIMARY KEY("iD" AUTOINCREMENT)
* "book"	TEXT
* "chapter"	TEXT
* "part"	TEXT
* "date"	TEXT
* "time"	TEXT
* "tags"	TEXT
* "note"	TEXT

The logic behind this structure is that Book, Chapter and Part works as folders.
First run will create:
    - Book: notes
    - Chapter: journal
    - Part: log AND daily
**log** is for short captures during the day
and **daily** is for a longer daily entry
that starts is life as an auto-generated .md file.

## USE

Most is self-explanatory.
If you modify files in an external editor, pay attention to the front-matter format,
the order, number and names of the attributes are needed by the script.
Add/change any value (the part at the right of the ":") but do not change the attribute (to the left of ":").

Name of the daily files is of no consequence - its the date following "Created: " in the frontmatter that is checked.

### CLI

```
usage: obsN.py [-h] [-o] [-l] [-m] [-writeconfig] [-firstrun] [-alias]

options:
  -h, --help    show this help message and exit
  -o            Open Daily-file
  -l            Write quick log-line
  -m            Run the menu
```

## TODO

- [ ] Replace pytz
- [ ] Add timezone setting
- [x] Better printout function   
- [ ] Faster/cleaner Menu   
- [x] Make the logging logical 
- [ ] Search function  
- [x] Log for first_run() 
