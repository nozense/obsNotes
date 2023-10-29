import sqlite3
import datetime
import pytz
import os
import glob
import frontmatter
import logging
import random


# SETTINGS - Change these to your liking
editor = "notepad"  # the command to launch your favorite editor
main_folder = "obsN-files"
tmp_folder = "tmp"
cache_folder = "cache"
daily_folder = "daily"
export_folder = "export"
log_folder = "logs"
db_file = "obsN.sqlite"
db_table = "obsNotes"
log_level = 1  # 1 = seperate file for every run, save all, 2 just save the latest run


# Definitions - do not change these
script_dir = os.path.dirname(__file__)
main_folder = os.path.join(script_dir, main_folder)
db_file = os.path.join(script_dir, main_folder, db_file)
tmp_folder = os.path.join(script_dir, main_folder, tmp_folder)
log_folder = os.path.join(script_dir, main_folder, log_folder)
cache_folder = os.path.join(script_dir, main_folder, cache_folder)
daily_folder = os.path.join(script_dir, main_folder, daily_folder)
export_folder = os.path.join(script_dir, main_folder, export_folder)
folder_list = [main_folder, tmp_folder, cache_folder, log_folder, daily_folder, export_folder]

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


def first_run():
    """A function to create a folder-structure and sqlite file to use obsNotes"""
    log(2, "first_run()")
    for folder in folder_list:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
                log(2, f" - Folder did not exist, created {folder}")
            except OSError as error:
                log(1, f"first_run() os.makedirs had an error: {error}")

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
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute(sql_q)
        conn.commit()
        conn.close()
        write_log("DB created!")
        log(2, f" - Database created and first row created")
    except sqlite3.Error as error:
        log(1, f"first_run() had an except (sqlite3.error): {error}")
    finally:
        return


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
        log_file = f"{get_date()}_{get_time().replace(':', '-')}_{gen_color()}-log.log"
    log_file = os.path.join(log_folder, log_file)
    format_str = "%(asctime)s:%(levelname)s:%(lineno)i:%(message)s"
    logging.basicConfig(filename=log_file, encoding='utf-8', filemode='w', format=format_str, level=logging.DEBUG)
    logging.info('asctime:levelname:lineno:message')


def log(sel, mess):
    match sel:
        case 1:
            logging.error(mess)
        case 2:
            logging.debug(mess)
        case 3:
            logging.info(mess)


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
    except sqlite3.Error as error:
        log(1, f"write_any() had an except (sqlite3.error): {error}")
    finally:
        conn.close()
        log(2, " - Connection closed")


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
    write_any_log("notes", "journal", "log", line)
  

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
    print(f"Note written to {book}/{chapter}/{part}!")   


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
        print("File found!")
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
        folder_path = f"{export_folder}{row[1]}/{row[2]}/{row[3]}/"
        if not os.path.exists(folder_path):
            try:  
                os.makedirs(folder_path)
            except OSError as error:  
                logging.error(f"export_things() os.mkdir had an error: {error}")

        path = f"{folder_path}{clean_date}_{row[0]}.md"
        if not os.path.exists(path):
            f = open(path, "w", encoding="utf-8")
            f.write(write_data)
            f.close()
            i += 1
    print(f" Exported a total of {i} files.")


def export_for_edit(the_id):
    the_file = f"cache_{the_id}.md"
    path = os.path.join(cache_folder, the_file)
    sql_q = f"SELECT * FROM '{db_table}' WHERE iD = '{the_id}'"
    result = get_things(sql_q)
    for row in result:
        write_data = gen_write_data(row)
    if not os.path.exists(path):
        f = open(path, "w", encoding="utf-8")
        f.write(write_data)
        f.close()
    return path


def export_selection(choise, selection):
    """export to file based on selection"""
    log(2, "export_selection()")
    sql_q = "not"
    match choise:
        case "tag":
            sql_q = f"SELECT * FROM '{db_table}' WHERE tags LIKE '%{selection}%'"
        case "book":
            sql_q = f"SELECT * FROM '{db_table}' WHERE book = '{selection}'"
        case "chapter":
            selection = selection.split(";")
            sql_q = f"SELECT * FROM '{db_table}' WHERE book = '{selection[1]}' AND chapter = '{selection[2]}'"
        case "part":
            selection = selection.split(";")
            sql_q = f"""SELECT * FROM '{db_table}' 
                WHERE book = '{selection[1]}' 
                AND chapter = '{selection[2]}' 
                AND part = '{selection[3]}'"""
        case "id":
            sql_q = f"SELECT * FROM '{db_table}' WHERE iD = '{selection}'"
        case _:
            logging.error(f"export_selection() didnt find the choise!")
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
            if len(content) < 6:
                print("Old daily is empty - Removed")
                os.remove(file)
            else:
                print("Written old daily")
                write_file(file)
        elif file_date == now_date:
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
        path = create_file("notes", "journal", "daily", now_date, path)
    else:
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
            for row in data:
                result += gen_write_data(row)
                result += "\n---\n"
            return result

        case "short":
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


def get_by_tag(tag):
    """Finds all notes with the given tag"""
    log(2, "get_by_tag()")
    result = get_things(f"SELECT * FROM '{db_table}' WHERE tags LIKE '%{tag}%'")
    result = print_nice(result, "short")
    return result


def create_long(book, chapter, part):
    """Creates a new long-file for the given book/chapter/part and returns path"""
    log(2, "create_long()")
    now_date = get_date()
    path = f"{tmp_folder}tmp_{now_date}_{book}_{chapter}_{part}.md"
    path = create_file(book, chapter, part, now_date, path)
    return path


def run_menu():
    """Runs the menu-driven notes system - alot of looping and code (sanitize!)"""
    log(2, "run_menu()")
# Menu Loops

    def q_loop():
        log(2, f"run_menu() got q")
        print("\n Good Bye! \n")

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
                    val2 = int(input("\n What file do you want to edit? "))
                    if len(file_list) >= val2:
                        path = file_list[val2-1]
                        os.system(editor + " " + path)
                case "d":
                    log(2, f"run_menu() - h: got d")
                    val2 = int(input("\n What file do you want to edit? "))
                    if len(file_list) >= val2:
                        path = file_list[val2-1]
                        os.remove(path)
                        print("File deleted!")
                case "w":
                    log(2, f"run_menu() - h: got w")
                    val2 = int(input("\n What file do you want to write? (0 For all) "))
                    if val2 == 0:
                        write_all_tmp_files()
                    elif len(file_list) >= val2:
                        path = file_list[val2-1]
                        write_file(path)
                case _:
                    print("Something went wrong!")
                    logging.error(f"run_menu()- h: Got a choise thats not in the menu")
        else:
            print("No files found!")
            
    def a_loop():
        log(2, f"run_menu() got a")
    # What book
        books = get_books()
        i = 0
        print("\n")
        for book in books:
            i += 1
            print(f"    {i}: {book}")
        val1 = int(input("\n What book do you want to add a note to? ")) - 1
        book = books[val1]
    # What Chapter
        chapters = get_chapters(book)
        i = 0
        print("\n")
        for chapter in chapters:
            i += 1
            print(f"    {i}: {chapter}")
        val2 = int(input("\n What chapter do you want to add to? ")) - 1
        chapter = chapters[val2]
    # What part
        parts = get_parts(book, chapter)
        i = 0
        print("\n")
        for part in parts:
            i += 1
            print(f"    {i}: {part}")
        val3 = int(input("\n What part do you want to add to? ")) - 1
        part = parts[val3]
    # Long or short
        val4 = int(input(f"\n Do you want to add a:\n 1. Short log\n 2. Long note \n  > "))
        if val4 == 1:
            val5 = input(f"\n What do you want to add to {book}/{chapter}/{part}:\n  > ")
            write_any_log(book, chapter, part, val5)
        elif val4 == 2:
            path = create_long(book, chapter, part)
            os.system(editor + " " + path) 

    def b_loop():
        try:
            log(2, f"run_menu() got b")
    # What book
            books = get_books()
            i = 0
            print("\n")
            for book in books:
                i += 1
                print(f"    {i}: {book}")
            val1 = int(input("\n What book do you want to open? (nr) ")) - 1
            book = books[val1]
    # What Chapter
            chapters = get_chapters(book)
            i = 0
            print("\n")
            for chapter in chapters:
                i += 1
                print(f"    {i}: {chapter}")
            val2 = int(input("\n What chapter do you want to open? (nr) ")) - 1
            chapter = chapters[val2]
    # What part
            parts = get_parts(book, chapter)
            i = 0
            print("\n")
            for part in parts:
                i += 1
                print(f"    {i}: {part}")
            val3 = int(input("\n What part do you want to open? (nr) ")) - 1
            part = parts[val3]
    # What note
            print(get_notes(book, chapter, part))
            val4 = int(input("\n 0: Edit a note\n What note id do you want to open?  "))
            if val4 == 0:
                val4 = int(input("\n What note id do you want to EDIT?  "))
                path = export_for_edit(val4)
                os.system(editor + " " + path)
                print(update_from_file(path))
            else:
                print_from_id(val4)
        except OSError as error:
            print(f"Something went sideways! ({error})")
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
        t Search tag
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
                    input_line = input("\nLine for log ('exit' to exit) > ")
                    if input_line == "exit":
                        print("\nReturning to start!\n")
                        runit1 = 1
                    else:
                        write_log(input_line)
                        runit1 = 2     
    # SEARCH TAG
            case "t":
                log(2, f"run_menu() got t")
                tag_search = input("\nWhat tag to seach for? (l to list existing) ")
                print(get_by_tag(tag_search))
                look_at = input("\nWant to look closer at any of them? (iD)")        
                print_from_id(look_at) 
    # Open daily file
            case "o":
                log(2, f"run_menu() got o")
                open_today()
                continue        
            case _:
                logging.error(f"run_menu() did not get a viable selection in the menu!")
                print("\nSomething went sideways, check your input!\n")
                continue


def main():
    if not os.path.exists(db_file):
        first_run()
        do_the_logging()
        run_menu()
    else:
        do_the_logging()
        run_menu()


if __name__ == "__main__":
    main()
