########
obsNotes
########

A simple script to handle a sqlight database file to store notes and a journal.

obsNotes
    One Big Sqlight Notes

===========
What is it?
===========

The script lets you write to a sqlite database from a cli-menu and your favorite editor.


First run: (edit settings besfore this!)
    - The script will create a folder-structure in the same folder as obsN.py
    - The script will create a sqlite file and add a first entry.

Features
--------
- Easy to use CLI menu
- MarkDown export
- Very hackable!

============
Installation
============

Dependencies
------------

1. ``pytz``
2. ``python-frontmatter``

Process
-------

1. Install dependencies
2. Edit the obsN.py file
    * Edit the "settings" section to your liking.

=====
TODO
=====

+-----------------------------+--------+-------+
| TODO                        |  Prio  | Done? |
+=============================+========+=======+
| Replace pytz                |  5     |  no   |
+-----------------------------+--------+-------+
| Make a better               |  1     |  no   |
| printout function           |        |       |
+-----------------------------+--------+-------+
| Make menu faster/cleaner    |  2     |  no   |
+-----------------------------+--------+-------+
| Make the logging logical    |  2     |  no   |
+-----------------------------+--------+-------+