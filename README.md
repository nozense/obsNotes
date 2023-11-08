# obsNotes

> [!WARNING]
> This script "works" but is not tested or complete!
> **Do not run** this script without reading and understanding code!

- [obsNotes](#obsnotes)
  - [What is it?](#what-is-it)
    - [Features](#features)
  - [Installation](#installation)
    - [Dependencies](#dependencies)
    - [Process](#process)
  - [Database Struckture](#database-struckture)
  - [Use](#use)
    - [CLI](#cli)
    - [tmp-files and daily-files](#tmp-files-and-daily-files)
  - [TODO](#todo)

## What is it?

A simple python script to handle a sqlight database file to store notes and a journal.\
The script lets you write to a sqlite database from a cli-"interface" and your favorite editor.

Written in very easy python and should be easely modified by anyone with some basic knowlage of python.\
My goal is to make the code reable, well documented and easy to follow - that might not be the case yet.

**obsNotes** = **o**ne **b**ig **s**qlight **Notes**

I love the idea of "one big file" for notes but needed functionality to quickly add short lines AND longer notes, so i wrote a cli.\
SQLite is just simple and effective way to store data that is very easy to export to what ever format I'd (or you'd) like to use next time.

### Features

- Easy to use
- Very hackable!

## Installation

### Dependencies

1. ``pytz``
2. ``python-frontmatter``
3. ``pyyaml``

### Process

> [!NOTE]
> This script has a **First run** function!
> First run: (edit settings before this!)
>
> - The script will create a folder-structure in the same folder as obsN.py
> - The script will create a sqlite file and add a first entry.

1. Install dependencies
2. Run the script

## Database Struckture

```sql
 "iD" INTEGER UNIQUE - PRIMARY KEY("iD" AUTOINCREMENT)
"book" TEXT
"chapter" TEXT
"part" TEXT
"date" TEXT (written with datetime)
"time" TEXT (written with datetime)
"tags" TEXT
"note" TEXT
```

The logic behind this structure is that Book, Chapter and Part works as folders.
First run will create:
    - Book: notes
    - Chapter: journal
    - Part: log AND daily
**log** is for short captures during the day
and **daily** is for a longer daily entry
that starts is life as an auto-generated .md file.

## Use

Most is self-explanatory.
Run the script! (pref. with python in linux)

### CLI

```bash
usage: obsN.py [-h] [-o] [-l] [-m] [-writeconfig] [-firstrun] [-alias]

options:
  -h, --help    show this help message and exit
  -o            Open Daily-file
  -l            Write quick log-line
  -m            Run the menu
```

### tmp-files and daily-files

If you modify files in an external editor, pay attention to the front-matter format,
the order, number and names of the attributes are needed by the script.
Add/change any value (the part at the right of the ":") but do not change the attribute (to the left of ":").

Name of the daily files is of no consequence - its the date following "Created: " in the frontmatter that is checked.

## TODO

- [ ] Replace pytz
- [ ] Add timezone setting
- [x] Better printout function
- [ ] Faster/cleaner Menu
- [x] Make the logging logical
- [ ] Search function  
- [x] Log for `first_run()`
  