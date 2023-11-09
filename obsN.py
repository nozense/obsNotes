import sqlite3
import datetime
import pytz
import os
import sys
import glob
import frontmatter
import logging
import random
import argparse
import yaml
import shutil
from pathlib import Path
from pprint import pprint

'''
    This is the config! 
    (Below this comment, 'cfg')
    Change these to your liking - the part to the right of :
    Pleace take care to not change the format of this.
    These settings are exported to config.yaml during the first_run.

    If the script finds a config.yaml in the same folder as the script itself
    it will use the config in that file instead of these!
    This is so that you can pull/fetch the updates to the script (overwirte obsN.py)
    without the settings beeing reset.
'''
cfg = {
    'editor' : 'vim',
    'main_folder' : 'obsN-files',
    'tmp_folder' : 'tmp',
    'cache_folder' : 'cache',
    'daily_folder' : 'daily',
    'export_folder' : 'export',
    'backup_folder' : '~', 
    'log_folder' : 'logs',
    'db_file' : 'obsN.sqlite',
    'db_table' : 'obsNotes',
    'log_level' : '2',
    'colors' : 'yes',
    }

script_dir = os.path.dirname(__file__)


if os.path.exists(f"{script_dir}/config.yaml"):
    with open(f"{script_dir}/config.yaml") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

def write_cfg():
    if not os.path.exists(f"{script_dir}/config.yaml"):
        with open(f"{script_dir}/config.yaml", "w") as yamlfile:
            yaml.dump(cfg, yamlfile)
        print(clr.OK + "Creation of config.yaml successful!" + clr.END)
    else:
        print(clr.ER + "Found config.yaml - edit that file instead!" + clr.END)
    


editor = cfg['editor']  
main_folder = cfg['main_folder']
tmp_folder = cfg['tmp_folder']
cache_folder = cfg['cache_folder']
daily_folder = cfg['daily_folder']
export_folder = cfg['export_folder']
backup_folder = cfg['backup_folder']
log_folder = cfg['log_folder']
db_file = cfg['db_file']
db_table = cfg['db_table']
log_level = cfg['log_level']  
cfg_colors = cfg['colors']

if backup_folder == "~":
    backup_folder = f"{str(Path.home())}"

# Definitions - do not change these
main_folder = os.path.join(script_dir, main_folder)
db_file = os.path.join(script_dir, main_folder, db_file)
tmp_folder = os.path.join(script_dir, main_folder, tmp_folder)
log_folder = os.path.join(script_dir, main_folder, log_folder)
cache_folder = os.path.join(script_dir, main_folder, cache_folder)
daily_folder = os.path.join(script_dir, main_folder, daily_folder)
export_folder = os.path.join(script_dir, main_folder, export_folder)
folder_list = [main_folder, tmp_folder, cache_folder, log_folder, daily_folder, export_folder]

class clr:
    if cfg_colors == "yes":
        OK =  '\033[92m' # Something went RIGHT!
        ER =  '\033[1m\033[91m' # Something went WRONG!
        PR = '\x1B[3m\033[93m' # Promt/test from script
        END = '\033[0m\x1B[0m'
    else:
        OK =  '' # Something went RIGHT!
        ER =  '\033[1m' # Something went WRONG!
        PR = '\x1B[3m' # Promt/test from script
        END = '\033[0m\x1B[0m'

"""
Adapters for sqlite datetime 
"""


def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()


def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()


sqlite3.register_adapter(datetime.date, adapt_date_iso)
sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)


def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return datetime.date.fromisoformat(val.decode())


def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())


def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.datetime.fromtimestamp(int(val))


sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("timestamp", convert_timestamp)



def get_date():
    """Gets the datetime date for Europe/Stockholm timezone"""
    local_date = datetime.datetime.now(pytz.timezone('Europe/Stockholm')).date()
    local_date = datetime.datetime.strftime(local_date, '%Y-%m-%d')
    return local_date


def get_time():
    """Gets the datetime time for Europe/Stockholm timezone and formats it"""
    now = datetime.datetime.now(pytz.timezone('Europe/Stockholm'))
    local_time = now.strftime("%H:%M:%S")
    return local_time


def only_alnu(fix_str):
    """Removes all nonalpha-numerical characters from a string"""
    fixed_str = ''.join(e for e in fix_str if e.isalnum())
    return fixed_str


def gen_color():
    """Generates a random hex-value similar to a hex-color-code.
    Really only to have some random characters."""
    color = random.randrange(0, 2 ** 24)
    hex_color = hex(color)
    hex_color = hex_color[2:]
    return hex_color


def do_the_logging():
    """Defines the logging-settings"""
    log_file = "log.log"
    if log_level == 1:
        log_file = f"{get_date()}_{get_time().replace(':', '-')}_{gen_color()}.log"
    log_file = os.path.join(log_folder, log_file)
    format_str = "%(asctime)s:%(levelname)s:%(lineno)i:%(message)s"
    logging.basicConfig(filename=log_file, encoding='utf-8', filemode='w', format=format_str, level=logging.DEBUG)
    logging.info('asctime:levelname:lineno:message')


def log(sel, mess):
    """A shorter syntax for logging"""
    match sel:
        case 1:
            logging.error(mess)
        case 2:
            logging.debug(mess)
        case 3:
            logging.info(mess)

def make_backup():
    sql_q = f"SELECT * FROM '{db_table}'"
    now_date = get_date()
    export_things_md(sql_q)
    archive_path = f"{backup_folder}/obsNotes_backup_{str(now_date)}"
    shutil.make_archive(archive_path, 'tar', export_folder)
    for filename in os.listdir(export_folder):
        file_path = os.path.join(export_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            log(1, " - Failed to delete %s. Reason: %s" % (file_path, e))
            print(clr.ER + "Something went sideways!" + clr.END) 
    return f"{archive_path}.tar"



def gen_write_data(row):
    """Takes a database row and generates a string to print out"""
    log(2, "gen_write_data()")
    tags = prt_tags(row[6])
    write_data = (f"""---
iD: {row[0]} 
Book: {row[1]}
Chapter: {row[2]}
Part: {row[3]}
Created: {row[4]} {row[5]}
Tags: 
{tags}---
{row[7]} 
    """)
    return write_data


def prt_tags(row):
    """Takes the database `tags` field and generates a yaml-frontmatter version"""
    log(2, "prt_tags()")
    tags = "- \n"
    if row is None:
        return tags
    if len(row) > 3:
        tags = ""
        tagses = row.split(";")
        for tag in tagses:
            if len(tag) > 1:
                tags += f"- {tag}\n"
    return tags


def write_any(book, chapter, part, date, time, tags, note):
    """Writes any note to the DB, all given"""
    log(2, "write_any()")
    book = only_alnu(book)
    chapter = only_alnu(chapter)
    part = only_alnu(part)
    try:
        conn = sqlite3.connect(db_file)
        log(2, " - Connected to db")
        cur = conn.cursor()
        sql_q = f"""
            INSERT INTO {db_table} (book, chapter, part, date, time, tags, note) 
            VALUES (?,?,?,?,?,?,?);
            """
        insert_tuple = (book, chapter, part, date, time, tags, note)
        cur.execute(sql_q, insert_tuple)
        log(2, " - tuple inserted")
        conn.commit()
        conn.close()
        log(2, " - Connection closed")
    except sqlite3.Error as error:
        log(1, f"write_any() had an except (sqlite3.error): {error}")


def write_any_log(book, chapter, part, line):
    """Writes a log to any book/chapter"""
    log(2, "write_any_log()")
    book = only_alnu(book)
    chapter = only_alnu(chapter)
    part = only_alnu(part)
    words = line.split()
    tags = ""
    for word in words:
        if word.startswith('#'):
            line = line.replace(word, '')
            word = word.replace('#', '')
            tags += f"{word};"
    now_date = get_date()
    now_time = get_time()
    write_any(book, chapter, part, now_date, now_time, tags, line)


def write_log(line):
    """Writes a line to the journal/log"""
    log(2, "write_log()")
    if len(line) > 2:
        write_any_log("notes", "journal", "log", line)
    else:
        log(2, " - line shorter than 2 char, return false!")
        return False

  
def write_file(file):
    """Writes the given long-file to DB"""
    log(2, "write_file()")
    post = frontmatter.load(file)
    metadata = post.metadata          
    content = post.content
    book = metadata.get('Book')
    chapter = metadata.get('Chapter')
    part = metadata.get('Part')
    created = metadata.get('Created')
    date = datetime.datetime.strftime(created, '%Y-%m-%d')
    the_time = datetime.datetime.strftime(created, '%H:%M:%S')
    tagses = metadata.get('Tags')
    tags = ""
    for tag in tagses:
        if tag is not None and len(tag) > 2:
            tags += f"{tag};"
    write_any(book, chapter, part, date, the_time, tags, content)
    os.remove(file)
    log(2, " - Note written and file removed")
    print(clr.OK + f"Note written to {book}/{chapter}/{part}!" + clr.END)   


def update_from_file(path):
    """Writes changes from a file to the database"""
    log(2, "update_from_file()")
    post = frontmatter.load(path)
    metadata = post.metadata          
    content = post.content
    the_id = metadata.get('iD')
    tagses = metadata.get('Tags')
    tags = ""
    for tag in tagses:
        if tag is not None and len(tag) > 2:
            tags += f"{tag};"
    book = metadata.get('Book')
    chapter = metadata.get('Chapter')
    part = metadata.get('Part')
    created = metadata.get('Created')
    date = datetime.datetime.strftime(created, '%Y-%m-%d')
    the_time = datetime.datetime.strftime(created, '%H:%M:%S')
    try:
        conn = sqlite3.connect(db_file)
        log(2, " - Connected to db")
        cur = conn.cursor()
        sql_q = (f"""UPDATE {db_table} 
        SET book = '{book}', 
        chapter ='{chapter}', 
        part = '{part}', 
        date = '{date}', 
        time = '{the_time}', 
        tags = '{tags}', 
        note = '{content}' 
        WHERE iD = '{the_id}'""")
        cur.execute(sql_q)
        conn.commit()
        log(2, " - db updated")
        conn.close()
        log(2, " - connection closed")
    except sqlite3.Error as error:
        log(1, f"update_from_file() had an except (sqlite3.error): {error}")
    finally:
        os.remove(path)
        log(2, " - file removed")
        return f"Updated {the_id}!"


def write_all_tmp_files():
    """Finds ALL files in the tmp dir and writes them to db"""
    files = glob.glob(f"{tmp_folder}*.md")
    for file in files:
        write_file(file)
    return True


def create_file(book, chapter, part, date, path):
    """Creates a file to insert longer notes to the database"""
    log(2, "create_file()")
    if os.path.exists(path.strip()):
        log(2, " - File already exists")
        print(clr.ER + "File allready exists!" + clr.END)
        return path
    elif not os.path.exists(path.strip()):
        the_time = "13:37:00"
        f = open(path, "w", encoding="utf-8")
        log(2, " - File created")
        first_line = f"---\nBook: {book}\nChapter: {chapter}\nPart: {part}\nCreated: {date} {the_time}\nTags:\n- \n---\n"
        f.write(first_line)
        log(2, " - frontmatter written")
        f.close()
        log(2, " - File closed")
        return path


def get_things(sql_q):
    """Gets things from the database and returns the cursor"""
    log(2, "get_things()")
    try:
        conn = sqlite3.connect(db_file)
        log(2, " - Connected to db")
        cur = conn.cursor()
        cur.execute(sql_q)
        log(2, " - sql executed, returning cursor")
        return cur
    except sqlite3.Error as error:
        log(2, f"get_things() had an except (sqlite3.error): {error}")


def export_things_md(sql_q):
    """Export from DB to file based on sql_q - a sql query."""
    log(2, "export_things()")
    result = get_things(sql_q)
    i = 0
    for row in result:
        write_data = gen_write_data(row)
        clean_date = row[4].replace(":", "-")
        folder_path = f"{export_folder}/{row[1]}/{row[2]}/{row[3]}/"
        if not os.path.exists(folder_path):
            try:  
                os.makedirs(folder_path)
                log(2, " - Folder did not exist - created")
            except OSError as error:  
                log(1, f"export_things() os.mkdir had an error: {error}")
        path = f"{folder_path}{clean_date}_{row[0]}.md"
        if not os.path.exists(path):
            f = open(path, "w", encoding="utf-8")
            f.write(write_data)
            f.close()
            log(2, f" - exported file ({i})")
            i += 1
    print(clr.OK + f" Exported a total of {i} files." + clr.END)


def export_for_edit(the_id):
    """Exports a DB-entry by iD  to a cashe file for edit."""
    log(2, "export_for_edit(the_id)")
    the_file = f"cache_{the_id}.md"
    path = os.path.join(cache_folder, the_file)
    sql_q = f"SELECT * FROM '{db_table}' WHERE iD = '{the_id}'"
    result = get_things(sql_q)
    write_data = "no"
    for row in result:
        write_data = gen_write_data(row)
    if not os.path.exists(path):
        if not write_data == "no":
            f = open(path, "w", encoding="utf-8")
            f.write(write_data)
            f.close()
            log(2, " - wrote to cache file")
    if write_data == "no":
        log(1, " - id not in DB!")
        return False
    return path


def export_selection(choice, selection):
    """export to file based on selection"""
    log(2, "export_selection()")
    sql_q = "not"
    match choice:
        case "tag":
            sql_q = f"SELECT * FROM '{db_table}' WHERE tags LIKE '%{selection}%'"
            log(2, " - tag")
        case "book":
            sql_q = f"SELECT * FROM '{db_table}' WHERE book = '{selection}'"
            log(2, " - book")
        case "chapter":
            selection = selection.split(";")
            sql_q = f"SELECT * FROM '{db_table}' WHERE book = '{selection[1]}' AND chapter = '{selection[2]}'"
            log(2, " - chapter")
        case "part":
            log(2, " - part")
            selection = selection.split(";")
            sql_q = f"""SELECT * FROM '{db_table}' 
                WHERE book = '{selection[1]}' 
                AND chapter = '{selection[2]}' 
                AND part = '{selection[3]}'"""
        case "id":
            log(2, " - id")
            sql_q = f"SELECT * FROM '{db_table}' WHERE iD = '{selection}'"
        case _:
            log(1, f"export_selection() didnt find the choice!")
    if not sql_q == "not":
        export_things_md(sql_q)


def find_old_daily():
    """Find out if there are any older (and/or newer <- should not happen) daily files in the daily-folder,
    if there is older files it writes them to db with write_file()"""
    log(2, "find_old_daily()")
    now_date = get_date()
    the_file = "*.md"
    path = os.path.join(daily_folder, the_file)
    files = glob.glob(path)
    return_path = "no-today-file"
    for file in files: 
        post = frontmatter.load(file)
        metadata = post.metadata          
        content = post.content
        created = metadata.get('Created')
        file_date = datetime.datetime.strftime(created, '%Y-%m-%d')
        if file_date < now_date:
            log(2, " - older than today")
            if len(content) < 6:
                log(2, " - empty")
                print(clr.ER + "Old daily is empty - Removed" + clr.END)
                os.remove(file)
            else:
                print(clr.OK + "Written old daily" + clr.END)
                write_file(file)
                log(2, " - wrote old daily file to db.")
        elif file_date == now_date:
            log(2, " - found today!")
            return_path = file
    return return_path


def run_daily():
    """Runs the daily routine - trying to find the daily file for today's date, creating it if not found."""
    log(2, "run_daily()")
    return_path = find_old_daily()
    now_date = get_date()
    color = gen_color()
    the_file = f"{str(now_date)}_{color}.md"
    path = os.path.join(daily_folder, the_file)
    if return_path == "no-today-file":
        log(2, " - No today-file found")
        path = create_file("notes", "journal", "daily", now_date, path)
    else:
        log(2, " - found today!")
        path = return_path
    return path


def open_today():
    """Open todays daily-file with specified editor."""
    log(2, "open_today()")
    path = run_daily()
    os.system(editor + " " + path)


def print_nice(cursor, choice):
    """Print function with two different ways to print:
     * `full` gives a full recount of all the information in given cursor
     * `short` just gives some information and chopped in length - in a table
    """
    log(2, "print_nice()")
    data = cursor
    result = ""
    match choice:
        case "full":
            log(2, " - full")
            for row in data:
                result += gen_write_data(row)
                result += "\n---\n"
            return result

        case "short":
            log(2, " - short")
            len_id = 5
            len_date = 10
            len_time = 8
            len_tags = 20
            len_note = 35
            lines = []
            for row in data:
                if row[6]:
                    tagses = row[6].split(";")
                else:
                    tagses = []
                tags = ""
                for tag in tagses:
                    if len(tag) > 1:
                        tag = f"#{tag}"
                        tags += f"{tag} "
                note = row[7]
                note = note.replace("\n", " ")
                note = (note[:30] + '[...]') if len(note) > 30 else note
                tags = (tags[:15] + '[...]') if len(tags) > 15 else tags
                the_id = row[0]
                the_date = row[4]
                the_time = row[5]
                line = ""
                line += f"| {the_id} "
                for i in range(len_id - len(str(the_id))):
                    line += " "
                line += f"| {the_date} | {the_time} "
                line += f"| {tags} "
                for i in range(len_tags - len(tags)):
                    line += " "
                line += f"| {note} "
                for i in range(len_note - len(note)):
                    line += " "
                line += "|\n"
                lines.append(line)
            devider = "+-"
            for i in range(len_id):
                devider += "-"
            devider += "-+-"
            for i in range(len_date):
                devider += "-"
            devider += "-+-"
            for i in range(len_time):
                devider += "-"
            devider += "-+-"
            for i in range(len_tags):
                devider += "-"
            devider += "-+-"
            for i in range(len_note):
                devider += "-"
            devider += "-+\n"
            result += devider
            for line in lines:
                result += line
                result += devider
            return result


def print_all():
    """Dumps all from DB."""
    log(2, "print_all()")
    result = get_things(f"SELECT * FROM '{db_table}' ORDER BY date")
    for row in result:
        print(row)


def print_from_id(the_id):
    """Prints a post from iD"""
    log(2, "print_from_id()")
    result = get_things(f"SELECT * FROM '{db_table}' WHERE iD={the_id}")
    print(print_nice(result, "full"))


def get_books():
    """Gets a list of all the books in db"""
    log(2, "get_books()")
    books = []
    result = get_things(f"SELECT book FROM '{db_table}'")
    for row in result:
        row = only_alnu(row)
        if row not in books:
            books.append(row)
    return books


def get_chapters(book):
    """Gets all the chapters in given book"""
    log(2, "get_chapters()")
    chapters = []
    result = get_things(f"SELECT chapter FROM '{db_table}' WHERE book = '{book}'")
    for row in result:
        row = only_alnu(row)
        if row not in chapters:
            chapters.append(row)
    return chapters


def get_parts(book, chapter):
    """Gets all the parts of the given chapter in the given book"""
    log(2, "get_parts()")
    parts = []
    result = get_things(f"SELECT part FROM '{db_table}' WHERE book = '{book}' AND chapter = '{chapter}'")
    for row in result:
        row = only_alnu(row)
        if row not in parts:
            parts.append(row)
    return parts


def get_notes(book, chapter, part):
    """Gets the notes in the given part of the given chapter in the given book"""
    log(2, "get_notes()")
    sql_q = (f"""SELECT *
            FROM '{db_table}' 
            WHERE book = '{book}' 
            AND chapter = '{chapter}' 
            AND part='{part}'""")
    result = get_things(sql_q)
    notes = print_nice(result, "short")
    return notes


def get_latest_db():
    """Gets the latest note in DB by iD"""
    log(2, "get_latest_db()")
    sql_q = get_things(f"""SELECT *
        FROM '{db_table}' 
        ORDER BY ID DESC LIMIT 1""")
    result = print_nice(sql_q, "full")
    return result



def search_for(choice, srch_str):
    log(2, "search_for()")
    match choice:
        case "all":
            log(2, " - all")
            result = get_things(f"SELECT * FROM '{db_table}' WHERE tags LIKE '%{srch_str}%' or note LIKE '%{srch_str}%'")
        case "tags":
            log(2, " - tags")
            result = get_things(f"SELECT * FROM '{db_table}' WHERE tags LIKE '%{srch_str}%'")
        case _:
            print(clr.ER + "Something went sideways!" + clr.END) 
            logging.error(f" - Did'nt get a valid case match!")
            return False
    result = print_nice(result, "short")
    return result

def create_long(book, chapter, part):
    """Creates a new long-file for the given book/chapter/part and returns path"""
    log(2, "create_long()")
    now_date = get_date()
    path = f"{tmp_folder}tmp_{now_date}_{book}_{chapter}_{part}.md"
    path = create_file(book, chapter, part, now_date, path)
    return path

def write_alias():
    alias_line = f"alias obsN='{sys.executable} {__file__}'"
    print(clr.OK + alias_line + clr.END)
    print("\nThe line above is an example 'alias' line for .bashrc.")
    print("If written to your ~/.bashrc it lets you run this script with 'obsN' from anywhere.\n")
    write_rc = input(clr.PR + "Should I try and append this line to the end of your .bashrc? y/n > " + clr.END)
    if write_rc == "y" or write_rc == "Y":
        try:
            file_rc = os.path.expanduser('~')
            file_rc = f"{file_rc}/.bashrc"
            right_path = input(clr.PR + f"Is this the path to your .bashrc '{file_rc}' ? y/n > " + clr.END)
            if right_path == "y" or right_path == "Y":
                with open(file_rc, "a") as bashrc:
                    bashrc.write("\n")
                    bashrc.write(alias_line)
                    bashrc.write("\n")
                    print(clr.OK + "Appended alias to .bashrc\n" + clr.END)
                    print("Reload .bashrc with 'source ~/.bashrc' - or reboot (= \n")
            else:
                print(clr.ER + "Did NOT write to .bashrc" + clr.END)
        except OSError as error:
            print(clr.ER + "Something went sideways!" + clr.END) 
            log(1, f" - had an error! ({error})")
    else:
        print(clr.ER + "Did NOT write to .bashrc" + clr.END)

def first_run():
    """A function to create a folder-structure and sqlite file to use obsNotes"""
    f=open(f"{script_dir}/first_run_log(OK TO DELETE).txt", "a+")
    def first_run_log(line):
        log_line = f"{get_date()} - {get_time()}: {line}\n"
        f.write(log_line)
    first_run_log("first_run()")
    print("\nYour current config is: \n")
    pprint(cfg, width=1)
    ok_cfg = input(clr.PR + "\nDoes this look alright to you? y/n > " + clr.END)
    if not ok_cfg == "y" or ok_cfg == "Y":
        write_cfg()
        print("\nCreated a config.yaml file in the same directory as the script-file.\n")
        print("Please modify this file to your liking and run this script agan!")
        sys.exit()
    sql_q = (f'CREATE TABLE "{db_table}" (\n'
             '	"iD"	INTEGER NOT NULL UNIQUE,\n'
             '	"book"	TEXT NOT NULL,\n'
             '	"chapter"	TEXT NOT NULL,\n'
             '	"part"	TEXT,\n'
             '	"date"	TEXT NOT NULL,\n'
             '	"time"	TEXT NOT NULL,\n'
             '	"tags"	TEXT,\n'
             '	"note"	TEXT,\n'
             '	PRIMARY KEY("iD" AUTOINCREMENT)\n'
             '    )')
    for folder in folder_list:
        print(f"{folder}")
    create_all = input(clr.PR + "Should I create these folders (and database file)? y/n > " + clr.END)
    if create_all == "y" or create_all == "Y":
        first_run_log(" - Create folders: YES")
        for folder in folder_list:
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                    first_run_log(f" - Folder did not exist, created {folder}")
                except OSError as error:
                    first_run_log(f"first_run() os.makedirs had an error: {error}")
        try:
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            cur.execute(sql_q)
            conn.commit()
            conn.close()
            first_run_log(f" - Database created")
            write_log("DB created!")
            first_run_log(f" - First row written to DB")
        except sqlite3.Error as error:
            first_run_log(f"first_run() had an except (sqlite3.error): {error}")
        print(clr.OK + "Created Folders and Database file! \n" + clr.END)
        if not os.path.exists(f"{script_dir}/config.yaml"):
            first_run_log(" - No config file")
            write_cfg()
            first_run_log(" - Created config.yaml")
            print(clr.OK + "\nDid not find a config.yaml - Created one!\n" + clr.END)
        write_alias()
        print("\nExiting the script now, run it again to see the menu or use '-h' to see cli-commands!\n")
        sys.exit()
    else:
        print(clr.ER + "Did NOT create anything!\n" + clr.END)
        first_run_log(" - Did NOT create anything!")
        sys.exit()
    

def run_menu():
    """Runs the menu-driven notes system - alot of looping and code (sanitize!)"""
    log(2, "run_menu()")
# Menu Loops
        
    def what_parts():
        log(2, "what_parts()")
        try:
            print("\n")
                # What book
            books = get_books()
            i = 0
            for book in books:
                i += 1
                print(f"    {i}: {book}")
            val1 = int(input(clr.PR + "\n What book? " + clr.END)) - 1
            book = books[val1]
        # What Chapter
            chapters = get_chapters(book)
            i = 0
            for chapter in chapters:
                i += 1
                print(f"    {i}: {chapter}")
            val2 = int(input(clr.PR + "\n What chapter? " + clr.END)) - 1
            chapter = chapters[val2]
        # What part
            parts = get_parts(book, chapter)
            i = 0
            for part in parts:
                i += 1
                print(f"    {i}: {part}")
            val3 = int(input(clr.PR + "\n What part? " + clr.END)) - 1
            part = parts[val3]
            return [book, chapter, part]
        except Exception as error:
            print(clr.ER + "    Something went sideways!" + clr.END)
            log(1, f"what_parts() - {error}")
            return

    def q_loop():
        log(2, f"run_menu() got q")
        print("\n" + clr.OK + "Good " + clr.PR + "Bye" + clr.ER + "!" + clr.END + "\n")

    def tmp_loop():
        log(2, f"run_menu() got tmp")
        print(get_latest_db())

    def h_loop():
        log(2, f"run_menu() got h")
        files = glob.glob(f"{tmp_folder}*.md")
        file_list = []
        i = 0
        if files:
            for file in files:
                file_name = file.replace(f"{tmp_folder}", "")
                file_list.append(file)
                i += 1
                print(f"    {i}: {file_name}")
            val1 = input(""" 
                Do you want to:
                    e Edit a tmp file
                    w Write a tmp file
                    d Delete a temp file
                    > """)
            match val1:
                case "e":
                    log(2, f"run_menu() - h: got e")
                    val2 = int(input(clr.PR + "\n What file do you want to edit? " + clr.END))
                    if len(file_list) >= val2:
                        path = file_list[val2-1]
                        os.system(editor + " " + path)
                case "d":
                    log(2, f"run_menu() - h: got d")
                    val2 = int(input(clr.PR + "\n What file do you want to delete? " + clr.END))
                    if len(file_list) >= val2:
                        path = file_list[val2-1]
                        os.remove(path)
                        print(clr.OK + "File deleted!" + clr.END)
                case "w":
                    log(2, f"run_menu() - h: got w")
                    val2 = int(input(clr.PR + "\n What file do you want to write? (0 For all) " + clr.END))
                    if val2 == 0:
                        write_all_tmp_files()
                    elif len(file_list) >= val2:
                        path = file_list[val2-1]
                        write_file(path)
                case _:
                    print(clr.ER + "Something went sideways!" + clr.END) 
                    logging.error(f"run_menu()- h: Got a choice thats not in the menu")
        else:
            print("No files found!")
            
    def a_loop():
        log(2, f"run_menu() got a")
        try:
            parts = what_parts()
            book = parts[0]
            chapter = parts[1]
            part = parts[2]
        # Long or short
            val4 = int(input(clr.PR + "\n Do you want to add a:\n 1. Short log\n 2. Long note \n  > " + clr.END))
            if val4 == 1:
                val5 = input(clr.PR + "\n What do you want to add to {book}/{chapter}/{part}:\n  > " + clr.END)
                write_any_log(book, chapter, part, val5)
            elif val4 == 2:
                path = create_long(book, chapter, part)
                os.system(editor + " " + path) 
        except Exception as error:
            print(clr.ER + "    Something went sideways!" + clr.END)
            log(1, f"a_loop() - {error}")
            return

    def s_loop():
        log(2, f"run_menu() got s")
        srch_str = input(clr.PR + "\nWhat do you want to seach for (str)? \n > " + clr.END)
        srch_in = input(clr.PR + "\n Search in:\n t: Tags \n a: Everything \n > " + clr.END)
        match srch_in:
            case "t":
                choice = "tags"
            case "a":
                choice = "all"
            case _:
                choice = "all"
        print(search_for(choice, srch_str))
        look_at = input(clr.PR + "Want to look closer at any of them? (iD)" + clr.END)        
        print_from_id(look_at) 

    def b_loop():
        try:
            log(2, f" - got b")
            parts = what_parts()
            book = parts[0]
            chapter = parts[1]
            part = parts[2]
            print(get_notes(book, chapter, part))
            log(2, f"b_loop() edit/view")
            val4 = int(input(clr.PR + "\n 0: Edit a note\n What note id do you want to open?  " + clr.END))
            if val4 == 0:
                log(2, f"b_loop() edit/view - edit")
                val4 = int(input(clr.PR + "\n What note id do you want to EDIT?  " + clr.END))
                path = export_for_edit(val4)
                if path:
                    os.system(editor + " " + path)
                    print(update_from_file(path))
                    log(2, f"b_loop() edit/view - edited!")
                else:
                    print(clr.ER + "Something went sideways!" + clr.END) 
                    log(1, f"b_loop() edit/view - tried to edit a id not in db!")
            else:
                log(2, f"b_loop() edit/view - view")
                print_from_id(val4)
        except Exception as error:
            print(clr.ER + "    Something went sideways!" + clr.END)
            log(1, f"b_loop() - {error}")
            return
        
    runit = 0
    while runit == 0:
        # MENY
        selector1 = input("""\n
        What do you want to do?
        q Quit
        l Quick log
        o Open daily file
        a Add to any
        s Search
        b Browser DB
        h Handle tmp-files

        > """)
        match selector1:
            # QUIT
            case "q":
                q_loop()
                break
    # test function
            case "tmp":
                tmp_loop()
                continue
    # Handle tmp-files
            case "h":
                h_loop()
                continue
    # Add to any
            case "a":
                a_loop()
                continue
    
    # Browser DB
            case "b":
                b_loop()
                continue
    # QUICK LOG
            case "l":
                log(2, f"run_menu() got l")
                runit1 = 0
                while runit1 == 0:
                    input_line = input(clr.PR + "\nLine for log ('exit' to exit) > " + clr.END)
                    if input_line == "exit":
                        print("\nReturning to start!\n")
                        runit1 = 1
                    else:
                        do_it = write_log(input_line)
                        if do_it is False:
                            print(clr.ER + "Line must be longer than 2 char!" + clr.END)
                            runit1 = 0
                        else:
                            print(clr.OK + "Line written." + clr.END)
                            runit1 = 2     
    # SEARCH TAG
            case "s":
                s_loop()
                continue
    # Open daily file
            case "o":
                log(2, f"run_menu() got o")
                open_today()
                continue        
            case _:
                logging.error(f"run_menu() did not get a viable selection in the menu!")
                print(clr.ER + "\nSomething went sideways, check your input!\n" + clr.END)
                continue


def main():
    log(2, "main()")
    try:
        run_menu()
    except Exception as error:
        print(clr.ER + "Something went sideways!" + clr.END) 
        log(1, f"main() had an error! ({error})")
        return


parser = argparse.ArgumentParser()
parser.add_argument("-o", help="Open Daily-file", action="store_true")
parser.add_argument("-l", help="Write quick log-line", action="store_true")
parser.add_argument("-m", help="Run the menu", action="store_true")
parser.add_argument("-bu", help="Make backup to single archive in ~/", action="store_true")


args = parser.parse_args()



if __name__ == "__main__":
    if not os.path.exists(db_file): # <--- Check for firstrun!
        print("\nDid not find your DB-file!\n")
        print(f"Looked in for it here: {db_file}\n")
        print("This is eighter your first run of this script - or a catastrophic faliure!\n")
        frst_run = input(clr.PR + "Is this the first time you run this script (or a new installation)? y/n > " + clr.END)
        if frst_run == "n" or frst_run == "N":
            print("\nTry and make sure your DB-file is in the above location, or modifie your config!\n")
            sys.exit()
        elif frst_run == "y" or frst_run == "Y":
            print("\nWill now run a first-run script!")
            first_run()
        else:
            print(clr.ER + "Something went sideways!" + clr.END) 
            sys.exit()
    
    try:
        do_the_logging()
    except OSError as error:
        print(f"No logging")
    if args.o:
        log(2, "args.o")
        open_today()
    elif args.l:
        log(2, "args.l")
        input_line = input(clr.PR + "Line for log ('exit' to exit) > " + clr.END)
        do_it = write_log(input_line)
        if do_it is False:
            print(clr.ER + "Line must be longer than 2 char!" + clr.END)
        else:
            print(clr.OK + "Line written." + clr.END)
    elif args.m:
        run_menu()
    elif args.bu:
        file_path = make_backup()
        print(f"Backup (as markdown files) saved to your home folder ({file_path}).\n To backup the DB (as is) just copy the '{db_file}' file.")
    else:
        log(2, "No args")
        main()
    
