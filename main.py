from colorama import Fore, init # Import the Fore and init functions from colorama to change text color
import sqlite3 # Import the sqlite3 module to work with SQLite databases
import bcrypt # Import the bcrypt module for password hashing
from config import chapters # Import the chapters dictionary from config.py to access the lesson content
from questions import validate_answer_with_gpt, generate_lesson_content, generate_questions_from_content, generate_review_questions, generate_cumulative_review # Import functions from questions.py to generate questions, reviews, lesson content, and validate answers for code and scenario questions.
from fuzzywuzzy import fuzz # Import the fuzz function from fuzzywuzzy to compare strings
import subprocess # Import the subprocess module to run the user's code
import sys # Import the sys module to access system-specific parameters and functions
import random # Import the random module to generate random numbers
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Triangle
from kivy.uix.widget import Widget
from kivy.config import Config
from kivy.metrics import dp

Config.set('graphics', 'width', '360')  # Example width for a phone screen
Config.set('graphics', 'height', '640')  # Example height for a phone screen

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
                    INSERT INTO mistakes (user_id, chapter, lesson, question, user_answer, correct_answer, feedback, user_code, user_output, user_errors, original_lesson)
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

class LoginScreen(Screen):
    def authenticate_or_register(self, name=None, email=None, password=None):
        if self.ids.main_button.text == "Login":
            # Call existing login logic
            user = self.login_user(email, password)
            if user:
                # Navigate to the main screen if login is successful
                self.manager.current = "main"
        else:
            # Call existing registration logic
            self.register_user(name, email, password)

    def toggle_form(self):
        if self.ids.main_button.text == "Login":
            # Switch to registration form
            self.ids.form_label.text = "Register"
            self.ids.main_button.text = "Register"
            self.ids.switch_text.text = "[color=0000FF][ref=toggle]Already Registered? Login Here[/ref][/color]"
        else:
            # Switch to login form
            self.ids.form_label.text = "Login"
            self.ids.main_button.text = "Login"
            self.ids.switch_text.text = "[color=0000FF][ref=toggle]Not Registered? Register Here[/ref][/color]"

    def login_user(self, email, password):
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                user = cursor.fetchone()
            if user and user[3] and bcrypt.checkpw(password.encode(), user[3].encode() if isinstance(user[3], str) else user[3]):
                print(f"Welcome, {user[1]}!")  # Replace with a Kivy label/message if needed
                # Pass user_id to MainScreen
                main_screen = self.manager.get_screen('main')
                main_screen.user_id = user[0]  # Assuming user[0] is the user_id
                return user
            else:
                self.ids.message_label.text = "Invalid email or password."  # Update Kivy label
        except sqlite3.Error as e:
            self.ids.message_label.text = f"Database error: {e}"
        return None

    def register_user(self, name, email, password):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                    (name, email, hashed_password)
                )
                conn.commit()
                self.ids.message_label.text = "Registration successful! Please login."
        except sqlite3.IntegrityError:
            self.ids.message_label.text = "Error: A user with that email already exists."

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id = None  # Initialize user_id
    def get_chapters(self):
        return chapters  # Returns the chapters dictionary imported from config.py

    def on_enter(self):
        self.populate_roadmap()

    def populate_roadmap(self):
        if not self.user_id:
            print("Error: user_id is not set.")
            return  # Exit the function or handle the error as needed

        roadmap_layout = self.ids.roadmap_layout
        roadmap_layout.clear_widgets()  # Clear previous widgets if any

        chapters = self.get_chapters()  # Replace with your method to fetch chapters
        user_progress = UserProgress(user_id=self.user_id)  # Replace with appropriate user progress instance
        unlocked_chapters = user_progress.chapter  # Assuming progress.chapter gives the current unlocked chapter

        for chapter_num, chapter_data in chapters.items():
            if chapter_num > unlocked_chapters:
                continue  # Skip locked chapters

            chapter_title = chapter_data['title']
            
            # Main container for chapter and lesson with vertical centering
            chapter_and_lesson_container = BoxLayout(
                orientation='horizontal',
                spacing=10,
                size_hint=(None, None),
                height=60,
                width=300,
                pos_hint={"center_y": 0.5}  # This helps with centering within the parent layout
            )
            chapter_and_lesson_container.add_widget(Widget())  # Spacer for centering
            
            # Chapter widget container
            chapter_box = BoxLayout(
                orientation='vertical',
                size_hint=(None, None),
                width=150,
                height=60,
                pos_hint={"center_y": 0.5}  # Ensure centered positioning
            )
            chapter_label = Button(
                text=f"Chapter {chapter_num}\n{chapter_title}",
                size_hint=(None, None),
                width=150,
                height=50,
                background_normal='',
                background_color=(0.3, 0.3, 0.3, 1),
            )
            chapter_box.add_widget(chapter_label)
            chapter_and_lesson_container.add_widget(chapter_box)

            # Lesson widget container
            lesson_box = BoxLayout(
                orientation='vertical',
                size_hint=(None, None),
                width=40,
                height=60
            )
            lesson_num = 1  # Show only the first unlocked lesson for now
            lesson_data = chapter_data['lessons'].get(lesson_num)
            if lesson_data:
                lesson_button = Button(
                    text=f"{lesson_num}\n{lesson_data['title']}",
                    size_hint=(None, None),
                    width=40,
                    height=40,
                    background_normal='',
                    background_color=(0.6, 0.6, 0.6, 1),  # Gray circle
                    on_press=lambda btn, ch=chapter_num, ln=lesson_num: self.load_lesson_screen(ch, ln)  # Call a method to load lesson
                )
                lesson_box.add_widget(Widget())  # Spacer for vertical centering
                lesson_box.add_widget(lesson_button)
                lesson_box.add_widget(Widget())  # Spacer for vertical centering
                chapter_and_lesson_container.add_widget(lesson_box)

            chapter_and_lesson_container.add_widget(Widget())  # Spacer for centering

            # Add the chapter_and_lesson_container to the roadmap layout
            roadmap_layout.add_widget(chapter_and_lesson_container)
    def load_lesson_screen(self, chapter, lesson):
        # Navigate to the lesson screen and load the lesson
        lesson_screen = self.manager.get_screen('lesson')  # Get the lesson screen instance
        lesson_screen.load_lesson(self.user_id, chapter, lesson)  # Pass necessary data to load the lesson
        self.manager.current = 'lesson'  # Switch to the lesson screen

class LessonScreen(Screen):
    lesson_parts = []  # Default value for lesson_parts
    current_part = 0   # Default value for current_part

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lesson_parts = []  # Initialize an empty list for lesson parts
        self.current_part = 0  # Initialize current part index

    def load_lesson(self, user_id, chapter, lesson):
        print(f"Loading lesson for User ID: {user_id}, Chapter: {chapter}, Lesson: {lesson}")
        progress = UserProgress(user_id=user_id)
        lesson_content = generate_lesson_content(progress, chapter, lesson)
        print(f"Generated Lesson Content:\n{lesson_content}")  # Inspect the raw content

        self.lesson_parts = [part.strip() for part in lesson_content.split("\n\n") if part.strip()]
        self.current_part = 0
        if self.lesson_parts:
            print(f"Lesson Parts Loaded: {self.lesson_parts}")  # Debug print for parts loaded
            self.ids.lesson_content.text = self.lesson_parts[self.current_part]
        else:
            print("No content available.")
            self.ids.lesson_content.text = "No content available."
    def update_lesson_display(self):
        """Update the content display based on the current part index."""
        content = self.lesson_parts[self.current_part]
        self.ids.lesson_content.text = content

    
    def next_lesson_part(self):
        if self.current_part < len(self.lesson_parts) - 1:
            self.current_part += 1
            print(f"Moving to Next Part: {self.current_part}, Content: {self.lesson_parts[self.current_part]}")
            self.update_lesson_display()
        else:
            print("Reached end of lesson, transitioning to questions.")
            self.transition_to_questions()
        self.update_navigation_buttons()

    def previous_lesson_part(self):
        if self.current_part > 0:
            self.current_part -= 1
            print(f"Returning to Previous Part: {self.current_part}, Content: {self.lesson_parts[self.current_part]}")
            self.update_lesson_display()
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Control the visibility and state of navigation buttons."""
        # Control visibility and enable state of back button
        self.ids.back_button.opacity = 1 if self.current_part > 0 else 0
        self.ids.back_button.disabled = self.current_part <= 0

    def transition_to_questions(self):
        print("End of lesson content, transitioning to questions.")


class ProfileScreen(Screen):
    pass
class MistakesScreen(Screen):
    pass
class ChapterReviewScreen(Screen):
    pass
class CumulativeReviewScreen(Screen):
    pass
Builder.load_file("main.kv")

class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(LessonScreen(name="lesson"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(MistakesScreen(name="mistakes"))
        return sm
# Main entry point
if __name__ == "__main__":
    MyApp().run()
