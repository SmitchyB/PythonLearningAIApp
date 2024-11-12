from colorama import Fore, init # Import the Fore and init functions from colorama to change text color
import sqlite3 # Import the sqlite3 module to work with SQLite databases
import bcrypt # Import the bcrypt module for password hashing
from config import chapters # Import the chapters dictionary from config.py to access the lesson content
from questions import validate_answer_with_gpt, generate_lesson_content, generate_questions_from_content, generate_review_questions, generate_cumulative_review # Import functions from questions.py to generate questions, reviews, lesson content, and validate answers for code and scenario questions.
from fuzzywuzzy import fuzz # Import the fuzz function from fuzzywuzzy to compare strings
import subprocess # Import the subprocess module to run the user's code
import sys # Import the sys module to access system-specific parameters and functions
import random # Import the random module to generate random numbers
from kivy.config import Config
Config.set('graphics', 'width', '360')  # Example width for a phone screen
Config.set('graphics', 'height', '640')  # Example height for a phone screen
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout

#Run the user's code and capture output or errors
def run_user_code(code): # Define the run_user_code function
    try: 
        # Running code in a subprocess to prevent main app crashes
        result = subprocess.run(
            [sys.executable, "-c", code],  # Use current Python interpreter
            capture_output=True, text=True, timeout=5  # Capture output/errors
        )
        return result.stdout.strip(), result.stderr.strip()  # Return output and errors
    except subprocess.TimeoutExpired: # Handle timeout
        return "", "Execution timed out."  # Handle timeout case
    except Exception as e: # Handle generic exceptions
        return "", f"An error occurred: {str(e)}"  # Handle generic errors

# Initialize colorama to reset color after each print
init(autoreset=True) # Initialize colorama

# Track user progress and score *currently using in Kivy code*
class UserProgress: # Define the UserProgress class
    
    # Initialize the UserProgress class
    def __init__(self, user_id):
        self.user_id = user_id
        self.chapter = 1  # Default start at Chapter 1
        self.lesson = 1  # Default start at Lesson 1
        self.load_progress()  # Load progress from database on initialization
        
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
    def save_progress(self):
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET chapter = ?, lesson = ? WHERE id = ?',
                    (self.chapter, self.lesson, self.user_id)
                )
                conn.commit()
                print(f"Progress saved: Chapter {self.chapter}, Lesson {self.lesson} for User ID {self.user_id}")  # Debugging line
        except sqlite3.Error as e:
            print(f"Failed to save progress: {e}")
    def load_progress(self):
        """Load the user's progress from the database."""
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT chapter, lesson FROM users WHERE id = ?',
                    (self.user_id,)
                )
                row = cursor.fetchone()
                if row:
                    self.chapter, self.lesson = row
                    print(f"Loaded progress: Chapter {self.chapter}, Lesson {self.lesson} for User ID {self.user_id}")
                else:
                    print(f"No progress found for User ID {self.user_id}, starting at default values.")
        except sqlite3.Error as e:
            print(f"Failed to load progress: {e}")
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
    
# Helper function to calculate the percentage score *will use keep this function for later implementation in Kivy code*
def calculate_percentage_score(correct, total): # Define the calculate_percentage_score function
    return (correct / total) * 100 if total > 0 else 0 # Calculate the percentage score

# # Function to generate review questions *will use keep this function for later implementation in Kivy code*
# def review_test(progress): # Define the review_test function
#     chapter = progress.chapter # Get the current chapter
#     try: # Try to clear the user's previous mistakes
#         with sqlite3.connect('progress.db') as conn: # Connect to the database
#             cursor = conn.cursor() # Create a cursor object
#             # Assuming lesson number for review test is always set to 8
#             cursor.execute( # Execute an SQL query
#                 '''
#                 DELETE FROM mistakes WHERE user_id = ? AND chapter = ? AND lesson = ?
#                 ''',
#                 (progress.user_id, chapter, 8) # Pass the user ID, chapter, and lesson as parameters
#             )
#             conn.commit() # Commit the transaction
#     except sqlite3.Error as e: # Handle database errors
#         print(f"Failed to clear previous mistakes: {e}") # Print an error message

#     questions = generate_review_questions(progress, chapter) # Generate review questions for the chapter
#     correct_answers = 0 # Initialize the number of correct answers

#     print(Fore.MAGENTA + f"\n--- Review Test: {chapters[chapter]['title']} ---") # Print the review test title
#     print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score

#     for i, question_data in enumerate(questions): # Iterate over the questions
#         print(f"\nQuestion {i + 1}/{len(questions)}:") # Print the question number
#         correct = ask_question_and_validate(question_data, progress, chapter, lesson=8) # Ask the question and validate the answer
#         if correct: # Handle correct answers
#             correct_answers += 1 # Increment the correct answers count

#     if correct_answers >= int(len(questions) * 0.7): # Check if the user passed the review
#         print(Fore.GREEN + "Congratulations! You passed the review.\n") # Print a success message
#         return True # Return True for passing the review
#     else: # Handle failing the review
#         print(Fore.RED + "You did not pass the review. Try again!\n") # Print an error message
#         return False # Return False for failing the review

# #Function to generate cumulative review questions *will use keep this function for later implementation in Kivy code*
# def cumulative_review_test(progress): # Define the cumulative_review_test function
#     """Conduct the cumulative review covering all chapters and return pass status.""" 
#     questions = generate_cumulative_review(progress) # Generate cumulative review questions
#     correct_answers = 0 # Initialize the number of correct answers
 
#     print(Fore.MAGENTA + "\n--- Final Cumulative Review: All Chapters ---") # Print the cumulative review title
#     print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score
    
#     # For each question in the cumulative review, run the ask_question_and_validate function and track the correct answers
#     for i, question_data in enumerate(questions): # Iterate over the questions
#         print(f"\nQuestion {i + 1}/{len(questions)}:") # Print the question number
#         chapter = question_data.get('chapter', 1) # Get the chapter number
#         lesson = question_data.get('lesson', None) # Get the lesson number
#         if ask_question_and_validate(question_data, progress, chapter, lesson): # Ask the question and validate the answer
#             correct_answers += 1 # Increment the correct answers count
#         else: # Handle incorrect answers
#             chapter = question_data.get('chapter', 1)  # Track which chapter the mistake came from
#             progress.add_review_mistake(chapter) # Track the review mistakes

#     # Check if the user passed the cumulative review
#     if correct_answers >= int(len(questions) * 0.7): # Check if the user passed the cumulative review
#         print(Fore.GREEN + "Congratulations! You passed the cumulative review!\n") # Print a success message
#         return True # Return True for passing the cumulative review
#     else: # Handle failing the cumulative review
#         print(Fore.RED + "You did not pass the cumulative review. Please try again.\n") # Print an error message
#         return False # Return False for failing the cumulative review

#This starts the new code that converst my previous terminal based code to a Kivy app
#class to handle the login screen
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
# class to handle the main screen
class MainScreen(Screen): # Define the MainScreen class
    # Initialize the MainScreen class
    def __init__(self, **kwargs): # Define the constructor
        super().__init__(**kwargs) # Call the superclass constructor
        self.user_id = None  # Initialize user_id
    # Function that runs when the screen is entered
    def on_enter(self): # Define the on_enter function
        # Load user progress
        if self.user_id is not None: # Check if user_id is set
            user_progress = UserProgress(user_id=self.user_id) # Initialize UserProgress
            self.populate_roadmap(user_progress) # Populate the roadmap
    # Function to populate the roadmap
    def populate_roadmap(self, user_progress=None): # Define the populate_roadmap function
        if not self.user_id: # Check if user_id is set
            print("Error: user_id is not set.")
            return # Exit the function if user_id is not set

        roadmap_layout = self.ids.roadmap_layout # Get the roadmap layout
        roadmap_layout.clear_widgets()  # Clear any existing widgets

        if user_progress is None: # Initialize UserProgress if not provided
            user_progress = UserProgress(user_id=self.user_id) # Initialize UserProgress
        unlocked_chapters = user_progress.chapter # Include all unlocked chapters
        unlocked_lessons = user_progress.lesson # Include all unlocked lessons

        total_height = 0  # Track the total height of the content for ScrollView

        # Loop through chapters defined in config.py
        for chapter_num, chapter_data in chapters.items(): # Iterate over chapters 
            if chapter_num > unlocked_chapters: # Skip locked chapters
                continue  # Skip locked chapters

            # Parent container for each chapter (GridLayout for consistent sizing)
            chapter_container = GridLayout( # GridLayout for consistent sizing
                cols=1, # Single column
                size_hint_y=None, # Required for height to take effect
                spacing=10, # Spacing between elements
                padding=[10, 10], # Padding for each chapter
            ) 

            # Chapter indicator (Label)
            chapter_label = Label( # Label for chapter title
                text=f"Chapter {chapter_num}: {chapter_data.get('title', 'Unknown')}", # Display chapter title
                size_hint_y=None, # Required for height to take effect
                height=40, # Adjust height as needed
                color=(1, 1, 1, 1), # White text
                halign='center', # Center the text horizontally
                valign='middle', # Center the text vertically
                text_size=(self.width - 40, None),  # Adjust text wrapping width (subtract some padding)
                size_hint_x=None,  # Required to control text wrapping
                width=self.width - 40  # Ensure it matches the `text_size` width to wrap properly
            )
            chapter_container.add_widget(chapter_label) # Add chapter label to chapter container
            # Container for lessons (GridLayout)
            lesson_box = GridLayout(
                cols=1,
                size_hint_y=None,
                spacing=10,
                padding=[20, 10],
            )
            # Loop through lessons (ensure all unlocked lessons are shown)
            for lesson_num in range(1, unlocked_lessons + 1): # Include all unlocked lessons
                lesson_data = chapter_data['lessons'].get(lesson_num) # Get lesson data
                if lesson_data: # Check if lesson data is available
                    lesson_button = Button( # Button for each lesson
                        text=f"Lesson {lesson_num}", # Display lesson number
                        size_hint_y=None, # Required for height to take effect
                        height=40, # Adjust height as needed
                        on_press=lambda btn, ch=chapter_num, ln=lesson_num: self.load_lesson_screen(ch, ln) # Pass chapter and lesson numbers
                    ) 
                    lesson_box.add_widget(lesson_button) # Add lesson button to lesson box
            # Adjust lesson_box height based on its contents
            lesson_box.height = lesson_box.minimum_height # Set the height of the lesson box
            chapter_container.add_widget(lesson_box) # Add lesson box to chapter container
            # Set container height based on contents
            chapter_container.height = chapter_label.height + lesson_box.height + 20  # Adding padding between elements
            roadmap_layout.add_widget(chapter_container) # Add chapter container to the roadmap layout
            total_height += chapter_container.height # Add the chapter container height to the total height
        roadmap_layout.height = total_height # Set the height of the roadmap layout
    # Function to load the lesson screen
    def load_lesson_screen(self, chapter, lesson): # Define the load_lesson_screen function
        # Navigate to the lesson screen and load the lesson
        lesson_screen = self.manager.get_screen('lesson') # Get the LessonScreen instance
        lesson_screen.load_lesson(self.user_id, chapter, lesson) # Pass user_id, chapter, and lesson
        self.manager.current = 'lesson' # Transition to the lesson screen
# class to handle the lesson screen
class LessonScreen(Screen): # Define the LessonScreen class
    lesson_parts = []  # Default value for lesson_parts
    current_part = 0   # Default value for current_part
    # Initialize the LessonScreen class
    def __init__(self, **kwargs): # Define the constructor
        super().__init__(**kwargs) # Call the superclass constructor
        self.lesson_parts = []  # Initialize an empty list for lesson parts
        self.current_part = 0  # Initialize current part index
        self.chapter = None  # Initialize chapter attribute
        self.lesson = None  # Initialize lesson attribute
    # Function to load the lesson content
    def load_lesson(self, user_id, chapter, lesson): # Define the load_lesson function
        print(f"Loading lesson for User ID: {user_id}, Chapter: {chapter}, Lesson: {lesson}") # Debugging
        self.chapter = chapter  # Store the chapter value
        self.lesson = lesson  # Store the lesson value
        try: # Try to clear the user's previous mistakes
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    DELETE FROM mistakes WHERE user_id = ? AND chapter = ? AND lesson = ?
                    ''',
                    (user_id, chapter, lesson) # Pass the user ID, chapter, and lesson as parameters
                )
                conn.commit() # Commit the transaction
            print("Cleared previous mistakes for the current lesson.") # Debugging line
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to clear previous mistakes: {e}") # Debugging line

        progress = UserProgress(user_id=user_id) # Initialize UserProgress
        lesson_content = generate_lesson_content(progress, chapter, lesson) # Generate lesson content
        print(f"Generated Lesson Content:\n{lesson_content}") # Debugging statement

        self.lesson_parts = [part.strip() for part in lesson_content.split("\n\n") if part.strip()] # Split the lesson parts
        self.current_part = 0   # Reset current part index
        if self.lesson_parts:
            self.ids.lesson_content.text = self.lesson_parts[self.current_part] # Display the first part
        else:
            self.ids.lesson_content.text = "No content available." # Error Handling/Debugging line

        # Generate questions from lesson content
        question_count = chapters[chapter]['lessons'][lesson].get('question_count') # Get question count
        if not question_count: # Check if question count is not specified
            print("Error: No question count specified for this lesson.") # Print an error message
            self.questions = []  # Ensure questions list is initialized even if empty
        else: # Generate questions
            self.questions = generate_questions_from_content(chapter, lesson, lesson_content, question_count) # Generate questions
            print(f"Generated Questions: {self.questions}") # Debugging statement
    # Function to store questions for transition
    def store_questions_for_transition(self, questions, chapter, lesson): # define the store_questions_for_transition function
        question_screen = self.manager.get_screen("questions")  # Get the QuestionScreen instance
        if question_screen:  # Check if QuestionScreen is found   
            question_screen.set_questions(questions, chapter, lesson) # Set the questions on the QuestionScreen
        else: # Handle case where QuestionScreen is not found
            print("Failed to retrieve QuestionScreen") # Debug message
    # Function to update the lesson display
    def update_lesson_display(self): # Define the update_lesson_display function
        content = self.lesson_parts[self.current_part] # Get the content for the current part
        self.ids.lesson_content.text = content  # Update the lesson content
    # Function to navigate to the next lesson part
    def next_lesson_part(self): # Define the next_lesson_part function
        if self.current_part < len(self.lesson_parts) - 1: # Check if not at the end
            self.current_part += 1 # Move to the next part
            self.update_lesson_display() # Update the lesson display
        else:
            self.store_questions_for_transition(self.questions, self.chapter, self.lesson)  # Add this call here if not present
            self.manager.current = "questions" # Transition to the questions screen
        self.update_navigation_buttons()  # Update the navigation buttons
    # Function to navigate to the previous lesson part
    def previous_lesson_part(self): # Define the previous_lesson_part function
        if self.current_part > 0: # Check if not at the beginning
            self.current_part -= 1 # Move to the previous part
            self.update_lesson_display() # Update the lesson display
        self.update_navigation_buttons() # Update the navigation buttons
    # Function to update the visibility and enable state of navigation buttons
    def update_navigation_buttons(self): # Define the update_navigation_buttons function
        # Control visibility and enable state of back button
        self.ids.back_button.opacity = 1 if self.current_part > 0 else 0 # Hide if at the beginning
        self.ids.back_button.disabled = self.current_part <= 0 # Disable if at the beginning
class ProfileScreen(Screen):
    pass
class MistakesScreen(Screen):
    pass
class ChapterReviewScreen(Screen):
    pass
class CumulativeReviewScreen(Screen):
    pass
# class to handle the question screen
class QuestionScreen(Screen): # Define the QuestionScreen class
    def __init__(self, **kwargs): # Define the constructor
        super().__init__(**kwargs) # Call the superclass constructor
        self.questions = []  # To store the questions for the screen
        self.current_question_index = 0  # To track the current question index
        self.chapter = None  # To store the current chapter number
        self.lesson = None  # To store the current lesson number
        self.selected_answer = None  # To track selected answers for multiple choice
        self.awaiting_next_submission = False  # To prevent multiple submissions
        self.feedback_label = None # To store the feedback label
    def set_questions(self, questions, chapter, lesson): # Define the set_questions function
        print(f"set_questions called with questions: {questions}, Chapter: {chapter}, Lesson: {lesson}")  # Debug statement
        self.questions = questions # Store the questions
        self.chapter = chapter # Store the chapter numbers
        self.lesson = lesson  # Store the lesson numbers
        self.current_question_index = 0  # Reset the current question index
        self.display_next_question()  # Ensure this call is here
    # Function to display the next question
    def display_next_question(self): # Define the display_next_question function
        print("display_next_question called")  # Debug statement
        if not self.questions or self.current_question_index >= len(self.questions): # Check if there are no questions or end of questions reached
            print("No questions available or end of questions reached.") # Debug statement
            self.ids.question_content.text = "No questions available." # Update the question content

            # Unlock the next lesson and save progress
            user_progress = UserProgress(self.manager.get_screen('main').user_id) # Retrieve user progress
            if self.lesson is not None and self.chapter is not None: # Ensure lesson and chapter are set
                total_lessons_in_chapter = len(chapters[self.chapter]['lessons']) - 1 # Subtract 1 for review lesson 
                if self.lesson < total_lessons_in_chapter: # Check if there are more lessons in the chapter
                    user_progress.lesson += 1  # Unlock the next lesson
                else:
                    user_progress.chapter += 1  # Unlock the next chapter if all lessons are complete
                    user_progress.lesson = 1  # Reset to the first lesson of the next chapter
                user_progress.save_progress()  # Ensure this line is called

            # Transition back to the main screen
            self.manager.current = 'main' # Transition back to the main screen
            self.manager.get_screen('main').on_enter()  # Refresh the main screen if necessary
            return # Exit the function

        self.awaiting_next_submission = False # Reset the flag
        question = self.questions[self.current_question_index] # Get the current question
        print(f"Displaying question: {question}")  # Debugging statement

        self.ids.feedback_label.text = ""  # Clear the feedback label

        # Display the question text
        question_text = question.get('question', 'No question text available') # Get the question text
        lines = question_text.split('\n') # Split the question text into lines
        filtered_lines = [line for line in lines if not line.startswith(('MULTIPLE CHOICE QUESTION', 'Chapter:', 'Lesson:', 'Options:', 'Question:'))] # Filter out metadata
        cleaned_question_text = "\n".join(filtered_lines).strip() # Clean up the question text

        # If multiple-choice, add options to the question text
        if question.get('type') == 'multiple_choice': # For multiple choice questions
            options = question.get('options', {}) # Get the options
            formatted_options = "\n".join([f"{key}) {value}" for key, value in options.items()]) # Format options
            cleaned_question_text = f"{cleaned_question_text}\n\n{formatted_options}" # Append options to the question text

        self.ids.question_content.text = cleaned_question_text # Display the question text

        self.ids.answer_area.clear_widgets() # Clear existing answer area widgets

        # Handle different question types
        if question.get('type') == 'multiple_choice':  # For multiple choice questions
            for key in ["A", "B", "C", "D"]: # Add A, B, C, D buttons
                btn = Button(text=key, size_hint=(None, None), height=40, width=40) # Adjust width as needed
                btn.bind(on_press=self.on_option_selected) # Bind the button press event
                self.ids.answer_area.add_widget(btn) # Add the button to the answer area
        elif question.get('type') == 'true_false': # For true/false questions
            for option in ["True", "False"]: # Add True and False buttons
                btn = Button(text=option, size_hint=(None, None), height=40, width=100) # Adjust width as needed
                btn.bind(on_press=self.on_option_selected) # Bind the button press event
                self.ids.answer_area.add_widget(btn) # Add the button to the answer area
        else:  # For fill in the blank, write code, and scenarios
            text_input = TextInput(hint_text="Enter your answer", multiline=False, size_hint=(0.8, None), height=40) # Adjust size_hint as needed
            self.ids.answer_area.add_widget(text_input) # Add the text input widget
            self.ids.user_input = text_input # Store the text input reference
    # Function to handle the selection of an option
    def on_option_selected(self, instance): # Define the on_option_selected function
        # Change color to indicate selection and store the selected answer
        for child in self.ids.answer_area.children: # Iterate over the answer area children
            if isinstance(child, Button): # Check if the child is a Button
                child.background_color = [1, 1, 1, 1]  # Reset color
        instance.background_color = [0, 1, 0, 1]  # Highlight selected button
        self.selected_answer = instance.text # Store the selected answer
    # Function to handle the submission of an answer
    def submit_answer(self): # Define the submit_answer function
        if self.awaiting_next_submission: # Prevent multiple submissions
            # Move to the next question after showing feedback
            self.current_question_index += 1 # Move to the next question
            self.display_next_question() # Ensure this call is here
            return # Exit the function

        if self.questions: # Ensure questions are available
            question = self.questions[self.current_question_index] # Get the current question
            correct = False  # Track whether the answer was correct
            user_answer = ""    # Initialize user answer

            if question.get('type') in ['multiple_choice', 'true_false']: # Handle multiple choice and true/false questions
                user_answer = self.selected_answer   # Get the selected answer
                if user_answer: # Validate the answer 
                    correct = self.validate_answer(question, user_answer) # Validate the answer
            elif question.get('type') == 'fill_in_the_blank': # Handle fill in the blank questions
                user_answer = self.ids.user_input.text if hasattr(self.ids, 'user_input') else "" # Get user input
                correct = self.validate_answer(question, user_answer)
            elif question.get('type') == 'write_code': # Handle code questions
                user_code = self.collect_code_input() # Collect the user's code input
                correct, feedback = self.validate_code_answer(question, user_code) # Validate the code answer
                db_feedback = self.get_feedback_from_mistakes(self.manager.get_screen('main').user_id, self.chapter, self.lesson, question.get('question', '')) # Retrieve feedback from mistakes
                feedback += f"\n{db_feedback}"  # Append feedback from mistakes
                self.display_feedback(correct, feedback, question.get('correct_answer')) # Display feedback
            elif question.get('type') == 'scenario': # Handle scenario questions
                user_response = self.collect_scenario_response() # Collect the user's response
                correct, feedback = self.validate_scenario_answer(question, user_response) # Validate the scenario response
                db_feedback = self.get_feedback_from_mistakes(self.manager.get_screen('main').user_id, self.chapter, self.lesson, question.get('question', '')) # Retrieve feedback from mistakes
                feedback += f"\n{db_feedback}" # Append feedback from mistakes
                self.display_feedback(correct, feedback, question.get('correct_answer')) # Display feedback

            # Display feedback for all other types 
            if question.get('type') not in ['write_code', 'scenario']:  # Handled separately
                self.display_feedback(correct, "", question.get('correct_answer')) # Display feedback

            self.awaiting_next_submission = True # Set flag to wait for next submission
    # Function to validate answers for multiple choice, true/false, and fill in the blank questions
    def validate_answer(self, question_data, user_answer): # Define the validate_answer function
        correct = False # Track whether the answer was correct
        if question_data['type'] == 'multiple_choice': # Case-sensitive comparison
            correct = user_answer == question_data.get('correct_answer') # Case-sensitive comparison
        elif question_data['type'] == 'true_false': # Case-insensitive comparison
            correct = user_answer.lower() == question_data.get('correct_answer', '').lower() # Case-insensitive comparison
        elif question_data['type'] == 'fill_in_the_blank': # Case-insensitive comparison
            correct = user_answer.lower() == question_data.get('correct_answer', '').lower() #Case-insensitive comparison

        if not correct: # Save the mistake if incorrect
            self.save_mistake(question_data, user_answer) # Save the mistake
        return correct # Return the validation result
    # Function to validate code answers
    def validate_code_answer(self, question_data, user_code): # Define the validate_code_answer function
        user_output, user_errors = run_user_code(user_code) # Run the user code and capture output/errors
        correct, feedback = validate_answer_with_gpt( # Validate the answer using GPT
            question_data, user_code=user_code, user_output=user_output # Pass the question data, user code, and user output
        )
        feedback_message = feedback  # Initialize feedback message with GPT feedback

        # Save the mistake if incorrect
        if not correct: # Check if the answer is incorrect
            feedback_message += f"\n\nYour Output:\n{user_output or 'No output.'}" # Include user output in feedback
            if user_errors: # Check if there are user errors
                feedback_message += f"\n\nErrors:\n{user_errors}" # Include user errors in feedback
            self.save_mistake(question_data, user_code, feedback_message) # Save the mistake
        
        return correct, feedback_message # Return the validation result and feedback
    # Function to validate scenario answers
    def validate_scenario_answer(self, question_data, user_response): # Define the validate_scenario_answer function
        print("Scenario Question Validation:")  # Log for scenario validation
        print(f"Question Data: {question_data}")  # Log the question data
        print(f"User Response: {user_response}")  # Log the user's response

        correct, feedback = validate_answer_with_gpt( # Validate the answer using GPT
            question_data=question_data, # Pass the question data
            user_response=user_response # Pass the user response to the validation function
        )

        print(f"Validation Result: {'Correct' if correct else 'Incorrect'}")  # Log validation result
        print(f"Feedback: {feedback}")  # Log feedback

        if not correct: # Save the mistake if incorrect
            self.save_mistake(question_data, user_response, feedback) # Save the mistake
        return correct, feedback # Return the validation result and feedback
    # Function to save mistakes
    def save_mistake(self, question_data, user_answer, feedback=""): # Define the save_mistake function
        user_progress = UserProgress(self.manager.get_screen('main').user_id) # Initialize UserProgress
        user_progress.add_mistake( # Add the mistake to the user progress
            chapter=self.chapter, # Include chapter number
            lesson=self.lesson, # Include lesson number
            question=question_data.get('question', ''),  # Include question text
            user_answer=user_answer, # Include user's answer
            correct_answer=question_data.get('correct_answer', ''), # Include correct answer
            feedback=feedback   # Include GPT feedback
        ) 
    # Function to get feedback from mistakes
    def get_feedback_from_mistakes(self, user_id, chapter, lesson, question): # Define the get_feedback_from_mistakes function
        try: # Try to retrieve feedback from the database
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    SELECT feedback FROM mistakes 
                    WHERE user_id = ? AND chapter = ? AND lesson = ? AND question = ?
                    ''', (user_id, chapter, lesson, question) # Pass the parameters
                )
                result = cursor.fetchone() # Fetch the first row from the result set
                return result[0] if result else "No additional feedback available." # Return the feedback if available
        except sqlite3.Error as e: # Handle database errors
            return f"Database error: {e}" # Return an error message if there is an error
    # Function to display feedback
    def display_feedback(self, correct, feedback, correct_answer): # Define the display_feedback function
        feedback_label = self.ids.feedback_label  # Access the feedback label using ids

        if correct: # Correct answer
            feedback_label.text = "Correct!" # Set the feedback label text
            feedback_label.color = (0, 1, 0, 1)  # Green color for correct feedback
        else: # Incorrect answer
            # Include correct answer, feedback from GPT, and any additional feedback if applicable
            feedback_label.text = ( # Set the feedback label text
                f"Correct Answer: {correct_answer}\n{feedback}" # Include correct answer and feedback
            )
            feedback_label.color = (1, 0, 0, 1)  # Red color for incorrect feedback
    # Function to collect scenario response
    def collect_scenario_response(self): # Define the collect_scenario_response function
        if hasattr(self.ids, 'user_input'): # Check if the user input field exists
            return self.ids.user_input.text # Return the user input
        return "" # Return empty string if `user_input` is not found
    # Function to collect code input
    def collect_code_input(self): # Define the collect_code_input function
        if hasattr(self.ids, 'user_input'): # Check if the user input field exists
            return self.ids.user_input.text  # Return the user input
        return "" # Return empty string if `user_input` is not found

Builder.load_file("main.kv") # Load the Kivy file

#Function to start the app
class MyApp(App): # Define the MyApp class
    def build(self): # Define the build method
        sm = ScreenManager() # Create a ScreenManager object
        sm.add_widget(LoginScreen(name="login")) # Add the LoginScreen to the Screen
        sm.add_widget(MainScreen(name="main")) # Add the MainScreen to the Screen
        sm.add_widget(LessonScreen(name="lesson")) # Add the LessonScreen to the Screen
        sm.add_widget(ProfileScreen(name="profile")) # Add the ProfileScreen to the Screen
        sm.add_widget(MistakesScreen(name="mistakes")) # Add the MistakesScreen to the Screen
        sm.add_widget(QuestionScreen(name="questions")) # Add the QuestionScreen to the Screen
        sm.add_widget(ChapterReviewScreen(name="chapter_review")) # Add the ChapterReviewScreen to the Screen
        sm.add_widget(CumulativeReviewScreen(name="cumulative_review")) # Add the CumulativeReviewScreen to the Screen
        return sm
# Main entry point
if __name__ == "__main__":  # Check if the script is being run directly
    MyApp().run() # Run the Kivy application