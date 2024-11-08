import sqlite3 # Import the SQLite3 module to interact with the SQLite database

def initialize_database(): # Function to initialize the SQLite database
    # Connect to the SQLite database (creates the file if it doesn't exist)
    conn = sqlite3.connect('progress.db') # The database file is named progress.db
    cursor = conn.cursor() # Create a cursor object to interact with the database

    # Create the users table (if it doesn't already exist)
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        chapter INTEGER DEFAULT 1,
        lesson INTEGER DEFAULT 1
    )
    ''')

    # Create the mistakes table (if it doesn't already exist)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        chapter INTEGER NOT NULL,
        lesson INTEGER NOT NULL,
        question TEXT NOT NULL,
        user_answer TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        feedback TEXT,
        user_code TEXT,
        user_output TEXT,
        user_errors TEXT,
        original_lesson INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create the lesson_content table (if it doesn't already exist)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lesson_content (
        user_id INTEGER NOT NULL,
        chapter INTEGER NOT NULL,
        lesson INTEGER NOT NULL,
        content TEXT NOT NULL,
        PRIMARY KEY (user_id, chapter, lesson),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create the lesson_scores table (if it doesn't already exist)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lesson_scores (
        user_id INTEGER NOT NULL,
        chapter INTEGER NOT NULL,
        lesson INTEGER NOT NULL,
        correct INTEGER NOT NULL,
        total INTEGER NOT NULL,
        PRIMARY KEY (user_id, chapter, lesson),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit() # Commit the changes to the database
    conn.close() # Close the connection to the database

# Call the function to initialize the database
initialize_database()
