from colorama import Fore, init # Import the Fore and init functions from colorama
import sqlite3 # Import the sqlite3 module
import bcrypt # Import the bcrypt module
from config import chapters # Import the chapters dictionary from config.py

from questions import validate_answer_with_gpt, generate_lesson_content, generate_questions_from_content, generate_review_questions, generate_cumulative_review # Import functions from questions.py
#validate_answer_with_gpt: Validate the user's answer using GPT-3, generate_python_question: Generate a Python question,
#generate_lesson_content: Generate lesson content, generate_questions_from_content: Generate questions from lesson content,
#generate_review_questions: Generate review questions, generate_cumulative_review: Generate cumulative review questions

import logging # Import the logging module
from fuzzywuzzy import fuzz # Import the fuzz function from fuzzywuzzy
import subprocess # Import the subprocess module
import sys # Import the sys module
import random # Import the random module
#logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Helper function to run the user's code **this was created by chatgpt but hasnt been fully implemented yet**
def run_user_code(code): # Define the run_user_code function
    """Execute the user's code safely and capture the output."""
    try: # Try to run the user's code
        # Use subprocess to run the code and capture both stdout and stderr
        result = subprocess.run( # Run the code with subprocess
            [sys.executable, "-c", code],  # Run code with the current Python interpreter
            capture_output=True, text=True, timeout=5 # Capture output as text and set a timeout
        ) # Run the code
        return result.stdout.strip(), result.stderr.strip() # Return the output and errors
    except subprocess.TimeoutExpired: # Handle timeouts
        return "", "Execution timed out." # Return an error message for timeouts

# Initialize colorama to reset color after each print
init(autoreset=True) # Initialize colorama

# Registers new users
def register_user(): # Define the register_user function
    """Register a new user."""
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
    """Log in an existing user."""
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
    return None

# Track user progress and score
class UserProgress: # Define the UserProgress class
    """Track user progress and score."""
    
    # Initialize the UserProgress class
    def __init__(self, user_id): # Define the __init__ function
        self.user_id = user_id # Set the user ID
        self.chapter = 1  # Start at Chapter 1
        self.lesson = 1  # Start at Lesson 1
        
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
    
    # Add a mistake to the lesson
    def add_mistake(self, chapter, lesson, question, user_answer, correct_answer, feedback=None, user_code=None, user_output=None, user_errors=None, original_lesson=None):
        """Track mistakes with detailed information, including feedback and code details."""
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO mistakes (user_id, chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (self.user_id, chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson)
                )
                conn.commit()
                logging.info(f"Mistake recorded for user {self.user_id} in Chapter {chapter} Lesson {lesson}.")
        except sqlite3.Error as e:
            logging.error(f"Failed to add mistake: {e}")



    
    # show the user's mistakes
    def show_mistakes(self):
        """Display the user's mistakes."""
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson
                    FROM mistakes
                    WHERE user_id = ?
                    ORDER BY chapter, lesson
                    ''',
                    (self.user_id,)
                )
                mistakes = cursor.fetchall()

            if not mistakes:
                print(Fore.YELLOW + "No mistakes recorded yet.")
                return

            print(Fore.RED + "Mistakes:")
            current_lesson_key = None
            for mistake in mistakes:
                chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson = mistake
                lesson_key = f'Chapter {chapter} Lesson {lesson}'
                if lesson_key != current_lesson_key:
                    print(f"\n{lesson_key}:")
                    current_lesson_key = lesson_key
                print(f"Question: {question}")
                print(f"Your Answer: {user_answer}")
                print(f"Correct Answer: {correct_answer}")
                if feedback:
                    print(f"Feedback: {feedback}")
                if user_code:
                    print(f"Your Code:\n{user_code}")
                if user_output:
                    print(f"Your Code Output:\n{user_output}")
                if user_errors:
                    print(f"Your Code Errors:\n{user_errors}")
                if original_lesson:
                    print(f"Original Lesson: {original_lesson}")  # Display original_lesson if present
                print()  # Blank line for readability
        except sqlite3.Error as e:
            logging.error(f"Failed to retrieve mistakes: {e}")




    # save the user's progress       
    def save_progress(self):
        """Save the user's progress to the database."""
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET chapter = ?, lesson = ? WHERE id = ?',
                    (self.chapter, self.lesson, self.user_id)
                )
                conn.commit()
                logging.info(f"Progress saved: Chapter {self.chapter}, Lesson {self.lesson}")
        except sqlite3.Error as e:
            logging.error(f"Failed to save progress: {e}")

    # calculate the chapter score
    def calculate_chapter_score(progress):
        """Calculate the cumulative chapter score from the database."""
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT SUM(correct), SUM(total)
                    FROM lesson_scores
                    WHERE user_id = ? AND chapter = ?
                    ''',
                    (progress.user_id, progress.chapter)
                )
                row = cursor.fetchone()
                if row and row[1] > 0:
                    total_correct, total_questions = row
                    return calculate_percentage_score(total_correct, total_questions)
                else:
                    return 0
        except sqlite3.Error as e:
            logging.error(f"Failed to calculate chapter score: {e}")
            return 0
  
# Helper function to calculate the percentage score
def calculate_percentage_score(correct, total): # Define the calculate_percentage_score function
    """Calculate the percentage score.""" 
    return (correct / total) * 100 if total > 0 else 0 # Calculate the percentage score

#Function to select a lesson within a chapter
def select_lesson(progress, chapter):
    """Allow the user to select a lesson within a chapter."""
    while True:
        print(f"\nSelect a Lesson for Chapter {chapter}:")
        
        # Exclude the review test when counting total lessons
        total_lessons_in_chapter = len(chapters[chapter]['lessons']) - 1  # Subtract 1 for the review test

        # Determine which lessons are unlocked
        if chapter == progress.chapter:
            if progress.lesson > total_lessons_in_chapter:
                # User has completed all lessons, include the chapter review test
                unlocked_lessons = range(1, total_lessons_in_chapter + 2)
            else:
                unlocked_lessons = range(1, progress.lesson + 1)
        else:
            unlocked_lessons = [1]

        # Display unlocked lessons
        for lesson in unlocked_lessons:
            if lesson <= total_lessons_in_chapter:
                print(f"{lesson}) {chapters[chapter]['lessons'][lesson]['title']}")
            else:
                print(f"{lesson}) Review Test: {chapters[chapter]['title']}")

        lesson_choice = input("Enter the lesson number (or 'B' to go back): ").strip()

        if lesson_choice.lower() == 'b':
            return  # Go back to chapter selection

        if not lesson_choice.isdigit() or int(lesson_choice) not in unlocked_lessons:
            print(Fore.RED + "Invalid lesson number.")
            continue

        lesson = int(lesson_choice)

        if lesson <= total_lessons_in_chapter:
            # Proceed with the lesson
            print(Fore.GREEN + "Retrieving lesson content...")
            lesson_content = generate_lesson_content(progress, chapter, lesson)
            play_lesson(progress, chapter, lesson, lesson_content)
        else:
            # User selected the Review Test
            if progress.lesson > total_lessons_in_chapter:
                # Call your review test function
                passed = review_test(progress)
                if passed:
                    # Update progress to unlock the next chapter
                    progress.chapter += 1
                    progress.lesson = 1
                    progress.save_progress()
                    print(Fore.GREEN + "You have advanced to the next chapter!")
                    return  # Go back to chapter selection
                else:
                    print(Fore.RED + "Please review the lessons and try again.")
            else:
                print(Fore.RED + "You need to complete all lessons before taking the review test.")

# Function to generate the lesson content, questions and track user progress
def play_lesson(progress, chapter, lesson, lesson_content):
    """Play a single lesson with the provided content."""
    
    try:
        with sqlite3.connect('progress.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                DELETE FROM mistakes WHERE user_id = ? AND chapter = ? AND lesson = ?
                ''',
                (progress.user_id, chapter, lesson)
            )
            conn.commit()
            logging.info(f"Cleared previous mistakes for Chapter {chapter} Lesson {lesson}")
    except sqlite3.Error as e:
        logging.error(f"Failed to clear previous mistakes: {e}")

    print(Fore.CYAN + f"\n--- {chapters[chapter]['title']} ---")
    print(Fore.CYAN + f"--- Lesson {lesson}: {chapters[chapter]['lessons'][lesson]['title']} ---")

    print(Fore.YELLOW + "\nLesson Content:\n")
    print(lesson_content)

    # Generate questions based on the lesson content
    question_count = chapters[chapter]['lessons'][lesson].get('question_count')
    if not question_count:
        print(Fore.RED + "Error: No question count specified for this lesson.")
        return

    questions = generate_questions_from_content(chapter, lesson, lesson_content, question_count)

    correct_answers = 0

    # For each question in the lesson, run the ask_question_and_validate function and track the correct answers
    for i, question_data in enumerate(questions):
        print(f"\nQuestion {i + 1}/{question_count}:")
        correct = ask_question_and_validate(question_data, progress, chapter, lesson)

        if correct:
            correct_answers += 1

    print(f"\nLesson {lesson} complete! You answered {correct_answers} out of {question_count} correctly.")

    try:
        with sqlite3.connect('progress.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT OR REPLACE INTO lesson_scores (user_id, chapter, lesson, correct, total)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (progress.user_id, chapter, lesson, correct_answers, question_count)
            )
            conn.commit()
            logging.info(f"Lesson score saved for Chapter {chapter} Lesson {lesson}")
    except sqlite3.Error as e:
        logging.error(f"Failed to save lesson score: {e}")

    # Unlock the next lesson if applicable
    total_lessons_in_chapter = len(chapters[chapter]['lessons']) - 1  # Exclude the review test
    if lesson < total_lessons_in_chapter:
        progress.lesson += 1
    else:
        # Set progress.lesson to the review test
        progress.lesson = total_lessons_in_chapter + 1
        print(Fore.GREEN + "You have completed all lessons in this chapter!")

    progress.save_progress()

# Function to ask questions and validate answers **ChatGPT was used to assist with the creation of this function**
def ask_question_and_validate(question_data, progress=None, chapter=None, lesson=None): # Define the ask_question_and_validate function
    """Display the question, get user input, and validate the answer."""

    # Validate the question data
    if not question_data or 'question' not in question_data: # Check if the question data is missing or invalid
        logging.error(f"Invalid question data: {question_data}") # Log an error message
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
            logging.warning(f"Invalid input received: {user_answer}") # Log a warning message
            print(Fore.RED + "Invalid input. Please enter a valid option letter (A, B, C, D).") # Print an error message
            return False # Return False for an invalid answer

        # Check if the answer is correct
        correct = user_answer == question_data['correct_answer'] # Check if the user's answer is correct
        if correct:
            print(Fore.GREEN + "Correct!")
        else:
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}") 
            if progress and chapter is not None and lesson is not None:
                progress.add_mistake(
                    chapter=chapter,
                    lesson=lesson,
                    question=question_data['question'],
                    user_answer=user_answer,
                    correct_answer=question_data['correct_answer'],
                    original_lesson=original_lesson
                )
        return correct  # Return the correctness of the answer

    # Display true or false questions   
    elif question_data['type'] == "true_false": # Check if the question type is true or false
        user_answer = input("True or False? ").strip().lower() # Get the user's answer
        logging.debug(f"User Answer: {user_answer} | Expected Answer: {question_data['correct_answer']}")
        correct = user_answer == question_data['correct_answer'].lower() # Check if the user's answer is correct
        if correct:
            print(Fore.GREEN + "Correct!")
        else:
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}") 
            if progress and chapter is not None and lesson is not None:
                progress.add_mistake(
                    chapter=chapter,
                    lesson=lesson,
                    question=question_data['question'],
                    user_answer=user_answer,
                    correct_answer=question_data['correct_answer'],
                    original_lesson=original_lesson
                )
        return correct # Return the correctness of the answer

    # Display fill in the blank questions
    elif question_data['type'] == "fill_in_the_blank": # Check if the question type is fill in the blank
        user_answer = input("Fill in the blank: ").strip().lower() # Get the user's answer
        logging.debug(f"User Answer: {user_answer} | Expected Answer: {question_data['correct_answer']}")
        correct = user_answer == question_data.get('correct_answer', '').lower() # Check if the user's answer is correct
        if correct:
            print(Fore.GREEN + "Correct!")
        else:
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}") 
            if progress and chapter is not None and lesson is not None:
                progress.add_mistake(
                    chapter=chapter,
                    lesson=lesson,
                    question=question_data['question'],
                    user_answer=user_answer,
                    correct_answer=question_data['correct_answer'],
                    original_lesson=original_lesson
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

        logging.debug(f"User's Code:\n{user_code}") # Log the user's code

        # Run the user's code and capture output or errors
        user_output, user_errors = run_user_code(user_code) # Run the user's code

        if user_errors: # Handle errors
            print(f"\nYour code produced the following error:\n{user_errors}") # Print the error message
            logging.error(f"User's Code Error: {user_errors}") # Log the error message
        else: # Handle output
            print(f"\nYour code produced the following output:\n{user_output}") # Print the output
            logging.info(f"User's Code Output: {user_output}") # Log the output

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
            if progress and chapter is not None and lesson is not None and not correct:
                progress.add_mistake(
                    chapter=chapter,
                    lesson=lesson,
                    question=question_data['question'],
                    user_answer=user_code,
                    correct_answer=question_data['correct_answer'],
                    feedback=feedback,
                    user_code=user_code,
                    user_output=user_output if not user_errors else None,
                    user_errors=user_errors if user_errors else None,
                    original_lesson=original_lesson
                )
        return correct # Return the correctness of the answer

    # Display scenario questions
    elif question_data['type'] == "scenario": # Check if the question type is a scenario
        user_response = input("Describe your response to the scenario: ").strip() # Get the user's response

        # Validate the user's response using GPT
        correct, feedback = validate_answer_with_gpt(
            question_data=question_data,  # Pass the full dictionary
            user_response=user_response
        )

        # Display the result based on GPT validation
        if correct: # Handle correct answers
            print(Fore.GREEN + "Correct! Well done.") # Print a success message
        else: # Handle incorrect answers
            print(Fore.RED + "Incorrect. Review the feedback below:") # Print an error message
            print(Fore.YELLOW + feedback) # Print the feedback
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}") 
        if progress and chapter is not None and lesson is not None and not correct:
            progress.add_mistake(
                chapter=chapter,
                lesson=lesson,
                question=question_data['question'],
                user_answer=user_response,
                correct_answer=question_data['correct_answer'],
                feedback=feedback,
                original_lesson=original_lesson
            )
        return correct # Return the correctness of the answer

# Function to generate review questions
def review_test(progress):
    """Conduct the chapter review and return whether the user passed."""
    chapter = progress.chapter
    try:
        with sqlite3.connect('progress.db') as conn:
            cursor = conn.cursor()
            # Assuming lesson number for review test is always set to 8
            cursor.execute(
                '''
                DELETE FROM mistakes WHERE user_id = ? AND chapter = ? AND lesson = ?
                ''',
                (progress.user_id, chapter, 8)
            )
            conn.commit()
            logging.info(f"Cleared previous mistakes for Chapter {chapter} Review Test")
    except sqlite3.Error as e:
        logging.error(f"Failed to clear previous mistakes: {e}")

    questions = generate_review_questions(progress, chapter)
    correct_answers = 0

    print(Fore.MAGENTA + f"\n--- Review Test: {chapters[chapter]['title']} ---")
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n")

    for i, question_data in enumerate(questions):
        print(f"\nQuestion {i + 1}/{len(questions)}:")
        correct = ask_question_and_validate(question_data, progress, chapter, lesson=8)
        if correct:
            correct_answers += 1

    if correct_answers >= int(len(questions) * 0.7):
        print(Fore.GREEN + "Congratulations! You passed the review.\n")
        return True
    else:
        print(Fore.RED + "You did not pass the review. Try again!\n")
        return False

#Function to generate cumulative review questions **currently note working as intended**
def cumulative_review_test(progress): # Define the cumulative_review_test function
    """Conduct the cumulative review covering all chapters and return pass status.""" 
    questions = generate_cumulative_review(progress) # Generate cumulative review questions
    correct_answers = 0 # Initialize the number of correct answers
 
    print(Fore.MAGENTA + "\n--- Final Cumulative Review: All Chapters ---") # Print the cumulative review title
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score

    for i, question_data in enumerate(questions):
        print(f"\nQuestion {i + 1}/{len(questions)}:")
        chapter = question_data.get('chapter', 1)
        lesson = question_data.get('lesson', None)
        if ask_question_and_validate(question_data, progress, chapter, lesson):
            correct_answers += 1 # Increment the correct answers count
        else: # Handle incorrect answers
            chapter = question_data.get('chapter', 1)  # Track which chapter the mistake came from
            progress.add_review_mistake(chapter) # Track the review mistakes

    if correct_answers >= int(len(questions) * 0.7): # Check if the user passed the cumulative review
        print(Fore.GREEN + "Congratulations! You passed the cumulative review!\n") # Print a success message
        return True # Return True for passing the cumulative review
    else: # Handle failing the cumulative review
        print(Fore.RED + "You did not pass the cumulative review. Please try again.\n") # Print an error message
        return False # Return False for failing the cumulative review

# Main game loop    
def play_game(progress): # Define the play_game function
    """Allow the user to select and play chapters and lessons."""
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
def main_menu(progress):
    """Display the main menu and handle user choices."""
    while True:
        print("\n--- Main Menu ---")
        print("1) Play")
        print("2) Show Mistakes")
        print("3) Display Lesson Content")  # New option added
        print("4) Exit")
        print("5) Testing Mode")  # If you have testing mode as option 5

        choice = input("Select an option (1-5): ").strip()

        if choice == '1':
            play_game(progress)
        elif choice == '2':
            show_mistakes_menu(progress)
        elif choice == '3':
            display_lesson_content_menu(progress)  # Call the new function
        elif choice == '4':
            print(Fore.GREEN + "Goodbye!")
            break
        elif choice == '5':
            testing_mode(progress)
        else:
            print(Fore.RED + "Invalid choice. Please select 1-5.")
def display_lesson_content_menu(progress):
    """Display the lesson content stored in the database."""
    try:
        with sqlite3.connect('progress.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT DISTINCT chapter, lesson
                FROM lesson_content
                WHERE user_id = ?
                ORDER BY chapter, lesson
                ''',
                (progress.user_id,)
            )
            lessons = cursor.fetchall()
        if not lessons:
            print(Fore.YELLOW + "No lesson content available in the database.")
            return
        # Build a nested dictionary of chapters and lessons
        content_dict = {}
        for chapter, lesson in lessons:
            content_dict.setdefault(chapter, []).append(lesson)
        while True:
            print("\nSelect a Chapter (or 'B' to go back):")
            for chapter in sorted(content_dict.keys()):
                chapter_title = chapters.get(chapter, {}).get('title', f"Chapter {chapter}")
                print(f"{chapter}) {chapter_title}")
            chapter_choice = input("Enter chapter number: ").strip()
            if chapter_choice.lower() == 'b':
                return
            if not chapter_choice.isdigit() or int(chapter_choice) not in content_dict:
                print(Fore.RED + "Invalid chapter number.")
                continue
            chapter = int(chapter_choice)
            lessons_in_chapter = content_dict[chapter]
            while True:
                print(f"\nSelect a Lesson in Chapter {chapter} (or 'B' to go back):")
                for lesson in sorted(lessons_in_chapter):
                    lesson_title = chapters.get(chapter, {}).get('lessons', {}).get(lesson, {}).get('title', f"Lesson {lesson}")
                    print(f"{lesson}) {lesson_title}")
                lesson_choice = input("Enter lesson number: ").strip()
                if lesson_choice.lower() == 'b':
                    break
                if not lesson_choice.isdigit() or int(lesson_choice) not in lessons_in_chapter:
                    print(Fore.RED + "Invalid lesson number.")
                    continue
                lesson = int(lesson_choice)
                # Fetch and display the lesson content
                with sqlite3.connect('progress.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        '''
                        SELECT content
                        FROM lesson_content
                        WHERE user_id = ? AND chapter = ? AND lesson = ?
                        ''',
                        (progress.user_id, chapter, lesson)
                    )
                    row = cursor.fetchone()
                    if row:
                        content = row[0]
                        chapter_title = chapters.get(chapter, {}).get('title', f"Chapter {chapter}")
                        lesson_title = chapters.get(chapter, {}).get('lessons', {}).get(lesson, {}).get('title', f"Lesson {lesson}")
                        print(Fore.CYAN + f"\n--- {chapter_title} ---")
                        print(Fore.CYAN + f"--- Lesson {lesson}: {lesson_title} ---")
                        print(Fore.YELLOW + "\nLesson Content:\n")
                        print(content)
                    else:
                        print(Fore.RED + "Lesson content not found.")
                input("\nPress Enter to continue...")
                break  # After displaying content, go back to lesson selection
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        print(Fore.RED + f"Database error: {e}")

#Helper function to display the user's mistakes
def show_mistakes_menu(progress): # Define the show_mistakes_menu function
    """Display the recorded mistakes."""    
    progress.show_mistakes() # Show the user's mistakes

def testing_mode(progress):
    """Testing mode to generate lesson content, questions, mistakes, etc."""
    while True:
        print("\n--- Testing Mode ---")
        print("1) Generate Lesson Content")
        print("2) Generate Questions from Lesson Content")
        print("3) Generate Mistake Data for Lessons")
        print("4) Generate Chapter Review")
        print("5) Generate Cumulative Review")
        print("6) Generate All Lesson Content and Mistake Data")  # New option added
        print("7) Go Back to Main Menu")

        choice = input("Select an option (1-7): ").strip()

        if choice == '1':
            generate_lesson_content_testing(progress)
        elif choice == '2':
            generate_questions_testing(progress)
        elif choice == '3':
            generate_mistake_data_testing(progress)
        elif choice == '4':
            generate_chapter_review_testing(progress)
        elif choice == '5':
            cumulative_review_test(progress)
        elif choice == '6':
            generate_all_lesson_content_and_mistakes(progress)  # New function
        elif choice == '7':
            return  # Go back to the main menu
        else:
            print(Fore.RED + "Invalid choice. Please select 1-7.")

def generate_lesson_content_testing(progress):
    """Generate lesson content for selected chapter and lesson and save to database."""
    while True:
        print("\nSelect a Chapter (or 'B' to go back):")
        for chapter_num, chapter_info in chapters.items():
            print(f"{chapter_num}) {chapter_info['title']}")

        chapter_choice = input("Enter chapter number: ").strip()
        if chapter_choice.lower() == 'b':
            return

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters:
            print(Fore.RED + "Invalid chapter number.")
            continue

        chapter = int(chapter_choice)

        print(f"\nSelect a Lesson in Chapter {chapter} (excluding lesson 8) (or 'B' to go back):")
        lessons = chapters[chapter]['lessons']
        for lesson_num, lesson_info in lessons.items():
            if lesson_num == 8:
                continue  # Exclude lesson 8
            print(f"{lesson_num}) {lesson_info['title']}")

        lesson_choice = input("Enter lesson number: ").strip()
        if lesson_choice.lower() == 'b':
            continue

        if not lesson_choice.isdigit() or int(lesson_choice) not in lessons or int(lesson_choice) == 8:
            print(Fore.RED + "Invalid lesson number.")
            continue

        lesson = int(lesson_choice)

        # Generate lesson content
        print(Fore.GREEN + f"Generating lesson content for Chapter {chapter}, Lesson {lesson}...")
        lesson_content = generate_lesson_content(progress, chapter, lesson)
        print(Fore.GREEN + "Lesson content generated and saved to database.")

        # Ask if the user wants to generate another lesson content
        another = input("Generate content for another lesson? (Y/N): ").strip().lower()
        if another != 'y':
            break

def generate_questions_testing(progress):
    """Generate questions from lesson content by question type."""
    question_types = ['multiple_choice', 'true_false', 'fill_in_the_blank', 'scenario', 'write_code']
    while True:
        print("\nSelect a Question Type (or 'B' to go back):")
        for idx, q_type in enumerate(question_types, 1):
            print(f"{idx}) {q_type}")

        qtype_choice = input("Enter question type number: ").strip()
        if qtype_choice.lower() == 'b':
            return

        if not qtype_choice.isdigit() or int(qtype_choice) < 1 or int(qtype_choice) > len(question_types):
            print(Fore.RED + "Invalid choice.")
            continue

        question_type = question_types[int(qtype_choice) - 1]

        # Select chapter and lesson
        print("\nSelect a Chapter (or 'B' to go back):")
        for chapter_num, chapter_info in chapters.items():
            print(f"{chapter_num}) {chapter_info['title']}")

        chapter_choice = input("Enter chapter number: ").strip()
        if chapter_choice.lower() == 'b':
            continue

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters:
            print(Fore.RED + "Invalid chapter number.")
            continue

        chapter = int(chapter_choice)

        print(f"\nSelect a Lesson in Chapter {chapter} (excluding lesson 8) (or 'B' to go back):")
        lessons = chapters[chapter]['lessons']
        for lesson_num, lesson_info in lessons.items():
            if lesson_num == 8:
                continue  # Exclude lesson 8
            print(f"{lesson_num}) {lesson_info['title']}")

        lesson_choice = input("Enter lesson number: ").strip()
        if lesson_choice.lower() == 'b':
            continue

        if not lesson_choice.isdigit() or int(lesson_choice) not in lessons or int(lesson_choice) == 8:
            print(Fore.RED + "Invalid lesson number.")
            continue

        lesson = int(lesson_choice)

        # Check if lesson content is available
        with sqlite3.connect('progress.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT content
                FROM lesson_content
                WHERE user_id = ? AND chapter = ? AND lesson = ?
                ''',
                (progress.user_id, chapter, lesson)
            )
            row = cursor.fetchone()
            if not row:
                print(Fore.RED + "Lesson content not found. Generate lesson content first.")
                continue
            lesson_content = row[0]

        # Generate question of the selected type
        print(Fore.GREEN + f"Generating {question_type} question for Chapter {chapter}, Lesson {lesson}...")
        # Modify the function to generate questions of a specific type
        questions = generate_questions_from_content(
            chapter, lesson, lesson_content, question_count=1, allowed_types=[question_type]
        )
        if questions:
            question_data = questions[0]
            print(Fore.GREEN + f"Question generated:\n{question_data['question']}")
        else:
            print(Fore.RED + "Failed to generate question.")

        another = input("Generate another question? (Y/N): ").strip().lower()
        if another != 'y':
            break

def generate_mistake_data_testing(progress):
    """Generate mistake data for lessons."""
    while True:
        print("\nSelect a Chapter (or 'B' to go back):")
        for chapter_num, chapter_info in chapters.items():
            print(f"{chapter_num}) {chapter_info['title']}")

        chapter_choice = input("Enter chapter number: ").strip()
        if chapter_choice.lower() == 'b':
            return

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters:
            print(Fore.RED + "Invalid chapter number.")
            continue

        chapter = int(chapter_choice)

        print(f"\nSelect a Lesson in Chapter {chapter} (or 'B' to go back):")
        lessons = chapters[chapter]['lessons']
        for lesson_num, lesson_info in lessons.items():
            print(f"{lesson_num}) {lesson_info['title']}")

        lesson_choice = input("Enter lesson number: ").strip()
        if lesson_choice.lower() == 'b':
            continue

        if not lesson_choice.isdigit() or int(lesson_choice) not in lessons:
            print(Fore.RED + "Invalid lesson number.")
            continue

        lesson = int(lesson_choice)

        # Determine the original_lesson
        if lesson == 8:
            # For review lessons, pick a random lesson between 1 and 7
            original_lesson = random.randint(1, 7)
        else:
            original_lesson = lesson

        # Create a sample mistake entry
        question_text = f"Sample question for Chapter {chapter}, Lesson {lesson}"
        user_answer = "Incorrect answer"
        correct_answer = "Correct answer"

        # Save the mistake to the database
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO mistakes (user_id, chapter, lesson, question, user_answer, correct_answer, original_lesson)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (progress.user_id, chapter, lesson, question_text, user_answer, correct_answer, original_lesson)
                )
                conn.commit()
                logging.info(f"Mistake recorded for user {progress.user_id} in Chapter {chapter} Lesson {lesson}.")
                print(Fore.GREEN + "Mistake data generated and saved.")
        except sqlite3.Error as e:
            logging.error(f"Failed to add mistake: {e}")
            print(Fore.RED + f"Failed to save mistake: {e}")

        another = input("Generate mistake for another lesson? (Y/N): ").strip().lower()
        if another != 'y':
            break

def generate_chapter_review_testing(progress):
    """Generate chapter review for selected chapter."""
    while True:
        print("\nSelect a Chapter to generate review (or 'B' to go back):")
        for chapter_num, chapter_info in chapters.items():
            print(f"{chapter_num}) {chapter_info['title']}")

        chapter_choice = input("Enter chapter number: ").strip()
        if chapter_choice.lower() == 'b':
            return

        if not chapter_choice.isdigit() or int(chapter_choice) not in chapters:
            print(Fore.RED + "Invalid chapter number.")
            continue

        chapter = int(chapter_choice)

        # Check if lesson content for all lessons is available
        lessons = chapters[chapter]['lessons']
        missing_content = False
        for lesson_num in lessons:
            if lesson_num == 8:
                continue  # Skip review lesson
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT content
                    FROM lesson_content
                    WHERE user_id = ? AND chapter = ? AND lesson = ?
                    ''',
                    (progress.user_id, chapter, lesson_num)
                )
                row = cursor.fetchone()
                if not row:
                    print(Fore.RED + f"Lesson content missing for Chapter {chapter}, Lesson {lesson_num}. Cannot generate review.")
                    missing_content = True
                    break
        if missing_content:
            continue

        # Generate the chapter review
        print(Fore.GREEN + f"Generating chapter review for Chapter {chapter}...")
        questions = generate_review_questions(progress, chapter)
        print(Fore.GREEN + f"Chapter review generated with {len(questions)} questions.")

        another = input("Generate review for another chapter? (Y/N): ").strip().lower()
        if another != 'y':
            break

def cumulative_review_test(progress):
    """Conduct the cumulative review covering all chapters and return pass status."""
    questions = generate_cumulative_review(progress)
    correct_answers = 0

    print(Fore.MAGENTA + "\n--- Final Cumulative Review: All Chapters ---")
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n")

    for i, question_data in enumerate(questions):
        print(f"\nQuestion {i + 1}/{len(questions)}:")
        chapter = question_data.get('chapter', 1)
        lesson = question_data.get('lesson', None)
        correct = ask_question_and_validate(question_data, progress, chapter, lesson)
        if correct:
            correct_answers += 1
        else:
            # Record the mistake using add_mistake
            progress.add_mistake(
                chapter=chapter,
                lesson=lesson,
                question=question_data.get('question', ''),
                user_answer='Incorrect',  # Replace with actual user input if available
                correct_answer=question_data.get('correct_answer', ''),
                feedback='',  # Provide feedback if available
                original_lesson=question_data.get('original_lesson', None)
            )

    if correct_answers >= int(len(questions) * 0.7):
        print(Fore.GREEN + "Congratulations! You passed the cumulative review!\n")
        return True
    else:
        print(Fore.RED + "You did not pass the cumulative review. Please try again.\n")
        return False


def generate_all_lesson_content_and_mistakes(progress):
    """Generate and save lesson content and mistake data for all chapters and lessons."""
    print(Fore.GREEN + "Generating lesson content and mistake data for all chapters and lessons...")

    total_lessons = 0
    lessons_with_errors = []

    for chapter_num, chapter_info in chapters.items():
        lessons = chapter_info['lessons']
        for lesson_num in lessons:
            # Skip if it's a cumulative review chapter (like chapter 21 in your config)
            if chapter_num == 21:
                continue
            # Generate lesson content for lessons 1-7
            if lesson_num != 8:  # Exclude review lessons for content generation
                try:
                    lesson_title = chapters[chapter_num]['lessons'][lesson_num]['title']
                    print(Fore.GREEN + f"Generating content for Chapter {chapter_num}, Lesson {lesson_num}: {lesson_title}")
                    lesson_content = generate_lesson_content(progress, chapter_num, lesson_num)
                    total_lessons += 1
                except Exception as e:
                    print(Fore.RED + f"Failed to generate content for Chapter {chapter_num}, Lesson {lesson_num}: {e}")
                    lessons_with_errors.append((chapter_num, lesson_num))
            else:
                print(Fore.YELLOW + f"Skipping content generation for Chapter {chapter_num}, Lesson {lesson_num} (Review Lesson)")

            # Generate mistake data for all lessons, including review lessons
            try:
                # Determine the original_lesson
                if lesson_num == 8:
                    # For review lessons, pick a random lesson between 1 and 7
                    original_lesson = random.randint(1, 7)
                else:
                    original_lesson = lesson_num

                question_text = f"Sample question for Chapter {chapter_num}, Lesson {lesson_num}"
                user_answer = "Incorrect answer"
                correct_answer = "Correct answer"

                # Save the mistake to the database
                with sqlite3.connect('progress.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        '''
                        INSERT INTO mistakes (user_id, chapter, lesson, question, user_answer, correct_answer, original_lesson)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (progress.user_id, chapter_num, lesson_num, question_text, user_answer, correct_answer, original_lesson)
                    )
                    conn.commit()
                    logging.info(f"Mistake recorded for user {progress.user_id} in Chapter {chapter_num} Lesson {lesson_num}.")
            except sqlite3.Error as e:
                logging.error(f"Failed to add mistake for Chapter {chapter_num}, Lesson {lesson_num}: {e}")
                print(Fore.RED + f"Failed to save mistake for Chapter {chapter_num}, Lesson {lesson_num}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error for Chapter {chapter_num}, Lesson {lesson_num}: {e}")
                print(Fore.RED + f"Unexpected error for Chapter {chapter_num}, Lesson {lesson_num}: {e}")

    print(Fore.GREEN + f"\nGenerated lesson content for {total_lessons} lessons.")
    if lessons_with_errors:
        print(Fore.RED + "Some lessons encountered errors during content generation:")
        for chapter_num, lesson_num in lessons_with_errors:
            print(f"- Chapter {chapter_num}, Lesson {lesson_num}")
    else:
        print(Fore.GREEN + "All lesson content generated successfully.")

    print(Fore.GREEN + "Mistake data generated for all lessons.")
# Main entry point
if __name__ == "__main__": # Check if the script is being run directly
    welcome()  # Start with the welcome screen
