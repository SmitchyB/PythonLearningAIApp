from colorama import Fore, init # Import the Fore and init functions from colorama to change text color
import sqlite3 # Import the sqlite3 module to work with SQLite databases
import bcrypt # Import the bcrypt module for password hashing
from config import chapters # Import the chapters dictionary from config.py to access the lesson content
from questions import validate_answer_with_gpt, generate_lesson_content, generate_questions_from_content, generate_review_questions, generate_cumulative_review # Import functions from questions.py to generate questions, reviews, lesson content, and validate answers for code and scenario questions.
from fuzzywuzzy import fuzz # Import the fuzz function from fuzzywuzzy to compare strings
import subprocess # Import the subprocess module to run the user's code
import sys # Import the sys module to access system-specific parameters and functions
import random # Import the random module to generate random numbers

#Run the user's code and capture output or errors
def run_user_code(code): # Define the run_user_code function
    try: # Try to run the user's code
        # Use subprocess to run the code and capture both stdout and stderr
        result = subprocess.run( # Run the code with subprocess
            [sys.executable, "-c", code],  # Run code with the current Python interpreter
            capture_output=True, text=True, timeout=5 # Capture output as text and set a timeout
        )
        return result.stdout.strip(), result.stderr.strip() # Return the output and errors
    except subprocess.TimeoutExpired: # Handle timeouts
        return "", "Execution timed out." # Return an error message for timeouts

# Initialize colorama to reset color after each print
init(autoreset=True) # Initialize colorama

# Registers new users
def register_user(): # Define the register_user function
    name = input("Enter your name: ").strip() # Get the user's name
    email = input("Enter your email: ").strip() # Get the user's email
    password = input("Enter your password: ").strip() # Get the user's password

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()) # Hash the user's password

    try: # Try to insert the user into the database
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute an SQL query
                'INSERT INTO users (name, email, password) VALUES (?, ?, ?)', # Insert the user's name, email, and password
                (name, email, hashed_password) # Pass the user's name, email, and hashed password as parameters
            )
            conn.commit() # Commit the transaction
    except sqlite3.IntegrityError: # Handle duplicate email errors
        print(Fore.RED + "Error: A user with that email already exists.") # Print an error message

# Logs in existing users
def login_user(): # Define the login_user function
    email = input("Enter your email: ").strip() # Get the user's email
    password = input("Enter your password: ").strip() # Get the user's password

    try: # Try to retrieve the user from the database
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object 
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,)) # Execute an SQL query
            user = cursor.fetchone() # Fetch the first row from the result set

        if user and user[3] and bcrypt.checkpw(password.encode(), user[3]): # Check if the user exists and the password is correct
            print(Fore.GREEN + f"Welcome, {user[1]}!") # Print a welcome message
            return user # Return the user
        else: # Handle invalid email or password
            print(Fore.RED + "Invalid email or password.") # Print an error message
    except sqlite3.Error as e: # Handle database errors
        print(Fore.RED + f"Database error: {e}") # Print an error message
    return None # Return None if the login fails

# Track user progress and score
class UserProgress: # Define the UserProgress class
    
    # Initialize the UserProgress class
    def __init__(self, user_id): # Define the __init__ function
        self.user_id = user_id # Set the user ID
        self.chapter = 1  # Start at Chapter 1
        self.lesson = 1  # Start at Lesson 1
        
    # Add a mistake to the lesson
    def add_mistake(self, chapter, lesson, question, user_answer, correct_answer, feedback=None, user_code=None, user_output=None, user_errors=None, original_lesson=None): # Define the add_mistake function
        try: # Try to add the mistake to the database
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    INSERT INTO mistakes (user_id, chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (self.user_id, chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson) # Pass the parameters
                )
                conn.commit() # Commit the transaction
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to add mistake: {e}") # Print an error message

    # show the user's mistakes
    def show_mistakes(self): # Define the show_mistakes function
        try: # Try to retrieve the user's mistakes from the database
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    SELECT chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson
                    FROM mistakes
                    WHERE user_id = ?
                    ORDER BY chapter, lesson
                    ''',
                    (self.user_id,) # Pass the user ID as a parameter
                )
                mistakes = cursor.fetchall() # Fetch all rows from the result set

            if not mistakes: # Check if there are no mistakes
                print(Fore.YELLOW + "No mistakes recorded yet.") # Print a message if there are no mistakes
                return # Return if there are no mistakes

            print(Fore.RED + "Mistakes:") 
            current_lesson_key = None # Initialize the current lesson key
            for mistake in mistakes: # Iterate over the mistakes
                chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson = mistake # Unpack the mistake
                lesson_key = f'Chapter {chapter} Lesson {lesson}' # Set the lesson key
                if lesson_key != current_lesson_key: # Check if the lesson key is different from the current lesson key
                    print(f"\n{lesson_key}:") # Print the lesson key
                    current_lesson_key = lesson_key # Update the current lesson key
                print(f"Question: {question}") # Print the question
                print(f"Your Answer: {user_answer}") # Print the user's answer
                print(f"Correct Answer: {correct_answer}") # Print the correct answer
                if feedback: # Check if there is feedback
                    print(f"Feedback: {feedback}") # Print the feedback
                if user_code: # Check if there is user code
                    print(f"Your Code:\n{user_code}") # Print the user's code
                if user_output: # Check if there is user output
                    print(f"Your Code Output:\n{user_output}") # Print the user's output
                if user_errors: # Check if there are user errors
                    print(f"Your Code Errors:\n{user_errors}") # Print the user's errors
                if original_lesson: # Check if there is an original lesson
                    print(f"Original Lesson: {original_lesson}")  # Display original_lesson if present
                print()  # Blank line for readability
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to retrieve mistakes: {e}") # Print an error message

    # save the user's progress       
    def save_progress(self): # Define the save_progress function
        try: # Try to save the user's progress to the database
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    'UPDATE users SET chapter = ?, lesson = ? WHERE id = ?', # Update the user's chapter and lesson
                    (self.chapter, self.lesson, self.user_id) # Pass the chapter, lesson, and user ID as parameters
                )
                conn.commit() # Commit the transaction
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to save progress: {e}") # Print an error message

    #calculate the chapter score
    def calculate_chapter_score(progress): # Define the calculate_chapter_score function
        try: # Try to calculate the chapter score
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    SELECT SUM(correct), SUM(total)
                    FROM lesson_scores
                    WHERE user_id = ? AND chapter = ?
                    ''',
                    (progress.user_id, progress.chapter) # Pass the user ID and chapter as parameters
                )
                row = cursor.fetchone() # Fetch the first row from the result set
                if row and row[1] > 0: # Check if the row exists and the total is greater than 0
                    total_correct, total_questions = row # Unpack the row
                    return calculate_percentage_score(total_correct, total_questions) # Calculate the percentage score
                else: # Handle no results
                    return 0 # Return 0 if there are no results
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to calculate chapter score: {e}") # Print an error message
            return 0 # Return 0 if there is an error
    
    # Update the score for the current lesson
    def update_score(self, correct, total): # Define the update_score function
        """Update the score for the current lesson."""
        if self.chapter not in self.lesson_scores: # Check if the chapter is not in the lesson scores
            self.lesson_scores[self.chapter] = [] # Initialize the chapter in the lesson scores
        self.lesson_scores[self.chapter].append({ # Append the lesson score to the chapter
            'lesson': self.lesson, # Set the lesson number
            'correct': correct, # Set the number of correct answers
            'total': total # Set the total number of questions
        })
    
# Helper function to calculate the percentage score
def calculate_percentage_score(correct, total): # Define the calculate_percentage_score function
    return (correct / total) * 100 if total > 0 else 0 # Calculate the percentage score

#Function to select a lesson within a chapter
def select_lesson(progress, chapter): # Define the select_lesson function
    while True: # Loop to select a lesson
        print(f"\nSelect a Lesson for Chapter {chapter}:") # Print the lesson selection prompt
        
        total_lessons_in_chapter = len(chapters[chapter]['lessons']) - 1  # Subtract 1 for the review test

        # Determine which lessons are unlocked
        if chapter == progress.chapter: # User is in the current chapter
            if progress.lesson > total_lessons_in_chapter: # User has completed all lessons, include the chapter review test
                unlocked_lessons = range(1, total_lessons_in_chapter + 2) # Include the review test
            else: # User is in the middle of the chapter
                unlocked_lessons = range(1, progress.lesson + 1) # Include the current lesson
        else: # User is in a future chapter
            unlocked_lessons = [1] # Only the first lesson is unlocked

        # Display unlocked lessons
        for lesson in unlocked_lessons: # Iterate over the unlocked lessons
            if lesson <= total_lessons_in_chapter: # Check if the lesson is not the review test
                print(f"{lesson}) {chapters[chapter]['lessons'][lesson]['title']}") # Print the lesson number and title
            else: # Handle the review test
                print(f"{lesson}) Review Test: {chapters[chapter]['title']}") # Print the review test

        lesson_choice = input("Enter the lesson number (or 'B' to go back): ").strip() # Get the user's lesson choice

        if lesson_choice.lower() == 'b': # Check if the user selected to go back
            return  # Go back to chapter selection

        if not lesson_choice.isdigit() or int(lesson_choice) not in unlocked_lessons: # Check if the user's lesson choice is invalid
            print(Fore.RED + "Invalid lesson number.") # Print an error message
            continue # Continue to the next iteration

        lesson = int(lesson_choice) # Convert the lesson choice to an integer

        if lesson <= total_lessons_in_chapter: # Check if the lesson is not the review test
            print(Fore.GREEN + "Retrieving lesson content...") # Print a message to retrieve the lesson content
            lesson_content = generate_lesson_content(progress, chapter, lesson) # Generate the lesson content
            play_lesson(progress, chapter, lesson, lesson_content) # Play the lesson
        else: # Handle the review test
            if progress.lesson > total_lessons_in_chapter: # Check if the user has completed all lessons
                passed = review_test(progress) # Conduct the review test
                if passed: # Check if the user passed the review test
                    progress.chapter += 1 # Advance to the next chapter
                    progress.lesson = 1 # Reset the lesson to 1
                    progress.save_progress() # Save the progress
                    print(Fore.GREEN + "You have advanced to the next chapter!") # Print a success message
                    return  # Go back to chapter selection
                else: # Handle failing the review test
                    print(Fore.RED + "Please review the lessons and try again.") # Print an error message
            else: # Handle attempting the review test before completing all lessons
                print(Fore.RED + "You need to complete all lessons before taking the review test.") # Print an error message

# Function to generate the lesson content, questions and track user progress
def play_lesson(progress, chapter, lesson, lesson_content): # Define the play_lesson function
    try: # Try to clear the user's previous mistakes
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute an SQL query
                '''
                DELETE FROM mistakes WHERE user_id = ? AND chapter = ? AND lesson = ?
                ''',
                (progress.user_id, chapter, lesson) # Pass the user ID, chapter, and lesson as parameters
            )
            conn.commit() # Commit the transaction
    except sqlite3.Error as e: # Handle database errors
        print(f"Failed to clear previous mistakes: {e}") # Print an error message

    print(Fore.CYAN + f"\n--- {chapters[chapter]['title']} ---") # Print the chapter title
    print(Fore.CYAN + f"--- Lesson {lesson}: {chapters[chapter]['lessons'][lesson]['title']} ---") # Print the lesson title

    print(Fore.YELLOW + "\nLesson Content:\n") # Print the lesson content header
    print(lesson_content) # Print the lesson content

    # Generate questions based on the lesson content
    question_count = chapters[chapter]['lessons'][lesson].get('question_count') # Get the question count for the lesson
    if not question_count: # Check if the question count is missing
        print(Fore.RED + "Error: No question count specified for this lesson.") # Print an error message
        return # Return if the question count is missing

    questions = generate_questions_from_content(chapter, lesson, lesson_content, question_count) # Generate questions from the lesson content

    correct_answers = 0 # Initialize the number of correct answers

    # For each question in the lesson, run the ask_question_and_validate function and track the correct answers
    for i, question_data in enumerate(questions): # Iterate over the questions
        print(f"\nQuestion {i + 1}/{question_count}:") # Print the question number
        correct = ask_question_and_validate(question_data, progress, chapter, lesson) # Ask the question and validate the answer

        if correct: # Check if the answer is correct
            correct_answers += 1 # Increment the correct answers count

    print(f"\nLesson {lesson} complete! You answered {correct_answers} out of {question_count} correctly.") # Print the lesson completion message

    try: # Try to save the lesson score to the database
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute an SQL query
                '''
                INSERT OR REPLACE INTO lesson_scores (user_id, chapter, lesson, correct, total)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (progress.user_id, chapter, lesson, correct_answers, question_count) # Pass the parameters
            ) 
            conn.commit() # Commit the transaction
    except sqlite3.Error as e: # Handle database errors
        print(f"Failed to save lesson score: {e}") # Print an error message

    # Unlock the next lesson if applicable
    total_lessons_in_chapter = len(chapters[chapter]['lessons']) - 1  # Exclude the review test
    if lesson < total_lessons_in_chapter: # Check if the lesson is not the last lesson
        progress.lesson += 1 # Advance to the next lesson
    else: # Handle completing all lessons in the chapter
        progress.lesson = total_lessons_in_chapter + 1 # Include the review test as the next lesson
        print(Fore.GREEN + "You have completed all lessons in this chapter!") # Print a success message

    progress.save_progress() # Save the user's progress

# Function to ask questions and validate answers **ChatGPT was used to assist with the creation of this function**
def ask_question_and_validate(question_data, progress=None, chapter=None, lesson=None): # Define the ask_question_and_validate function
    # Validate the question data
    if not question_data or 'question' not in question_data: # Check if the question data is missing or invalid
        raise ValueError("Error: Question data is missing or invalid.") # Raise a ValueError

    print(Fore.CYAN + f"\n{question_data['question']}") # Print the question
    original_lesson = question_data.get('original_lesson') # Get the original lesson number

    # Display multiple choice questions with the options, labels, and texts
    if question_data['type'] == "multiple_choice" and 'options' in question_data: # Check if the question type is multiple choice
        # Log and print each option as it is processed
        for label, option_text in question_data['options'].items(): # Iterate over the options
            print(f"{label}: {option_text}") # Print the option

        # Get user input and validate it
        user_answer = input("Enter the letter of your answer (A, B, C, D): ").strip().upper() # Get the user's answer

        # Validate input
        if user_answer not in question_data['options']: # Check if the user's answer is invalid
            print(Fore.RED + "Invalid input.") # Print an error message
            return False # Return False for an invalid answer

        # Check if the answer is correct
        correct = user_answer == question_data['correct_answer'] # Check if the user's answer is correct
        if correct: # Handle correct answers
            print(Fore.GREEN + "Correct!") # Print a success message
        else: # Handle incorrect answers
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}")  # Print an error message
            if progress and chapter is not None and lesson is not None: # Check if progress tracking is enabled
                progress.add_mistake( # Add the mistake to the progress tracker
                    chapter=chapter, # Pass the chapter number
                    lesson=lesson, # Pass the lesson number
                    question=question_data['question'], # Pass the question text
                    user_answer=user_answer, # Pass the user's answer
                    correct_answer=question_data['correct_answer'], # Pass the correct answer
                    original_lesson=original_lesson # Pass the original lesson number
                )
        return correct  # Return the correctness of the answer

    # Display true or false questions   
    elif question_data['type'] == "true_false": # Check if the question type is true or false
        user_answer = input("True or False? ").strip().lower() # Get the user's answer
        correct = user_answer == question_data['correct_answer'].lower() # Check if the user's answer is correct
        if correct: # Handle correct answers
            print(Fore.GREEN + "Correct!") # Print a success message
        else: # Handle incorrect answers
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}")  # Print an error message
            if progress and chapter is not None and lesson is not None: # Check if progress tracking is enabled
                progress.add_mistake( # Add the mistake to the progress tracker
                    chapter=chapter, # Pass the chapter number
                    lesson=lesson, # Pass the lesson number
                    question=question_data['question'], # Pass the question text
                    user_answer=user_answer, # Pass the user's answer
                    correct_answer=question_data['correct_answer'], # Pass the correct answer
                    original_lesson=original_lesson # Pass the original lesson number
                )
        return correct # Return the correctness of the answer

    # Display fill in the blank questions
    elif question_data['type'] == "fill_in_the_blank": # Check if the question type is fill in the blank
        user_answer = input("Fill in the blank: ").strip().lower() # Get the user's answer
        correct = user_answer == question_data.get('correct_answer', '').lower() # Check if the user's answer is correct
        if correct: # Handle correct answers
            print(Fore.GREEN + "Correct!") # Print a success message
        else: # Handle incorrect answers
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}")  # Print an error message
            if progress and chapter is not None and lesson is not None: # Check if progress tracking is enabled
                progress.add_mistake( # Add the mistake to the progress tracker
                    chapter=chapter, # Pass the chapter number
                    lesson=lesson, # Pass the lesson number
                    question=question_data['question'], # Pass the question text
                    user_answer=user_answer, # Pass the user's answer
                    correct_answer=question_data['correct_answer'], # Pass the correct answer
                    original_lesson=original_lesson # Pass the original lesson number
                )
        return correct # Return the correctness of the answer

    # Display write code questions
    elif question_data['type'] == "write_code": # Check if the question type is write code
        print(Fore.CYAN + "\nWrite your code solution below. Use multiple lines if needed. Type 'END' on a new line when finished:") # Print the code prompt

        # Collect multi-line user code input
        user_code = "" # Initialize the user's code
        while True: # Loop to collect the user's code
            line = input() # Get the user's code line by line
            if line.strip().upper() == "END": # Check if the user has finished entering code
                break # Exit the loop
            user_code += line + "\n" # Append the user's code to the full code

        # Run the user's code and capture output or errors
        user_output, user_errors = run_user_code(user_code) # Run the user's code

        if user_errors: # Handle errors
            print(f"\nYour code produced the following error:\n{user_errors}") # Print the error message
        else: # Handle output
            print(f"\nYour code produced the following output:\n{user_output}") # Print the output

        # Validate the user's solution using GPT
        correct, feedback = validate_answer_with_gpt( # Validate the user's answer with GPT
            question_data, user_code=user_code, user_output=user_output # Pass the question data, user code, and user output
        )

        # Display the result based on GPT validation
        if correct:  # Handle correct answers
            print(Fore.GREEN + "Correct! Well done.") # Print a success message
        else: # Handle incorrect answers
            print(Fore.RED + "Incorrect. Review the feedback below:") # Print an error message
            print(Fore.YELLOW + feedback) # Print the feedback
            if progress and chapter is not None and lesson is not None and not correct: # Check if progress tracking is enabled
                progress.add_mistake( # Add the mistake to the progress tracker
                    chapter=chapter, # Pass the chapter number
                    lesson=lesson, # Pass the lesson number
                    question=question_data['question'], # Pass the question text
                    user_answer=user_code, # Pass the user's code
                    correct_answer=question_data['correct_answer'], # Pass the correct answer
                    feedback=feedback, # Pass the feedback
                    user_code=user_code, # Pass the user's code
                    user_output=user_output if not user_errors else None, # Pass the user's output if there are no errors
                    user_errors=user_errors if user_errors else None, # Pass the user's errors if there are errors
                    original_lesson=original_lesson # Pass the original lesson number
                )
        return correct # Return the correctness of the answer

    # Display scenario questions
    elif question_data['type'] == "scenario": # Check if the question type is a scenario
        user_response = input("Describe your response to the scenario: ").strip() # Get the user's response

        # Validate the user's response using GPT
        correct, feedback = validate_answer_with_gpt(
            question_data=question_data,  # Pass the full dictionary
            user_response=user_response # Pass the user's response
        )

        # Display the result based on GPT validation
        if correct: # Handle correct answers
            print(Fore.GREEN + "Correct! Well done.") # Print a success message
        else: # Handle incorrect answers
            print(Fore.RED + "Incorrect. Review the feedback below:") # Print an error message
            print(Fore.YELLOW + feedback) # Print the feedback
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}")  # Print an error message
        if progress and chapter is not None and lesson is not None and not correct: # Check if progress tracking is enabled
            progress.add_mistake( # Add the mistake to the progress tracker
                chapter=chapter, # Pass the chapter number
                lesson=lesson, # Pass the lesson number
                question=question_data['question'], # Pass the question text
                user_answer=user_response, # Pass the user's response
                correct_answer=question_data['correct_answer'], # Pass the correct answer
                feedback=feedback, # Pass the feedback
                original_lesson=original_lesson # Pass the original lesson number
            )
        return correct # Return the correctness of the answer

# Function to generate review questions
def review_test(progress): # Define the review_test function
    chapter = progress.chapter # Get the current chapter
    try: # Try to clear the user's previous mistakes
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            # Assuming lesson number for review test is always set to 8
            cursor.execute( # Execute an SQL query
                '''
                DELETE FROM mistakes WHERE user_id = ? AND chapter = ? AND lesson = ?
                ''',
                (progress.user_id, chapter, 8) # Pass the user ID, chapter, and lesson as parameters
            )
            conn.commit() # Commit the transaction
    except sqlite3.Error as e: # Handle database errors
        print(f"Failed to clear previous mistakes: {e}") # Print an error message

    questions = generate_review_questions(progress, chapter) # Generate review questions for the chapter
    correct_answers = 0 # Initialize the number of correct answers

    print(Fore.MAGENTA + f"\n--- Review Test: {chapters[chapter]['title']} ---") # Print the review test title
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score

    for i, question_data in enumerate(questions): # Iterate over the questions
        print(f"\nQuestion {i + 1}/{len(questions)}:") # Print the question number
        correct = ask_question_and_validate(question_data, progress, chapter, lesson=8) # Ask the question and validate the answer
        if correct: # Handle correct answers
            correct_answers += 1 # Increment the correct answers count

    if correct_answers >= int(len(questions) * 0.7): # Check if the user passed the review
        print(Fore.GREEN + "Congratulations! You passed the review.\n") # Print a success message
        return True # Return True for passing the review
    else: # Handle failing the review
        print(Fore.RED + "You did not pass the review. Try again!\n") # Print an error message
        return False # Return False for failing the review

#Function to generate cumulative review questions **currently note working as intended**
def cumulative_review_test(progress): # Define the cumulative_review_test function
    """Conduct the cumulative review covering all chapters and return pass status.""" 
    questions = generate_cumulative_review(progress) # Generate cumulative review questions
    correct_answers = 0 # Initialize the number of correct answers
 
    print(Fore.MAGENTA + "\n--- Final Cumulative Review: All Chapters ---") # Print the cumulative review title
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score
    
    # For each question in the cumulative review, run the ask_question_and_validate function and track the correct answers
    for i, question_data in enumerate(questions): # Iterate over the questions
        print(f"\nQuestion {i + 1}/{len(questions)}:") # Print the question number
        chapter = question_data.get('chapter', 1) # Get the chapter number
        lesson = question_data.get('lesson', None) # Get the lesson number
        if ask_question_and_validate(question_data, progress, chapter, lesson): # Ask the question and validate the answer
            correct_answers += 1 # Increment the correct answers count
        else: # Handle incorrect answers
            chapter = question_data.get('chapter', 1)  # Track which chapter the mistake came from
            progress.add_review_mistake(chapter) # Track the review mistakes

    # Check if the user passed the cumulative review
    if correct_answers >= int(len(questions) * 0.7): # Check if the user passed the cumulative review
        print(Fore.GREEN + "Congratulations! You passed the cumulative review!\n") # Print a success message
        return True # Return True for passing the cumulative review
    else: # Handle failing the cumulative review
        print(Fore.RED + "You did not pass the cumulative review. Please try again.\n") # Print an error message
        return False # Return False for failing the cumulative review

# Main game loop    
def play_game(progress): # Define the play_game function
    # while loop to allow the user to select a chapter
    while True: # Loop to select a chapter
        print("\nSelect a Chapter:") # Print the chapter selection prompt
        unlocked_chapters = range(1, progress.chapter + 1) # Limit to unlocked chapters

        #for each chapter in the unlocked chapters print the chapter number and title
        for chapter in unlocked_chapters:  # Iterate over the unlocked chapters
            print(f"{chapter}) {chapters[chapter]['title']}") # Print the chapter number and title

        chapter_choice = input("Enter the chapter number (or 'B' to go back): ").strip() # Get the user's chapter choice

        #if the user selects 'B' go back to the main menu
        if chapter_choice.lower() == 'b': # Check if the user selected to go back
            return  # Go back to main menu

        #if the user's chapter choice is invalid print an error message
        if not chapter_choice.isdigit() or int(chapter_choice) not in unlocked_chapters: # Check if the user's chapter choice is invalid
            print(Fore.RED + "Invalid chapter number.") # Print an error message
            continue # Continue to the next iteration

        #if the user's chapter choice is valid select the lesson
        chapter = int(chapter_choice) # Convert the chapter choice to an integer
        select_lesson(progress, chapter) # Select the lesson

#Function to welcome users  
def welcome(): # Define the welcome function
    while True: # Loop to display the welcome screen
        print("\n--- Welcome ---") # Print the welcome message
        print("1) Log In") # Print the log in option
        print("2) Register") # Print the register option
        print("4) Exit") # Print the exit option

        choice = input("Select an option (1-4): ").strip() # Get the user's choice

        #if the user selects '1' log them in
        if choice == '1': # Check if the user selected log in
            user = login_user() # Log in the user
            if user: # Check if the user is valid
                progress = UserProgress(user[0])  # Restore progress 
                progress.chapter = user[4]  # Restore chapter
                progress.lesson = user[5] # Restore lesson
                main_menu(progress)  # Go to the post-login menu

        #if the user selects '2' register them
        elif choice == '2': # Check if the user selected register
            register_user() # Register the user
            print(Fore.GREEN + "\nRegistration complete! Please log in.") # Print a success message
            
        #if the user selects '4' exit the program
        elif choice == '4': # Check if the user selected to exit
            print(Fore.GREEN + "Goodbye!") # Print a goodbye message
            break # Exit the loop

        #if the user's choice is invalid print an error message
        else: # Handle invalid choices
            print(Fore.RED + "Invalid choice. Please select 1, 2, 3, or 4.") # Print an error message

#Function to display the main menu
def main_menu(progress): # Define the main_menu function
    while True: # Loop to display the main menu
        print("\n--- Main Menu ---") # Print the main menu options
        print("1) Play") # Print the play option
        print("2) Show Mistakes") # Print the show mistakes option
        print("3) Display Lesson Content")  # New option added
        print("4) Exit") # Print the exit option
        print("5) Testing Mode")  # If you have testing mode as option 5

        choice = input("Select an option (1-5): ").strip() # Get the user's choice

        if choice == '1': # Check if the user selected play
            play_game(progress) # Play the game
        elif choice == '2': # Check if the user selected show mistakes
            show_mistakes_menu(progress) # Show the user's mistakes
        elif choice == '3': # Check if the user selected the new option
            display_lesson_content_menu(progress)  # Display the lesson content
        elif choice == '4': # Check if the user selected exit
            print(Fore.GREEN + "Goodbye!") # Print a goodbye message
            break # Exit the loop
        elif choice == '5': # Check if the user selected testing mode
            testing_mode(progress) # Enter testing mode
        else: # Handle invalid choices
            print(Fore.RED + "Invalid choice. Please select 1-5.") # Print an error message

#Function to display the lesson content
def display_lesson_content_menu(progress): # Define the display_lesson_content_menu function
    try: # Try to retrieve the lesson content from the database
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute an SQL query
                '''
                SELECT DISTINCT chapter, lesson
                FROM lesson_content
                WHERE user_id = ?
                ORDER BY chapter, lesson
                ''',
                (progress.user_id,) # Pass the user ID as a parameter
            )
            lessons = cursor.fetchall() # Fetch all the lessons
        if not lessons: # Check if there are no lessons
            print(Fore.YELLOW + "No lesson content available in the database.") # Print a message
            return # Return if there is no lesson content
        # Build a nested dictionary of chapters and lessons
        content_dict = {} # Initialize the content dictionary
        for chapter, lesson in lessons: # Iterate over the lessons
            content_dict.setdefault(chapter, []).append(lesson) # Add the lesson to the chapter
        while True: # Loop to select a chapter and lesson
            print("\nSelect a Chapter (or 'B' to go back):") # Print the chapter selection prompt
            for chapter in sorted(content_dict.keys()): # Iterate over the chapters
                chapter_title = chapters.get(chapter, {}).get('title', f"Chapter {chapter}") # Get the chapter title
                print(f"{chapter}) {chapter_title}") # Print the chapter number and title
            chapter_choice = input("Enter chapter number: ").strip() # Get the user's chapter choice
            if chapter_choice.lower() == 'b': # Check if the user selected to go back
                return # Go back to the main menu
            if not chapter_choice.isdigit() or int(chapter_choice) not in content_dict: # Check if the user's chapter choice is invalid
                print(Fore.RED + "Invalid chapter number.") # Print an error message
                continue # Continue to the next iteration
            chapter = int(chapter_choice) # Convert the chapter choice to an integer
            lessons_in_chapter = content_dict[chapter] # Get the lessons in the selected chapter
            while True: # Loop to select a lesson
                print(f"\nSelect a Lesson in Chapter {chapter} (or 'B' to go back):") # Print the lesson selection prompt
                for lesson in sorted(lessons_in_chapter): # Iterate over the lessons in the chapter
                    lesson_title = chapters.get(chapter, {}).get('lessons', {}).get(lesson, {}).get('title', f"Lesson {lesson}") # Get the lesson title
                    print(f"{lesson}) {lesson_title}") # Print the lesson number and title
                lesson_choice = input("Enter lesson number: ").strip() # Get the user's lesson choice
                if lesson_choice.lower() == 'b': # Check if the user selected to go back
                    break # Go back to chapter selection
                if not lesson_choice.isdigit() or int(lesson_choice) not in lessons_in_chapter: # Check if the user's lesson choice is invalid
                    print(Fore.RED + "Invalid lesson number.") # Print an error message
                    continue # Continue to the next iteration
                lesson = int(lesson_choice) # Convert the lesson choice to an integer
                # Fetch and display the lesson content
                with sqlite3.connect('progress.db') as conn: # Connect to the database
                    cursor = conn.cursor() # Create a cursor object
                    cursor.execute( # Execute an SQL query
                        '''
                        SELECT content
                        FROM lesson_content
                        WHERE user_id = ? AND chapter = ? AND lesson = ?
                        ''',
                        (progress.user_id, chapter, lesson) # Pass the user ID, chapter, and lesson as parameters
                    )
                    row = cursor.fetchone() # Fetch the lesson content
                    if row: # Check if the lesson content is found
                        content = row[0] # Get the lesson content
                        chapter_title = chapters.get(chapter, {}).get('title', f"Chapter {chapter}") # Get the chapter title
                        lesson_title = chapters.get(chapter, {}).get('lessons', {}).get(lesson, {}).get('title', f"Lesson {lesson}") # Get the lesson title
                        print(Fore.CYAN + f"\n--- {chapter_title} ---") # Print the chapter title
                        print(Fore.CYAN + f"--- Lesson {lesson}: {lesson_title} ---") # Print the lesson title
                        print(Fore.YELLOW + "\nLesson Content:\n") # Print the lesson content header
                        print(content) # Print the lesson content
                    else: # Handle lesson content not found
                        print(Fore.RED + "Lesson content not found.") # Print an error message
                input("\nPress Enter to continue...") # Wait for user input
                break  # After displaying content, go back to lesson selection
    except sqlite3.Error as e: # Handle database errors
        print(Fore.RED + f"Database error: {e}") # Print an error message

#Display the user's mistakes
def show_mistakes_menu(progress): # Define the show_mistakes_menu function
    progress.show_mistakes() # Show the user's mistakes

#Function to enter testing mode
def testing_mode(progress): # Define the testing_mode function
    while True: # Loop to display the testing mode menu
        print("\n--- Testing Mode ---") # Print the testing mode options
        print("1) Generate Lesson Content") # Print the generate lesson content option
        print("2) Generate Questions from Lesson Content") # Print the generate questions option
        print("3) Generate Mistake Data for Lessons") # Print the generate mistake data option
        print("4) Generate Chapter Review") # Print the generate chapter review option
        print("5) Generate Cumulative Review") # Print the generate cumulative review option
        print("6) Generate All Lesson Content and Mistake Data") # Print the generate all lesson content and mistake data option
        print("7) Go Back to Main Menu") # Print the go back option

        choice = input("Select an option (1-7): ").strip() # Get the user's choice

        if choice == '1': # Check if the user selected generate lesson content
            generate_lesson_content_testing(progress) # Generate lesson content for selected chapter and lesson
        elif choice == '2': # Check if the user selected generate questions
            generate_questions_testing(progress) # Generate questions from lesson content by question type
        elif choice == '3': # Check if the user selected generate mistake data
            generate_mistake_data_testing(progress) # Generate mistake data for lessons
        elif choice == '4': # Check if the user selected generate chapter review
            generate_chapter_review_testing(progress) # Generate chapter review
        elif choice == '5': # Check if the user selected generate cumulative review
            cumulative_review_test(progress) # Generate cumulative review
        elif choice == '6': # Check if the user selected generate all lesson content and mistake data
            generate_all_lesson_content_and_mistakes(progress) # Generate all lesson content and mistake data
        elif choice == '7': # Check if the user selected go back
            return  # Go back to the main menu
        else: # Handle invalid choices
            print(Fore.RED + "Invalid choice. Please select 1-7.") # Print an error message

#Function to generate lesson content for testing mode
def generate_lesson_content_testing(progress): # Define the generate_lesson_content_testing function
    while True: # Loop to select a chapter and lesson
        print("\nSelect a Chapter (or 'B' to go back):") # Print the chapter selection prompt
        for chapter_num, chapter_info in chapters.items(): # Iterate over the chapters
            print(f"{chapter_num}) {chapter_info['title']}") # Print the chapter number and title

        chapter_choice = input("Enter chapter number: ").strip() # Get the user's chapter choice
        if chapter_choice.lower() == 'b': # Check if the user selected to go back
            return # Go back to the testing mode menu

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters: # Check if the user's chapter choice is invalid
            print(Fore.RED + "Invalid chapter number.") # Print an error message
            continue # Continue to the next iteration

        chapter = int(chapter_choice) # Convert the chapter choice to an integer

        print(f"\nSelect a Lesson in Chapter {chapter} (excluding lesson 8) (or 'B' to go back):") # Print the lesson selection prompt
        lessons = chapters[chapter]['lessons'] # Get the lessons in the selected chapter
        for lesson_num, lesson_info in lessons.items(): # Iterate over the lessons
            if lesson_num == 8: # Exclude lesson 8
                continue
            print(f"{lesson_num}) {lesson_info['title']}") # Print the lesson number and title

        lesson_choice = input("Enter lesson number: ").strip() # Get the user's lesson choice
        if lesson_choice.lower() == 'b': # Check if the user selected to go back
            continue # Continue to the next iteration

        if not lesson_choice.isdigit() or int(lesson_choice) not in lessons or int(lesson_choice) == 8: # Check if the user's lesson choice is invalid
            print(Fore.RED + "Invalid lesson number.") # Print an error message
            continue # Continue to the next iteration

        lesson = int(lesson_choice) # Convert the lesson choice to an integer

        # Generate lesson content
        print(Fore.GREEN + f"Generating lesson content for Chapter {chapter}, Lesson {lesson}...") # Print a success message
        lesson_content = generate_lesson_content(progress, chapter, lesson) # Generate lesson content
        print(Fore.GREEN + "Lesson content generated and saved to database.") # Print a success message

        # Ask if the user wants to generate another lesson content
        another = input("Generate content for another lesson? (Y/N): ").strip().lower() # Get the user's choice
        if another != 'y': # Check if the user selected not to generate another lesson content
            break

#Function to generate questions for testing mode
def generate_questions_testing(progress): # Define the generate_questions_testing function
    question_types = ['multiple_choice', 'true_false', 'fill_in_the_blank', 'scenario', 'write_code'] # Add the new question type
    while True: # Loop to select a question type, chapter, and lesson
        print("\nSelect a Question Type (or 'B' to go back):") # Print the question type selection prompt
        for idx, q_type in enumerate(question_types, 1): # Iterate over the question types
            print(f"{idx}) {q_type}") # Print the question type

        qtype_choice = input("Enter question type number: ").strip() # Get the user's question type choice
        if qtype_choice.lower() == 'b': # Check if the user selected to go back
            return # Go back to the testing mode menu

        if not qtype_choice.isdigit() or int(qtype_choice) < 1 or int(qtype_choice) > len(question_types): # Check if the user's question type choice is invalid
            print(Fore.RED + "Invalid choice.") # Print an error message
            continue # Continue to the next iteration

        question_type = question_types[int(qtype_choice) - 1] # Get the selected question type

        # Select chapter and lesson
        print("\nSelect a Chapter (or 'B' to go back):") # Print the chapter selection prompt
        for chapter_num, chapter_info in chapters.items(): # Iterate over the chapters
            print(f"{chapter_num}) {chapter_info['title']}") # Print the chapter number and title

        chapter_choice = input("Enter chapter number: ").strip() # Get the user's chapter choice
        if chapter_choice.lower() == 'b': # Check if the user selected to go back
            continue

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters: # Check if the user's chapter choice is invalid
            print(Fore.RED + "Invalid chapter number.") # Print an error message
            continue

        chapter = int(chapter_choice) # Convert the chapter choice to an integer

        print(f"\nSelect a Lesson in Chapter {chapter} (excluding lesson 8) (or 'B' to go back):") # Print the lesson selection prompt 
        lessons = chapters[chapter]['lessons'] # Get the lessons in the selected chapter
        for lesson_num, lesson_info in lessons.items(): # Iterate over the lessons
            if lesson_num == 8: # Exclude lesson 8
                continue
            print(f"{lesson_num}) {lesson_info['title']}") # Print the lesson number and title

        lesson_choice = input("Enter lesson number: ").strip() # Get the user's lesson choice
        if lesson_choice.lower() == 'b': # Check if the user selected to go back
            continue

        if not lesson_choice.isdigit() or int(lesson_choice) not in lessons or int(lesson_choice) == 8: # Check if the user's lesson choice is invalid
            print(Fore.RED + "Invalid lesson number.") # Print an error message
            continue

        lesson = int(lesson_choice) # Convert the lesson choice to an integer

        # Check if lesson content is available
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute an SQL query
                '''
                SELECT content
                FROM lesson_content
                WHERE user_id = ? AND chapter = ? AND lesson = ?
                ''',
                (progress.user_id, chapter, lesson) # Pass the user ID, chapter, and lesson as parameters
            )
            row = cursor.fetchone() # Fetch the lesson content
            if not row: # Check if the lesson content is not found
                print(Fore.RED + "Lesson content not found. Generate lesson content first.") # Print an error message
                continue # Continue to the next iteration
            lesson_content = row[0] # Get the lesson content

        # Generate question of the selected type
        print(Fore.GREEN + f"Generating {question_type} question for Chapter {chapter}, Lesson {lesson}...") # Print a success message
        # Modify the function to generate questions of a specific type
        questions = generate_questions_from_content( # Generate questions from lesson content
            chapter, lesson, lesson_content, question_count=1, allowed_types=[question_type] # Pass the chapter, lesson, lesson content, question count, and allowed types
        )
        if questions: # Check if questions are generated
            question_data = questions[0] # Get the first question
            print(Fore.GREEN + f"Question generated:\n{question_data['question']}") # Print the generated question
        else: # Handle failed question generation
            print(Fore.RED + "Failed to generate question.") # Print an error message

        another = input("Generate another question? (Y/N): ").strip().lower() # Get the user's choice
        if another != 'y': # Check if the user selected not to generate another question
            break

def generate_mistake_data_testing(progress): # Define the generate_mistake_data_testing function
    """Generate mistake data for lessons."""
    while True: # Loop to select a chapter and lesson
        print("\nSelect a Chapter (or 'B' to go back):") # Print the chapter selection prompt
        for chapter_num, chapter_info in chapters.items(): # Iterate over the chapters
            print(f"{chapter_num}) {chapter_info['title']}") # Print the chapter number and title

        chapter_choice = input("Enter chapter number: ").strip() # Get the user's chapter choice
        if chapter_choice.lower() == 'b': # Check if the user selected to go back
            return # Go back to the testing mode menu

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters: # Check if the user's chapter choice is invalid
            print(Fore.RED + "Invalid chapter number.") # Print an error message
            continue # Continue to the next iteration

        chapter = int(chapter_choice) # Convert the chapter choice to an integer

        print(f"\nSelect a Lesson in Chapter {chapter} (or 'B' to go back):") # Print the lesson selection prompt
        lessons = chapters[chapter]['lessons'] # Get the lessons in the selected chapter
        for lesson_num, lesson_info in lessons.items(): # Iterate over the lessons
            print(f"{lesson_num}) {lesson_info['title']}") # Print the lesson number and title

        lesson_choice = input("Enter lesson number: ").strip() # Get the user's lesson choice
        if lesson_choice.lower() == 'b': # Check if the user selected to go back
            continue

        if not lesson_choice.isdigit() or int(lesson_choice) not in lessons: # Check if the user's lesson choice is invalid
            print(Fore.RED + "Invalid lesson number.") # Print an error message
            continue

        lesson = int(lesson_choice) # Convert the lesson choice to an integer

        # Determine the original_lesson
        if lesson == 8: # Check if the lesson is a review lesson
            original_lesson = random.randint(1, 7) # Generate a random lesson number
        else: # Handle non-review lessons
            original_lesson = lesson # Set the original lesson to the selected lesson

        # Create a sample mistake entry
        question_text = f"Sample question for Chapter {chapter}, Lesson {lesson}" # Generate a sample question text
        user_answer = "Incorrect answer" # Generate a sample user answer
        correct_answer = "Correct answer" # Generate a sample correct answer

        # Save the mistake to the database
        try: # Try to save the mistake to the database
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    INSERT INTO mistakes (user_id, chapter, lesson, question, user_answer, correct_answer, original_lesson)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (progress.user_id, chapter, lesson, question_text, user_answer, correct_answer, original_lesson) # Pass the mistake data as parameters
                )
                conn.commit() # Commit the transaction
                print(Fore.GREEN + "Mistake data generated and saved.") # Print a success message
        except sqlite3.Error as e: # Handle database errors
            print(Fore.RED + f"Failed to save mistake: {e}") # Print an error message

        another = input("Generate mistake for another lesson? (Y/N): ").strip().lower() # Get the user's choice
        if another != 'y': # Check if the user selected not to generate another mistake
            break

#Function to generate chapter review for testing mode
def generate_chapter_review_testing(progress): # Define the generate_chapter_review_testing function
    while True: # Loop to select a chapter
        print("\nSelect a Chapter to generate review (or 'B' to go back):") # Print the chapter selection prompt
        for chapter_num, chapter_info in chapters.items(): # Iterate over the chapters
            print(f"{chapter_num}) {chapter_info['title']}") # Print the chapter number and title
 
        chapter_choice = input("Enter chapter number: ").strip() # Get the user's chapter choice
        if chapter_choice.lower() == 'b': # Check if the user selected to go back
            return 

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters: # Check if the user's chapter choice is invalid
            print(Fore.RED + "Invalid chapter number.") # Print an error message
            continue

        chapter = int(chapter_choice) # Convert the chapter choice to an integer

        # Check if lesson content for all lessons is available
        lessons = chapters[chapter]['lessons'] # Get the lessons in the selected chapter
        missing_content = False # Initialize the missing content flag
        for lesson_num in lessons: # Iterate over the lessons
            if lesson_num == 8: # Skip review lesson
                continue
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    SELECT content
                    FROM lesson_content
                    WHERE user_id = ? AND chapter = ? AND lesson = ?
                    ''',
                    (progress.user_id, chapter, lesson_num) # Pass the user ID, chapter, and lesson as parameters
                )
                row = cursor.fetchone() # Fetch the lesson content
                if not row: # Check if the lesson content is not found
                    print(Fore.RED + f"Lesson content missing for Chapter {chapter}, Lesson {lesson_num}. Cannot generate review.") # Print an error message
                    missing_content = True # Set the missing content flag
                    break
        if missing_content: # Check if lesson content is missing
            continue # Continue to the next iteration

        # Generate the chapter review
        print(Fore.GREEN + f"Generating chapter review for Chapter {chapter}...") # Print a success message
        questions = generate_review_questions(progress, chapter) # Generate review questions for the chapter
        print(Fore.GREEN + f"Chapter review generated with {len(questions)} questions.") # Print the number of questions generated
 
        another = input("Generate review for another chapter? (Y/N): ").strip().lower() # Get the user's choice
        if another != 'y': # Check if the user selected not to generate another review
            break

#Function to generate cumulative review for testing mode
def cumulative_review_test(progress): # Define the cumulative_review_test function
    questions = generate_cumulative_review(progress) # Generate cumulative review questions
    correct_answers = 0 # Initialize the number of correct answers

    print(Fore.MAGENTA + "\n--- Final Cumulative Review: All Chapters ---") # Print the cumulative review title
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score

    # For each question in the cumulative review, run the ask_question_and_validate function and track the correct answers
    for i, question_data in enumerate(questions): # Iterate over the questions
        print(f"\nQuestion {i + 1}/{len(questions)}:") # Print the question number
        chapter = question_data.get('chapter', 1) # Get the chapter number
        lesson = question_data.get('lesson', None) # Get the lesson number
        correct = ask_question_and_validate(question_data, progress, chapter, lesson) # Ask the question and validate the answer
        if correct: # Handle correct answers
            correct_answers += 1 # Increment the correct answers count
        else: # Handle incorrect answers
            # Record the mistake using add_mistake
            progress.add_mistake( # Add the mistake to the progress object
                chapter=chapter, # Pass the chapter number
                lesson=lesson, # Pass the lesson number
                question=question_data.get('question', ''), # Pass the question text
                user_answer='Incorrect',  # Replace with actual user input if available
                correct_answer=question_data.get('correct_answer', ''), # Pass the correct
                feedback='',  # Provide feedback if available
                original_lesson=question_data.get('original_lesson', None) # Pass the original lesson number
            )

    if correct_answers >= int(len(questions) * 0.7): # Check if the user passed the cumulative review
        print(Fore.GREEN + "Congratulations! You passed the cumulative review!\n") # Print a success message
        return True # Return True for passing the cumulative review
    else: # Handle failing the cumulative review
        print(Fore.RED + "You did not pass the cumulative review. Please try again.\n") # Print an error message
        return False # Return False for failing the cumulative review

#Function to generate all lesson content and mistake data for testing mode
def generate_all_lesson_content_and_mistakes(progress): # Define the generate_all_lesson_content_and_mistakes function
    print(Fore.GREEN + "Generating lesson content and mistake data for all chapters and lessons...") # Print a success message

    total_lessons = 0 # Initialize the total number of lessons
    lessons_with_errors = [] # Initialize the list of lessons with errors

    # Iterate over the chapters and lessons to generate content and mistakes
    for chapter_num, chapter_info in chapters.items(): # Iterate over the chapters
        lessons = chapter_info['lessons'] # Get the lessons in the chapter
        for lesson_num in lessons: # Iterate over the lessons
            # Skip if it's a cumulative review chapter (like chapter 21 in your config)
            if chapter_num == 21: # Check if it's a cumulative review chapter
                continue
            # Generate lesson content for lessons 1-7
            if lesson_num != 8:  # Exclude review lessons for content generation
                try: # Try to generate lesson content
                    lesson_title = chapters[chapter_num]['lessons'][lesson_num]['title'] # Get the lesson title
                    print(Fore.GREEN + f"Generating content for Chapter {chapter_num}, Lesson {lesson_num}: {lesson_title}") # Print a success message
                    total_lessons += 1 # Increment the total number of lessons 
                except Exception as e: # Handle errors during content generation
                    print(Fore.RED + f"Failed to generate content for Chapter {chapter_num}, Lesson {lesson_num}: {e}") # Print an error message
                    lessons_with_errors.append((chapter_num, lesson_num)) # Add the lesson to the list of lessons with errors
            else: # Handle review lessons
                print(Fore.YELLOW + f"Skipping content generation for Chapter {chapter_num}, Lesson {lesson_num} (Review Lesson)") # Print a message for review lessons

            # Generate mistake data for all lessons, including review lessons
            try: # Try to generate mistake data
                # Determine the original_lesson
                if lesson_num == 8: # For review lessons, pick a random lesson between 1 and 7
                    original_lesson = random.randint(1, 7) # Generate a random lesson number
                else: # For non-review lessons, use the lesson number
                    original_lesson = lesson_num # Set the original lesson to the lesson number

                # Create a sample mistake entry
                question_text = f"Sample question for Chapter {chapter_num}, Lesson {lesson_num}" # Generate a sample question text
                user_answer = "Incorrect answer" # Generate a sample user answer
                correct_answer = "Correct answer" # Generate a sample correct answer

                # Save the mistake to the database
                with sqlite3.connect('progress.db') as conn: # Connect to the database
                    cursor = conn.cursor() # Create a cursor object
                    cursor.execute( # Execute an SQL query
                        '''
                        INSERT INTO mistakes (user_id, chapter, lesson, question, user_answer, correct_answer, original_lesson)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (progress.user_id, chapter_num, lesson_num, question_text, user_answer, correct_answer, original_lesson) # Pass the mistake data as parameters
                    )
                    conn.commit() # Commit the transaction
            except sqlite3.Error as e: # Handle database errors
                print(Fore.RED + f"Failed to save mistake for Chapter {chapter_num}, Lesson {lesson_num}: {e}") # Print an error message
            except Exception as e:  # Handle other errors
                print(Fore.RED + f"Unexpected error for Chapter {chapter_num}, Lesson {lesson_num}: {e}") # Print an error message

    print(Fore.GREEN + f"\nGenerated lesson content for {total_lessons} lessons.") # Print the total number of lessons with content generated
    if lessons_with_errors: # Check if there are lessons with errors
        print(Fore.RED + "Some lessons encountered errors during content generation:") # Print a message for lessons with errors
        for chapter_num, lesson_num in lessons_with_errors: # Iterate over the lessons with errors
            print(f"- Chapter {chapter_num}, Lesson {lesson_num}") # Print the chapter and lesson numbers
    else: # Handle all lessons generated successfully
        print(Fore.GREEN + "All lesson content generated successfully.") # Print a success message

    print(Fore.GREEN + "Mistake data generated for all lessons.") # Print a success message

# Main entry point
if __name__ == "__main__": # Check if the script is being run directly
    welcome()  # Start with the welcome screen
