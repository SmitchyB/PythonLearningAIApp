import sqlite3 # Import the SQLite3 module
# Connect to the SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect('progress.db') # Create a connection object
cursor = conn.cursor() # Create a cursor object

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

# Commit changes and close the connection
conn.commit() # Save changes
conn.close() # Close the connection