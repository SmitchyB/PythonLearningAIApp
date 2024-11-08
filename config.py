# Description: Configuration file for the Python Learning Game setting up the chapters and lessons structure
chapters = {  # Dictionary of chapters with lessons and questions
    1: {
        "title": "Introduction to Python and Setting Up the Environment",
        "lessons": {
            1: {"title": "What is Python?", "question_count": 3, "complexity": 1},
            2: {"title": "Installing Python and Setting up PATH", "question_count": 4, "complexity": 2},
            3: {"title": "Introduction to Python IDEs", "question_count": 5, "complexity": 2},
            4: {"title": "Running Your First Python Program", "question_count": 3, "complexity": 1},
            5: {"title": "Python Syntax and Code Structure", "question_count": 5, "complexity": 3},
            6: {"title": "Python Community and Documentation", "question_count": 3, "complexity": 1},
            7: {"title": "Troubleshooting Common Setup Issues", "question_count": 4, "complexity": 2},
            8: {"title": "Review Test: Introduction to Python"}
        }
    },
    2: {
        "title": "Variables and Data Types",
        "lessons": {
            1: {"title": "Introduction to Variables", "question_count": 4, "complexity": 1},
            2: {"title": "Numeric Data Types (int, float)", "question_count": 5, "complexity": 2},
            3: {"title": "Strings and String Manipulation", "question_count": 6, "complexity": 3},
            4: {"title": "Boolean Values and Logical Expressions", "question_count": 5, "complexity": 2},
            5: {"title": "Lists, Tuples, and Dictionaries Overview", "question_count": 7, "complexity": 3},
            6: {"title": "Variable Naming Conventions", "question_count": 4, "complexity": 1},
            7: {"title": "Type Casting and Type Checking", "question_count": 5, "complexity": 2},
            8: {"title": "Review Test: Variables and Data Types", "question_count": 14}
        }
    },
    3: {
        "title": "Control Flow (If/Else Statements)",
        "lessons": {
            1: {"title": "Introduction to Conditional Statements", "question_count": 3, "complexity": 1},
            2: {"title": "Comparison Operators and Logical Operators", "question_count": 5, "complexity": 2},
            3: {"title": "The if Statement", "question_count": 4, "complexity": 1},
            4: {"title": "else and elif Clauses", "question_count": 5, "complexity": 2},
            5: {"title": "Nested Conditions and Indentation Rules", "question_count": 6, "complexity": 3},
            6: {"title": "Short-circuiting Logic", "question_count": 4, "complexity": 2},
            7: {"title": "Writing Clean and Readable Conditions", "question_count": 5, "complexity": 2},
            8: {"title": "Review Test: Control Flow", "question_count": 13} 
        }
    },
    4: {
        "title": "Loops and Iterations (For and While Loops)",
        "lessons": {
            1: {"title": "Introduction to Loops and Iteration", "question_count": 3, "complexity": 1},
            2: {"title": "The for Loop", "question_count": 5, "complexity": 2},
            3: {"title": "The while Loop", "question_count": 5, "complexity": 2},
            4: {"title": "Loop Control with break and continue", "question_count": 4, "complexity": 2},
            5: {"title": "Nested Loops", "question_count": 7, "complexity": 3},
            6: {"title": "Iterating Over Data Structures", "question_count": 6, "complexity": 3},
            7: {"title": "Loop Optimization Techniques", "question_count": 4, "complexity": 2},
            8: {"title": "Review Test: Loops and Iterations", "question_count": 15} 
        }
    },
    5: {
        "title": "Functions and Parameters",
        "lessons": {
            1: {"title": "Defining and Calling Functions", "question_count": 5, "complexity": 2},
            2: {"title": "Function Parameters and Return Values", "question_count": 6, "complexity": 2},
            3: {"title": "Default Parameters and Keyword Arguments", "question_count": 5, "complexity": 2},
            4: {"title": "Anonymous Functions (lambda)", "question_count": 4, "complexity": 2},
            5: {"title": "Function Scope and Variable Lifetime", "question_count": 6, "complexity": 3},
            6: {"title": "Recursive Functions", "question_count": 5, "complexity": 3},
            7: {"title": "Best Practices for Modular Code", "question_count": 4, "complexity": 2},
            8: {"title": "Review Test: Functions and Parameters", "question_count": 16} 
        }
    },
    6: {
        "title": "Lists, Tuples, and Dictionaries",
        "lessons": {
            1: {"title": "Introduction to Lists", "question_count": 4, "complexity": 1},
            2: {"title": "List Methods and Operations", "question_count": 6, "complexity": 2},
            3: {"title": "Working with Tuples", "question_count": 5, "complexity": 2},
            4: {"title": "Dictionaries and Key-Value Pairs", "question_count": 6, "complexity": 2},
            5: {"title": "Nested Data Structures", "question_count": 7, "complexity": 3},
            6: {"title": "List Comprehensions", "question_count": 6, "complexity": 3},
            7: {"title": "When to Use Lists, Tuples, or Dictionaries", "question_count": 5, "complexity": 2},
            8: {"title": "Review Test: Lists, Tuples, and Dictionaries", "question_count": 15}
        }
    },
    7: {
        "title": "Strings and String Methods",
        "lessons": {
            1: {"title": "Introduction to Strings", "question_count": 4, "complexity": 1},
            2: {"title": "String Indexing and Slicing", "question_count": 6, "complexity": 2},
            3: {"title": "Common String Methods (upper(), split(), etc.)", "question_count": 6, "complexity": 2},
            4: {"title": "String Formatting (f-strings and format())", "question_count": 5, "complexity": 2},
            5: {"title": "Regular Expressions (Regex Basics)", "question_count": 7, "complexity": 3},
            6: {"title": "Handling Multi-line Strings", "question_count": 5, "complexity": 2},
            7: {"title": "Encoding and Decoding Strings", "question_count": 5, "complexity": 2},
            8: {"title": "Review Test: Strings and String Methods", "question_count": 14}
        }
    },
    8: {
        "title": "Error Handling (Try/Except Blocks)",
        "lessons": {
            1: {"title": "Introduction to Exceptions", "question_count": 4, "complexity": 1},
            2: {"title": "Using try and except", "question_count": 5, "complexity": 2},
            3: {"title": "Handling Multiple Exceptions", "question_count": 6, "complexity": 2},
            4: {"title": "The finally Block", "question_count": 5, "complexity": 2},
            5: {"title": "Raising Exceptions", "question_count": 6, "complexity": 3},
            6: {"title": "Custom Exception Classes", "question_count": 5, "complexity": 2},
            7: {"title": "Best Practices for Error Handling", "question_count": 4, "complexity": 1},
            8: {"title": "Review Test: Error Handling", "question_count": 13}
        }
    },
    9: {
        "title": "File I/O (Reading and Writing Files)",
        "lessons": {
            1: {"title": "Opening and Closing Files", "question_count": 4, "complexity": 1},
            2: {"title": "Reading Files Line by Line", "question_count": 5, "complexity": 2},
            3: {"title": "Writing Data to Files", "question_count": 5, "complexity": 2},
            4: {"title": "Working with JSON and CSV Files", "question_count": 6, "complexity": 3},
            5: {"title": "File Modes (r, w, a, etc.)", "question_count": 5, "complexity": 2},
            6: {"title": "Exception Handling with File I/O", "question_count": 4, "complexity": 1},
            7: {"title": "File Path Management and OS Integration", "question_count": 6, "complexity": 3},
            8: {"title": "Review Test: File I/O", "question_count": 14}
        }
    },
    10: {
        "title": "Modules and Packages",
        "lessons": {
            1: {"title": "Introduction to Modules", "question_count": 4, "complexity": 1},
            2: {"title": "Importing Built-in Modules", "question_count": 5, "complexity": 2},
            3: {"title": "Creating Custom Modules", "question_count": 6, "complexity": 3},
            4: {"title": "Understanding Python Packages", "question_count": 5, "complexity": 2},
            5: {"title": "Using pip to Manage Dependencies", "question_count": 5, "complexity": 2},
            6: {"title": "Relative vs Absolute Imports", "question_count": 5, "complexity": 2},
            7: {"title": "Best Practices for Modular Code", "question_count": 4, "complexity": 1},
            8: {"title": "Review Test: Modules and Packages", "question_count": 13}
        }
    },
    11: {
        "title": "Object-Oriented Programming (OOP) Basics",
        "lessons": {
            1: {"title": "Introduction to Classes and Objects", "question_count": 4, "complexity": 1},
            2: {"title": "Defining Class Attributes and Methods", "question_count": 6, "complexity": 2},
            3: {"title": "The __init__ Method (Constructor)", "question_count": 5, "complexity": 2},
            4: {"title": "Encapsulation and Access Modifiers", "question_count": 6, "complexity": 3},
            5: {"title": "Working with Instances and Objects", "question_count": 5, "complexity": 2},
            6: {"title": "Magic Methods (__str__, __repr__, etc.)", "question_count": 4, "complexity": 2},
            7: {"title": "Practical Examples of OOP", "question_count": 5, "complexity": 2},
            8: {"title": "Review Test: Object-Oriented Programming Basics", "question_count": 14}
        }
    },
    12: {
        "title": "Advanced OOP Concepts (Inheritance and Polymorphism)",
        "lessons": {
            1: {"title": "Introduction to Inheritance", "question_count": 5, "complexity": 2},
            2: {"title": "Method Overriding", "question_count": 5, "complexity": 2},
            3: {"title": "Polymorphism in Python", "question_count": 6, "complexity": 3},
            4: {"title": "Multiple Inheritance", "question_count": 6, "complexity": 3},
            5: {"title": "Abstract Classes and Interfaces", "question_count": 7, "complexity": 3},
            6: {"title": "Composition vs Inheritance", "question_count": 5, "complexity": 2},
            7: {"title": "Real-World OOP Examples", "question_count": 5, "complexity": 2},
            8: {"title": "Review Test: Advanced OOP Concepts", "question_count": 17}
        }
    },
    13: {
        "title": "Functional Programming with Lambdas and Higher-Order Functions",
        "lessons": {
            1: {"title": "Introduction to Functional Programming", "question_count": 4, "complexity": 1},
            2: {"title": "Lambda Functions", "question_count": 5, "complexity": 2},
            3: {"title": "Using map(), filter(), and reduce()", "question_count": 6, "complexity": 3},
            4: {"title": "Closures and Decorators", "question_count": 6, "complexity": 3},
            5: {"title": "Composing Functions", "question_count": 5, "complexity": 2},
            6: {"title": "Pure Functions and Side Effects", "question_count": 5, "complexity": 2},
            7: {"title": "When to Use Functional Programming", "question_count": 4, "complexity": 1},
            8: {"title": "Review Test: Functional Programming", "question_count": 14}
        }
    },
    14: {
        "title": "Working with APIs (HTTP Requests)",
        "lessons": {
            1: {"title": "Introduction to APIs", "question_count": 4, "complexity": 1},
            2: {"title": "Using the requests Library", "question_count": 5, "complexity": 2},
            3: {"title": "Sending GET and POST Requests", "question_count": 6, "complexity": 3},
            4: {"title": "Handling API Responses (JSON)", "question_count": 5, "complexity": 2},
            5: {"title": "Authentication with APIs", "question_count": 6, "complexity": 3},
            6: {"title": "Handling API Errors", "question_count": 5, "complexity": 2},
            7: {"title": "Building Simple API Clients", "question_count": 5, "complexity": 2},
            8: {"title": "Review Test: Working with APIs", "question_count": 15}
        }
    },
    15: {
        "title": "Data Handling with CSVs, JSON, and Pandas",
            "lessons": {
            1: {"title": "Reading CSV Files", "question_count": 4, "complexity": 1},
            2: {"title": "Writing to CSV Files", "question_count": 5, "complexity": 2},
            3: {"title": "Working with JSON Data", "question_count": 6, "complexity": 3},
            4: {"title": "Introduction to Pandas DataFrames", "question_count": 5, "complexity": 2},
            5: {"title": "Basic Data Manipulation with Pandas", "question_count": 6, "complexity": 3},
            6: {"title": "Data Cleaning Techniques", "question_count": 5, "complexity": 2},
            7: {"title": "Exporting Data to Files", "question_count": 4, "complexity": 1},
            8: {"title": "Review Test: Data Handling with CSVs, JSON, and Pandas", "question_count": 14}
        }
    },
    16: {
        "title": "Testing and Debugging",
        "lessons": {
            1: {"title": "Introduction to Unit Testing", "question_count": 4, "complexity": 1},
            2: {"title": "Writing Tests with unittest", "question_count": 5, "complexity": 2},
            3: {"title": "Mocking and Patching", "question_count": 6, "complexity": 3},
            4: {"title": "Debugging with pdb", "question_count": 5, "complexity": 2},
            5: {"title": "Logging for Debugging", "question_count": 5, "complexity": 2},
            6: {"title": "Handling Test Failures", "question_count": 4, "complexity": 1},
            7: {"title": "Test-Driven Development (TDD)", "question_count": 6, "complexity": 3},
            8: {"title": "Review Test: Testing and Debugging", "question_count": 14}
        }
    },
    17: {
        "title": "Databases and SQL Basics",
        "lessons": {
            1: {"title": "Introduction to Databases", "question_count": 4, "complexity": 1},
            2: {"title": "Connecting to SQLite with Python", "question_count": 5, "complexity": 2},
            3: {"title": "Executing SQL Queries", "question_count": 6, "complexity": 3},
            4: {"title": "Handling SQL Results", "question_count": 5, "complexity": 2},
            5: {"title": "Inserting and Updating Data", "question_count": 6, "complexity": 3},
            6: {"title": "Working with Relationships", "question_count": 5, "complexity": 2},
            7: {"title": "Using ORMs (SQLAlchemy Basics)", "question_count": 6, "complexity": 3},
            8: {"title": "Review Test: Databases and SQL Basics", "question_count": 16}
        }
    },
    18: {
        "title": "Multithreading and Asynchronous Programming",
        "lessons": {
            1: {"title": "Introduction to Multithreading", "question_count": 4, "complexity": 1},
            2: {"title": "Using the threading Module", "question_count": 6, "complexity": 2},
            3: {"title": "Introduction to Asynchronous Programming", "question_count": 6, "complexity": 3},
            4: {"title": "Writing Async Functions with asyncio", "question_count": 5, "complexity": 2},
            5: {"title": "Handling Concurrency Issues", "question_count": 6, "complexity": 3},
            6: {"title": "Performance Optimization with Threads", "question_count": 5, "complexity": 2},
            7: {"title": "Real-World Async Examples", "question_count": 6, "complexity": 3},
            8: {"title": "Review Test: Multithreading and Asynchronous Programming", "question_count": 16}
        }
    },
    19: {
        "title": "Working with Virtual Environments and Dependency Management",
        "lessons": {
            1: {"title": "Introduction to Virtual Environments", "question_count": 4, "complexity": 1},
            2: {"title": "Creating and Activating Virtual Environments", "question_count": 5, "complexity": 2},
            3: {"title": "Managing Dependencies with pip", "question_count": 5, "complexity": 2},
            4: {"title": "Using requirements.txt Files", "question_count": 4, "complexity": 1},
            5: {"title": "Using pipenv or Poetry for Advanced Management", "question_count": 6, "complexity": 3},
            6: {"title": "Avoiding Dependency Conflicts", "question_count": 5, "complexity": 2},
            7: {"title": "Best Practices for Environment Management", "question_count": 4, "complexity": 1},
            8: {"title": "Review Test: Virtual Environments and Dependency Management", "question_count": 12}
        }
    },
    20: {
        "title": "Deploying Python Applications",
        "lessons": {
            1: {"title": "Introduction to Deployment", "question_count": 4, "complexity": 1},
            2: {"title": "Packaging Code with PyInstaller", "question_count": 5, "complexity": 2},
            3: {"title": "Creating Web Apps with Flask or FastAPI", "question_count": 6, "complexity": 3},
            4: {"title": "Hosting on Platforms like Heroku or AWS", "question_count": 5, "complexity": 2},
            5: {"title": "Using Docker for Containerization", "question_count": 6, "complexity": 3},
            6: {"title": "Continuous Integration and Deployment (CI/CD)", "question_count": 5, "complexity": 2},
            7: {"title": "Best Practices for Production Deployment", "question_count": 4, "complexity": 1},
            8: {"title": "Review Test: Deploying Python Applications", "question_count": 14}
        }
    },
    21: {
        "title": "Cumulative Review Test: All Chapters",
        "lessons": {
            1: {
                "title": "Final Cumulative Review",
                "question_count": 100
            }
        }
    }
}