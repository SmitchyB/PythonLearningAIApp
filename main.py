from colorama import Fore, init # Import the Fore and init functions from colorama to change text color
import sqlite3 # Import the sqlite3 module to work with SQLite databases
import bcrypt # Import the bcrypt module for password hashing
from config import chapters # Import the chapters dictionary from config.py to access the lesson content
from questions import validate_answer_with_gpt, generate_lesson_content, generate_questions_from_content, generate_review_questions, generate_cumulative_review # Import functions from questions.py to generate questions, reviews, lesson content, and validate answers for code and scenario questions.
from fuzzywuzzy import fuzz # Import the fuzz function from fuzzywuzzy to compare strings
import subprocess # Import the subprocess module to run the user's code
import sys # Import the sys module to access system-specific parameters and functions
from kivy.config import Config # Import the Config class from kivy.config to configure Kivy settings
Config.set('graphics', 'width', '360')  # Example width for a phone screen
Config.set('graphics', 'height', '640')  # Example height for a phone screen
from kivy.app import App # Import the App class from kivy.app to create the Kivy application
from kivy.uix.screenmanager import ScreenManager, Screen # Import the ScreenManager and Screen classes from kivy.uix.screenmanager to manage screens
from kivy.lang import Builder # Import the Builder class from kivy.lang to load Kivy language files
from kivy.uix.button import Button # Import the Button class from kivy.uix.button to create buttons
from kivy.uix.textinput import TextInput # Import the TextInput class from kivy.uix.textinput to create text input fields
from kivy.uix.label import Label # Import the Label class from kivy.u
from kivy.uix.boxlayout import BoxLayout # Import the BoxLayout class from kivy.uix.boxlayout to create layouts
from kivy.uix.popup import Popup # Import the Popup class from kivy.u
from kivy.uix.filechooser import FileChooserIconView # Import the FileChooserIconView class from kivy.uix.filechooser to create a file chooser
from kivy.properties import StringProperty, BooleanProperty # Import the StringProperty and BooleanProperty classes from kivy.properties to define properties
from kivy.clock import Clock # Import the Clock class from kivy.clock to schedule events
import os # Import the os module to interact with the operating system
from PIL import Image as PILImage # Import the Image class from the PIL module to work with images
from kivy.uix.scrollview import ScrollView # Import the ScrollView class from kivy.uix.scrollview to create scrollable views 
from kivy.uix.codeinput import CodeInput    # Import the CodeInput class from kivy.uix.codeinput to create a code input field
from pygments.lexers.python import PythonLexer # Import the PythonLexer class from pygments.lexers.python to highlight Python code
from reportlab.pdfgen import canvas # Import the canvas class from report
from PIL import Image # Import the Image class from the PIL module to work with images
import datetime # Import the datetime module to work with dates and times
from plyer import filechooser # Import the filechooser module from plyer to access file selection dialogs

#Run the user's code and capture output or errors
def run_user_code(code): # Define the run_user_code function
    try: 
        # Running code in a subprocess to prevent main app crashes
        result = subprocess.run( # Run the code in a subprocess
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

    # save the user's progress       
    def save_progress(self): # Define the save_progress function
        try: # Try to save the user's progress to the database
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    'UPDATE users SET chapter = ?, lesson = ? WHERE id = ?',
                    (self.chapter, self.lesson, self.user_id) # Pass the chapter, lesson, and user ID as parameters
                )
                conn.commit() # Commit the transaction
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to save progress: {e}") # Print an error message
    def load_progress(self): # Define the load_progress function
        try: # Try to load the user's progress from the database
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    'SELECT chapter, lesson FROM users WHERE id = ?', 
                    (self.user_id,) # Pass the user ID as a parameter
                )
                row = cursor.fetchone() # Fetch the first row from the result set
                if row: # Check if the row exists
                    self.chapter, self.lesson = row # Unpack the row
                    print(f"Loaded progress: Chapter {self.chapter}, Lesson {self.lesson} for User ID {self.user_id}") # Debugging line
                else: # Handle no progress found
                    print(f"No progress found for User ID {self.user_id}, starting at default values.") # Debugging line
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to load progress: {e}") # Print an error message
    
#class to handle the login screen
class LoginScreen(Screen): # Define the LoginScreen class
    
    # Function to authenticate or register the user
    def authenticate_or_register(self, name=None, email=None, password=None): # Define the authenticate_or_register function
        if self.ids.main_button.text == "Login": # Check if the button text is "Login"
            user = self.login_user(email, password) # Call the login_user function
            if user: # Check if the user is authenticated
                self.manager.current = "main" # Navigate to the main screen
        else: # Handle registration
            self.register_user(name, email, password) # Call the register_user function
    
    # Function to toggle between login and registration forms
    def toggle_form(self): # Define the toggle_form function
        if self.ids.main_button.text == "Login": # Check if the button text is "Login"
            self.ids.form_label.text = "Register" # Update the form label to "Register"
            self.ids.main_button.text = "Register" # Update the button text to "Register"
            self.ids.switch_text.text = "[color=0000FF][ref=toggle]Already Registered? Login Here[/ref][/color]" # Update the switch text
        else: # Handle registration form
            self.ids.form_label.text = "Login" # Update the form label to "Login"
            self.ids.main_button.text = "Login" # Update the button text to "Login"
            self.ids.switch_text.text = "[color=0000FF][ref=toggle]Not Registered? Register Here[/ref][/color]" # Update the switch text
    
    # Function to handle the login process
    def login_user(self, email, password): # Define the login_user function
        try: # Try to authenticate the user
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,)) # Execute an SQL query
                user = cursor.fetchone() # Fetch the first row from the result set
            if user and user[3] and bcrypt.checkpw(password.encode(), user[3].encode() if isinstance(user[3], str) else user[3]): # Check if the user exists and the password matches
                App.get_running_app().user_id = user[0]
                # Pass user_id to MainScreen
                main_screen = self.manager.get_screen('main')
                main_screen.user_id = user[0]  # Assuming user[0] is the user_id
                self.manager.current = "main"  # Navigate to the main screen
                return user
            else:
                self.ids.message_label.text = "Invalid email or password."  # Update Kivy label
        except sqlite3.Error as e:
            self.ids.message_label.text = f"Database error: {e}"
        return None

    # Function to handle user registration
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
        self.user_name = ""  # Initialize user_name with an empty value
    
    # Function that runs when the screen is entered
    def on_enter(self): # Define the on_enter function
        try: # Try to fetch user data from the database
            if self.user_id is None: # Check if user_id is not set
                print("Error: user_id is not set.") 
                return # Exit the function

            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                # Corrected SQL query to fetch the user by the `id` column, not `user_id`
                cursor.execute('SELECT id, name, chapter, lesson FROM users WHERE id = ?', (self.user_id,)) # Execute an SQL query
                result = cursor.fetchone() # Fetch the first row from the result set
                if result: # Check if a result is found
                    self.user_id, self.user_name, chapter, lesson = result
                    print(f"User found: ID={self.user_id}, Name={self.user_name}, Chapter={chapter}, Lesson={lesson}")
                else: # Handle case where user is not found 
                    self.user_name = "Default User" # Set a default user name
                    print("User not found. Setting default name.")

        except sqlite3.Error as e: # Handle database errors
            print(f"Database error while fetching user data: {e}") # Print an error message
            self.user_name = "" # Set a default user name

        # Load user progress if user_id is set
        if self.user_id is not None: # Check if user_id is set
            self.populate_roadmap()  # Populate the roadmap
            self.load_profile_picture()  # Load the profile picture

    # Function to load the user's profile picture
    def load_profile_picture(self): # Define the load_profile_picture function
        profile_pic_path = f'profile_pics/user_{self.user_id}.png' # Set the profile picture path
        if not os.path.exists(profile_pic_path): # Check if the file does not exist
            profile_pic_path = 'Assets/default_profile_pic.webp'  # Default picture path
        
        self.ids.profile_pic.source = profile_pic_path # Update the profile picture source

    # # Function to initialize the database connection ***REMOVE BEFORE SUBMISSION***
    # def set_progress_to_maximum(self): # Define the set_progress_to_maximum function
    #     user_progress = UserProgress(self.user_id) # Initialize UserProgress
    #     user_progress.chapter = 20  # Set to maximum chapter number
    #     user_progress.lesson = 8    # Set to maximum lesson number in the chapter
    #     user_progress.save_progress() # Save the updated progress
    #     self.populate_roadmap()     # Refresh the roadmap to reflect the new progress
    
    # Function to populate the roadmap
    def populate_roadmap(self, user_progress=None):  # Define the populate_roadmap function
        if not self.user_id: # Check if user_id is not set
            print("Error: user_id is not set.") # Print an error message
            return # Exit the function

        roadmap_layout = self.ids.roadmap_layout # Get the roadmap layout
        roadmap_layout.clear_widgets() # Clear existing widgets

        if user_progress is None: # Check if user_progress is not provided
            user_progress = UserProgress(user_id=self.user_id) # Initialize UserProgress
        unlocked_chapters = user_progress.chapter # Get the unlocked chapter
        unlocked_lessons = user_progress.lesson # Get the unlocked lesson

        for chapter_num, chapter_data in chapters.items(): # Iterate over the chapters
            # Display chapters up to and including the unlocked chapter
            if chapter_num > unlocked_chapters: # Check if the chapter is locked
                break  # Stop adding further chapters

            chapter_container = BoxLayout( # Create a BoxLayout for the chapter
                orientation='vertical', # Set the orientation to vertical
                size_hint_y=None, # Set the size hint for y-axis
                height=0,  # Will be updated based on content
                spacing=10, # Set the spacing between widgets
                padding=[10, 10], # Set the padding
            ) 

            chapter_label = Label( # Create a Label for the chapter
                text=f"Chapter {chapter_num}: {chapter_data.get('title', 'Unknown')}",  # Set the text
                size_hint_y=None, # Set the size hint for y-axis
                height=40, # Set the height
                color=(1, 1, 1, 1), # Set the text color
                halign='center', # Set the horizontal alignment
                valign='middle', # Set the vertical alignment
                text_size=(self.width - 40, None), # Set the text size
                size_hint_x=None, # Set the size hint for x-axis
                width=self.width - 40 # Set the width
            )
            chapter_container.add_widget(chapter_label) # Add the chapter label to the container
            chapter_container.height += chapter_label.height + 10  # Add spacing

            lesson_box = BoxLayout( # Create a BoxLayout for the lessons
                orientation='vertical', # Set the orientation to vertical
                size_hint_y=None, # Set the size hint for y-axis 
                height=0,  # Will be updated based on content
                spacing=10, # Set the spacing between widgets
                padding=[20, 10], # Set the padding
            )

            for lesson_num in range(1, len(chapter_data['lessons']) + 1): # Iterate over the lessons
                lesson_data = chapter_data['lessons'].get(lesson_num) # Get the lesson data
                if lesson_data: # Check if the lesson data exists
                    is_unlocked = True # Assume the lesson is unlocked
                    if chapter_num == unlocked_chapters and lesson_num > unlocked_lessons: # Check if the lesson is locked
                        is_unlocked = False # Set the lesson as locked
                    elif chapter_num > unlocked_chapters: # Check if the chapter is locked
                        is_unlocked = False # Set the lesson as locked

                    lesson_button = Button( # Create a Button for the lesson
                        text=f"Lesson {lesson_num}", # Set the text
                        size_hint_y=None, # Set the size hint for y-axis
                        height=40, # Set the height
                        on_press=lambda btn, ch=chapter_num, ln=lesson_num: self.load_lesson_screen(ch, ln), # Set the on_press event
                        disabled=not is_unlocked,   # Disable if locked
                        background_color=(0.5, 0.5, 0.5, 1) if not is_unlocked else (1, 1, 1, 1), # Set the background color
                    )
                    lesson_box.add_widget(lesson_button) # Add the lesson button to the lesson box
                    lesson_box.height += lesson_button.height + 10  # Add spacing

            chapter_container.add_widget(lesson_box) # Add the lesson box to the chapter container
            chapter_container.height += lesson_box.height + 10  # Add spacing

            roadmap_layout.add_widget(chapter_container) # Add the chapter container to the roadmap layout

        # After adding chapters, check if cumulative review should be added
        # Assuming total chapters are 20 and each chapter has 8 lessons including the review
        if unlocked_chapters == 20 and unlocked_lessons >= 8: # User has completed all chapters and chapter reviews
            cumulative_review_button = Button( # Create a Button for the cumulative review
                text="Cumulative Review", # Set the text
                size_hint_y=None, # Set the size hint for y-axis
                height=40, # Set the height
                on_press=lambda btn: self.load_cumulative_review(), # Set the on_press event
                background_color=(1, 1, 1, 1), # Set the background color
            )
            roadmap_layout.add_widget(cumulative_review_button) # Add the cumulative review button to the roadmap layout
            roadmap_layout.height += cumulative_review_button.height + 10 # Add spacing

        roadmap_layout.height = sum([child.height for child in roadmap_layout.children]) + 20 * len(roadmap_layout.children) # Update the height of the roadmap layout to fit the content


    # Function to load the lesson screen
    def load_lesson_screen(self, chapter, lesson): # Define the load_lesson_screen function
        if lesson == 8: # Check if the lesson is the review lesson
            # Navigate to the chapter review screen and generate the review
            chapter_review_screen = self.manager.get_screen('chapter_review') # Get the ChapterReviewScreen instance
            chapter_review_screen.start_chapter_review(self.user_id, chapter) # Start the chapter review
            self.manager.current = 'chapter_review' # Navigate to the chapter review screen
        else: # Handle regular lessons
            # Navigate to the lesson screen and load the lesson
            lesson_screen = self.manager.get_screen('lesson') # Get the LessonScreen instance
            lesson_screen.load_lesson(self.user_id, chapter, lesson) # Load the lesson
            self.manager.current = 'lesson' # Navigate to the lesson screen
    
    # Function to load the cumulative review screen
    def load_cumulative_review(self): # Define the load_cumulative_review function
        cumulative_review_screen = self.manager.get_screen('cumulative_review') # Get the CumulativeReviewScreen instance
        cumulative_review_screen.start_cumulative_review(self.user_id) # Start the cumulative review
        self.manager.current = 'cumulative_review' # Navigate to the cumulative review screen

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

# class to handle the questions screen
class ProfileScreen(Screen): # Define the ProfileScreen class
    user_id = None  # Initialize user_id attribute
    username = StringProperty('') # Initialize username property
    email = StringProperty('') # Initialize email property
    profile_pic_path = StringProperty('Assets/default_profile_pic.webp') # Initialize profile_pic_path property
    is_editing_username = BooleanProperty(False) # Initialize is_editing_username property
    is_editing_email = BooleanProperty(False) # Initialize is_editing_email property
    certificate_path = None # Initialize certificate_path attribute

    def __init__(self, **kwargs): # Define the constructor
        super().__init__(**kwargs) # Call the superclass constructor
        self.conn = None  # Initialize the conn attribute to ensure it exists

    def on_enter(self): # Define the on_enter function
        main_screen = self.manager.get_screen('main') # Get the MainScreen instance
        
        if not main_screen.conn: # Check if the connection is not established
            main_screen.initialize_database_connection() # Initialize the database connection

        self.conn = main_screen.conn # Inherit the connection
        self.user_id = main_screen.user_id # Inherit the user_id

        self.ensure_database_connection()  # Ensure the database connection is active
        self.load_user_data() # Load user data from the database
        self.check_certificate() # Check if a certificate exists
    
    # On leave function to reset editing states and clear data
    def on_leave(self): # Define the on_leave function
        self.is_editing_username = False # Reset the editing state
        self.is_editing_email = False # Reset the editing state
        self.username = "" # Reset the username
        self.email = "" # Reset the email
        self.certificate_path = None # Reset the certificate path

    # Function to ensure the database connection
    def ensure_database_connection(self): # Define the ensure_database_connection function
        main_screen = self.manager.get_screen('main') # Get the MainScreen instance
        if main_screen.conn is None: # Check if the connection is not established
            main_screen.initialize_database_connection() # Initialize the database connection
        self.conn = main_screen.conn # Inherit the connection
        try: # Try to check the database connection
            cursor = self.conn.cursor() # Create a cursor object
            cursor.execute('SELECT 1') # Execute a test query
        except sqlite3.Error as e:  # Handle database errors
            main_screen.initialize_database_connection() # Reinitialize the database connection
            self.conn = main_screen.conn # Inherit the connection

    # Function to load user data from the database
    def load_user_data(self):
        # Fetch user data from the database
        try: # Try to load user data from the database
            if self.conn: # Check if the connection is established
                cursor = self.conn.cursor() # Create a cursor object
                cursor.execute('SELECT name, email FROM users WHERE id = ?', (self.user_id,)) # Execute an SQL query
                result = cursor.fetchone() # Fetch the first row from the result set
                if result: # Check if the result is found
                    self.username = result[0] # Set the username
                    self.email = result[1] # Set the email
                    print(f"Loaded user data: {result}")  # Log loaded user data
                else: # Handle case where user is not found
                    print("User not found.") # Debugging line
        except sqlite3.Error as e: # Handle database errors
            print(f"Database error: {e}") # Handle database errors

        # Load profile picture if it exists
        profile_pic_file = f'profile_pics/user_{self.user_id}.png' # Set the profile picture path
        if os.path.exists(profile_pic_file): # Check if the file exists
            self.profile_pic_path = profile_pic_file # Set the profile picture path
        else: # Handle case where the file does not exist
            self.profile_pic_path = 'Assets/default_profile_pic.webp' # Set the default profile picture path

    # Function to toggle the username editing state
    def toggle_username_edit(self): # Define the toggle_username_edit function
        self.is_editing_username = not self.is_editing_username # Toggle the editing state

    # Function to save the updated username
    def save_username(self): # Define the save_username function
        new_username = self.ids.username_input.text  # This will now correctly reference the TextInput
        print(f"Updating username to: {new_username}, for user_id: {self.user_id}")  # Log the new username

        if not new_username.strip(): # Check if the username is empty
            self.show_message("Username cannot be empty.") # Show a message
            return # Exit the function

        try: # Try to update the username in the database
            if self.conn: # Check if the connection is established
                cursor = self.conn.cursor() # Create a cursor object
                cursor.execute('UPDATE users SET name = ? WHERE id = ?', (new_username, self.user_id)) # Execute an SQL query
                self.conn.commit() # Commit the transaction

                # Verify if the update was successful
                cursor.execute('SELECT name FROM users WHERE id = ?', (self.user_id,)) # Execute an SQL query
                updated_username = cursor.fetchone() # Fetch the first row from the result set
                if updated_username and updated_username[0] == new_username: # Check if the username is updated
                    self.username = new_username  # Update the property after a successful save
                    self.show_message("Username updated successfully.") # Show a message
                else: # Handle case where the username is not updated
                    self.show_message("Failed to update username.") # Show a message

            self.is_editing_username = False # Reset the editing state
        except sqlite3.Error as e: # Handle database errors 
            self.show_message("Database error occurred while updating username.") # Show a message

    # Function to toggle the email editing state
    def toggle_email_edit(self): # Define the toggle_email_edit function
        self.is_editing_email = not self.is_editing_email # Toggle the editing state

    # Function to save the updated email
    def save_email(self, password): # Define the save_email function
        new_email = self.ids.email_input.text # This will reference the TextInput
        print(f"Updating email to: {new_email}, for user_id: {self.user_id}") # Log the new email

        if not new_email.strip():  # Check if the email is empty
            self.show_message("Email cannot be empty.") # Show a message
            return # Exit the function

        if self.verify_password(password):  # Verify the password
            try:  # Try to update the email in the database
                if self.conn: # Check if the connection is established
                    cursor = self.conn.cursor() # Create a cursor object
                    cursor.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, self.user_id)) # Execute an SQL query
                    self.conn.commit() # Commit the transaction

                    # Check if the update was successful
                    cursor.execute('SELECT email FROM users WHERE id = ?', (self.user_id,)) # Execute an SQL query
                    updated_email = cursor.fetchone() # Fetch the first row from the result set
                    if updated_email and updated_email[0] == new_email: # Check if the email is updated
                        self.email = new_email  # Update the property after successful save
                        self.show_message("Email updated successfully.") # Show a message
                    else: # Handle case where the email is not updated
                        self.show_message("Failed to update email.") # Show a message

                self.is_editing_email = False # Reset the editing state
            except sqlite3.Error as e: # Handle database errors
                self.show_message("Database error occurred while updating email.") # Show a message
        else: # Handle case where the password verification fails
            self.show_message("Incorrect password. Email not updated.") # Show a message

    # Function to verify the password
    def verify_password(self, password): # Define the verify_password function
        try: # Try to verify the password
            if self.conn: # Check if the connection is established
                cursor = self.conn.cursor() # Create a cursor object
                cursor.execute('SELECT password FROM users WHERE id = ?', (self.user_id,)) # Execute an SQL query
                result = cursor.fetchone() # Fetch the first row from the result set
                if result and bcrypt.checkpw(password.encode(), result[0]): # Check if the password matches
                    return True # Return True if the password matches
        except sqlite3.Error as e: # Handle database errors
            print(f"Database error: {e}") # Print an error message
        return False # Return False if the password does not match

    # Function to change the password
    def change_password(self, old_password, new_password): # Define the change_password function
        if self.verify_password(old_password): # Verify the old password
            hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()) # Hash the new password
            try: # Try to update the password in the database
                if self.conn: # Check if the connection is established
                    cursor = self.conn.cursor() # Create a cursor object
                    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, self.user_id)) # Execute an SQL query
                    self.conn.commit() # Commit the transaction
                self.show_message("Password updated successfully.") # Show a message
            except sqlite3.Error as e: # Handle database errors
                print(f"Database error: {e}") # Print an error message
        else: # Handle case where the password verification fails
            self.show_message("Incorrect old password. Password not updated.") # Show a message

    # Function to check if a certificate exists
    def show_message(self, message): # Define the show_message function
        popup = Popup(title='Notification', content=Label(text=message), size_hint=(0.6, 0.4)) # Create a popup
        popup.open() # Open the popup

    # Function to open the profile picture popup
    def open_profile_pic_popup(self): # Define the open_profile_pic_popup function
        content = BoxLayout(orientation='vertical') # Create a BoxLayout
        filechooser = FileChooserIconView() # Create a FileChooserIconView
        content.add_widget(filechooser) # Add the filechooser to the content

        # Function to load the selected image
        def load_image(instance): # Define the load_image function
            selected = filechooser.selection # Get the selected file
            if selected: # Check if a file is selected
                self.update_profile_picture(selected[0]) # Update the profile picture
                popup.dismiss() # Dismiss the popup

        select_button = Button(text='Select', size_hint_y=None, height=40) # Create a Button
        select_button.bind(on_release=load_image) # Bind the load_image function to the button
        content.add_widget(select_button) # Add the button to the content

        popup = Popup(title='Select Profile Picture', content=content, size_hint=(0.9, 0.9)) # Create a popup
        popup.open() # Open the popup

    # Function to update the profile picture
    def update_profile_picture(self, image_path): # Define the update_profile_picture function
        try: # Try to update the profile picture
            img = PILImage.open(image_path) # Open the image
            img = img.resize((200, 200))  # Adjust size as needed
            profile_pic_dir = 'profile_pics' # Set the profile picture directory
            if not os.path.exists(profile_pic_dir): # Check if the directory does not exist
                os.makedirs(profile_pic_dir) # Create the directory
            save_path = f'{profile_pic_dir}/user_{self.user_id}.png' # Set the save path
            img.save(save_path) # Save the image
            self.profile_pic_path = save_path # Update the profile picture path
        except Exception as e: # Handle errors
            print(f"Error updating profile picture: {e}") # Print an error message
            self.show_message("Failed to update profile picture.") # Show a message

# class to handle the mistakes screen
class MistakesScreen(Screen): # Define the MistakesScreen class
    def __init__(self, **kwargs): # Define the constructor
        super(MistakesScreen, self).__init__(**kwargs) # Call the superclass constructor
        self.current_view_state = 'chapters'  # Tracks whether viewing 'chapters' or 'lessons'

    # Function to handle the back button press
    def on_pre_enter(self): # Define the on_pre_enter function
        app = App.get_running_app() # Get the running app
        if hasattr(app, 'user_id') and app.user_id is not None: # Check if the user_id is set
            self.user_id = app.user_id # Set the user_id
        else: # Handle case where user_id is not set
            self.manager.current = 'login' # Navigate to the login screen
            return # Exit the function

        self.ids.mistakes_container.clear_widgets() # Clear the mistakes container

        self.load_completed_chapters_and_lessons() # Load the completed chapters and lessons

    # Function to handle the back button press
    def on_back_pressed(self):  # Define the on_back_pressed function
        if self.current_view_state == 'details': # Check if viewing details
            self.current_view_state = 'chapters' # Switch to chapters view
            self.ids.mistakes_container.clear_widgets() # Clear the mistakes container
            self.load_completed_chapters_and_lessons() # Reload the chapters and lessons
        else: # Handle case where not viewing details
            self.manager.current = 'main' # Navigate to the main screen

    # Function to load the completed chapters and lessons
    def load_completed_chapters_and_lessons(self): # Define the load_completed_chapters_and_lessons function
        try: # Try to load the completed chapters and lessons
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    SELECT DISTINCT chapter, lesson
                    FROM mistakes
                    WHERE user_id = ?
                    ORDER BY chapter, lesson
                    ''',
                    (self.user_id,)
                )
                lessons = cursor.fetchall() # Fetch all rows from the result set
                chapters = {} # Initialize an empty dictionary for chapters
                for chapter, lesson in lessons: # Iterate over the lessons
                    if chapter not in chapters: # Check if the chapter is not in the dictionary
                        chapters[chapter] = [] # Initialize an empty list for the chapter
                    chapters[chapter].append(lesson) # Add the lesson to the chapter

                if not chapters: # Check if no chapters are found
                    no_mistakes_label = Label( # Create a Label
                        text="No lessons with mistakes found.", # Set the text
                        size_hint_y=None, # Set the size hint for y-axis
                        height=30 # Set the height
                    )
                    self.ids.mistakes_container.add_widget(no_mistakes_label) # Add the label to the container
                    return # Exit the function

                for chapter in sorted(chapters.keys()): # Iterate over the chapters
                    self.add_chapter(chapter, chapters[chapter]) # Add the chapter to the UI

                self.current_view_state = 'chapters' # Set the current view state to chapters

        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to load lessons with mistakes: {e}") # Print an error message

    # Function to add a chapter section to the UI
    def add_chapter(self, chapter, lessons): # Define the add_chapter function
        chapter_layout = BoxLayout(orientation='vertical', size_hint_y=None) # Create a BoxLayout
        chapter_layout.bind(minimum_height=chapter_layout.setter('height')) # Bind the minimum height

        # Chapter button
        chapter_button = Button( # Create a Button
            text=f"Chapter {chapter}", # Set the text
            size_hint_y=None, # Set the size hint for y-axis 
            height=40 # Set the height
        )
        chapter_button.bind(on_release=self.toggle_chapter) # Bind the toggle_chapter function
        chapter_button.lessons = lessons # Store lessons as attribute

        chapter_layout.add_widget(chapter_button) # Add the button to the layout

        # Lessons layout (initially collapsed)
        lessons_layout = BoxLayout(orientation='vertical', size_hint_y=None) # Create a BoxLayout
        lessons_layout.bind(minimum_height=lessons_layout.setter('height')) # Bind the minimum height
        lessons_layout.height = 0  # Start collapsed
        lessons_layout.visible = False  # Custom attribute
        chapter_layout.add_widget(lessons_layout) # Add the layout to the chapter layout

        chapter_button.lessons_layout = lessons_layout # Store lessons layout as attribute
        self.ids.mistakes_container.add_widget(chapter_layout) # Add the layout to the container

    # Function to toggle the chapter view
    def toggle_chapter(self, instance): # Define the toggle_chapter function
        lessons_layout = instance.lessons_layout # Get the lessons layout
        
        if lessons_layout.visible: # Check if the lessons layout is visible
            # Collapse lessons, but keep chapter button visible
            lessons_layout.clear_widgets()  # Clear lesson buttons
            lessons_layout.height = 0 # Collapse layout
            lessons_layout.visible = False # Update visibility
        else: # Handle case where the lessons layout is not visible
            if not lessons_layout.children: # Check if the lessons layout is empty
                self.add_lessons_to_layout(instance.lessons, lessons_layout, instance.text)  # Add lessons to layout
            lessons_layout.height = lessons_layout.minimum_height   # Expand layout
            lessons_layout.visible = True # Update visibility

    # Function to add lessons to the layout
    def add_lessons_to_layout(self, lessons, layout, chapter_text): # Define the add_lessons_to_layout function
        chapter_number = int(chapter_text.split()[1]) # Extract the chapter number
        for lesson in sorted(lessons): # Iterate over the lessons
            total_mistakes = self.get_total_mistakes(self.user_id, chapter_number, lesson) # Get the total mistakes

            lesson_button = Button( # Create a Button
                text=f"Lesson {lesson} - Mistakes: {total_mistakes}", # Set the text
                size_hint_y=None,  # Set the size hint for y-axis
                height=40   # Set the height
            )
            lesson_button.bind(on_release=self.show_mistakes_for_lesson) # Bind the show_mistakes_for_lesson function
            lesson_button.chapter = chapter_number # Store the chapter number
            lesson_button.lesson = lesson # Store the lesson number
            layout.add_widget(lesson_button) # Add the button to the layout
            self.current_view_state = 'lessons' # Set the current view state to lessons

    # Function to get the total mistakes for a lesson
    def get_total_mistakes(self, user_id, chapter, lesson): # Define the get_total_mistakes function
        try: # Try to get the total mistakes
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    '''
                    SELECT COUNT(*)
                    FROM mistakes
                    WHERE user_id = ? AND chapter = ? AND lesson = ?
                    ''',
                    (user_id, chapter, lesson)
                )
                total_mistakes = cursor.fetchone()[0] # Fetch the first row from the result set
                return total_mistakes # Return the total mistakes
        except sqlite3.Error as e: # Handle database errors
            return 0    # Return 0 if an error occurs

    # Function to show mistakes for a lesson
    def show_mistakes_for_lesson(self, instance): # Define the show_mistakes_for_lesson function
        self.ids.mistakes_container.clear_widgets() # Clear the mistakes container

        detailed_layout = BoxLayout(orientation='vertical', padding=[10, 15], size_hint=(1, None))  # Create a BoxLayout
        detailed_layout.bind(minimum_height=detailed_layout.setter('height')) # Bind the minimum height
        header_label = Label( # Create a Label for the header
            text=f"[b]Mistakes for Lesson {instance.lesson}[/b]", # Set the text
            size_hint_y=None, # Set the size hint for y-axis
            height=40, # Set the height
            markup=True, # Enable markup
            halign='center', # Set the horizontal alignment
            valign='middle' # Set the vertical alignment
        )
        header_label.text_size = (self.ids.mistakes_container.width * 0.9, None) # Set the text size
        detailed_layout.add_widget(header_label) # Add the header label to the layout

        mistakes = self.get_mistakes_for_lesson(self.user_id, instance.chapter, instance.lesson) # Get the mistakes
 
        for mistake in mistakes: # Iterate over the mistakes
            # Create a box for each mistake
            mistake_box = BoxLayout(orientation='vertical', padding=[5, 10], size_hint=(1, None)) # Create a BoxLayout
            mistake_box.bind(minimum_height=mistake_box.setter('height')) # Bind the minimum height

            # Display mistake details with proper wrapping and dynamic height
            def create_wrapped_label(text): # Define the create_wrapped_label function
                label = Label( # Create a Label
                    text=text, # Set the text
                    size_hint_y=None, # Set the size hint for y-axis
                    markup=True, # Enable markup
                    text_size=(self.ids.mistakes_container.width * 0.9, None), # Set the text size
                    halign='left', # Set the horizontal alignment 
                    valign='top' # Set the vertical alignment
                )
                label.bind( # Bind the text size
                    texture_size=lambda instance, value: setattr(instance, 'height', instance.texture_size[1]) # Set the height
                )
                return label # Return the label

            question_label = create_wrapped_label(f"[b]Question:[/b] {mistake['question']}") # Create a wrapped label
            mistake_box.add_widget(question_label) # Add the question label to the mistake box
 
            correct_answer_label = create_wrapped_label(f"[b]Correct Answer:[/b] {mistake['correct_answer']}") # Create a wrapped label
            mistake_box.add_widget(correct_answer_label) # Add the correct answer label to the mistake box

            user_answer_label = create_wrapped_label(f"[b]Your Answer:[/b] {mistake['user_answer']}") # Create a wrapped label
            mistake_box.add_widget(user_answer_label) # Add the user answer label to the mistake box

            # Optional feedback
            if mistake['feedback']: # Check if feedback exists
                feedback_label = create_wrapped_label(f"[b]Feedback:[/b] {mistake['feedback']}") # Create a wrapped label
                mistake_box.add_widget(feedback_label) # Add the feedback label to the mistake box

            detailed_layout.add_widget(mistake_box) # Add the mistake box to the layout

        self.ids.mistakes_container.add_widget(detailed_layout) # Add the detailed layout to the container

        self.current_view_state = 'details' # Set the current view state to details

    # Function to get mistakes for a lesson
    def get_mistakes_for_lesson(self, user_id, chapter, lesson): # Define the get_mistakes_for_lesson function
        try: # Try to get the mistakes for a lesson
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor()  # Create a cursor object
                cursor.execute(  # Execute an SQL query
                    '''
                    SELECT question, user_answer, correct_answer, feedback
                    FROM mistakes
                    WHERE user_id = ? AND chapter = ? AND lesson = ?
                    ORDER BY id
                    ''',
                    (user_id, chapter, lesson)
                )
                mistakes = cursor.fetchall() # Fetch all rows from the result set
                # Convert to list of dictionaries
                mistakes_list = [] # Initialize an empty list for mistakes
                for row in mistakes: # Iterate over the mistakes
                    mistakes_dict = { # Create a dictionary for the mistake
                        'question': row[0], # Set the question
                        'user_answer': row[1], # Set the user answer
                        'correct_answer': row[2], # Set the correct answer
                        'feedback': row[3] if len(row) > 3 else None  # Handle missing feedback
                    }
                    mistakes_list.append(mistakes_dict) # Add the mistake to the list
                return mistakes_list # Return the list of mistakes
        except sqlite3.Error as e: # Handle database errors
            print(f"Failed to get mistakes for lesson: {e}") # Print an error message
            return [] # Return an empty list if an error occurs
    # Function to handle the back button press
    def navigate_back(self): # Define the navigate_back function

        if self.current_view_state == 'details': # Check if viewing details
            # If viewing details, go back to the chapters (including any expanded lessons)
            self.current_view_state = 'chapters' # Set the current view state to chapters
            self.ids.mistakes_container.clear_widgets() # Clear the mistakes container
            self.load_completed_chapters_and_lessons() # Load the completed chapters and lessons
        else:
            self.manager.current = 'main' # Navigate to the main screen

    # Function to handle the back button press
    def navigate_home(self): # Define the navigate_home function
        self.manager.current = 'main'   # Navigate to the main screen

# class to handle the chapter review result screen
class ChapterReviewScreen(Screen): # Define the ChapterReviewScreen class
    def __init__(self, **kwargs): # Define the constructor
        super().__init__(**kwargs) # Call the superclass constructor
        self.user_id = None # Initialize the user_id attribute
        self.chapter = None # Initialize the chapter attribute

    # Function to start the chapter review
    def start_chapter_review(self, user_id, chapter): # Define the start_chapter_review function
        self.user_id = user_id # Set the user_id
        self.chapter = chapter # Set the chapter
        self.ids.loading_label.text = f"Generating Chapter {chapter} Review..." # Update the loading label
        Clock.schedule_once(self.generate_review_questions, 0.5)  # Slight delay for UI update

    # Function to generate review questions
    def generate_review_questions(self, dt): # Define the generate_review_questions function
        progress = UserProgress(self.user_id)   # Create a UserProgress instance
        questions = generate_review_questions(progress, self.chapter) # Generate review questions
        num_questions = len(questions) # Get the number of questions
        # Store questions in QuestionScreen with a flag indicating review mode
        question_screen = self.manager.get_screen('questions') # Get the QuestionScreen instance
        question_screen.set_questions(questions, self.chapter, lesson=8, is_review=True) # Set the questions
        self.manager.current = 'questions' # Navigate to the questions screen

# class to handle the chapter review result screen
class CumulativeReviewScreen(Screen): # Define the CumulativeReviewScreen class
    # Define the constructor
    def __init__(self, **kwargs): # Define the constructor
        super().__init__(**kwargs) # Call the superclass constructor
        self.user_id = None # Initialize the user_id attribute

    # Function to start the cumulative review
    def start_cumulative_review(self, user_id): # Define the start_cumulative_review function
        self.user_id = user_id # Set the user_id
        self.ids.loading_label.text = "Generating Cumulative Review..." # Update the loading label
        Clock.schedule_once(self.generate_cumulative_review_questions, 0.5)  # Slight delay for UI update

    # Function to generate cumulative review questions
    def generate_cumulative_review_questions(self, dt): # Define the generate_cumulative_review_questions function
        progress = UserProgress(self.user_id) # Create a UserProgress instance
        questions = generate_cumulative_review(progress)  # Use cumulative review logic
        num_questions = len(questions) # Get the number of questions
        # Update the loading label to display the number of questions
        self.ids.loading_label.text = f"Generated {num_questions} questions for the Cumulative Review." # Update the loading label
        Clock.schedule_once(lambda dt: self.go_to_questions_screen(questions), 1.0) # Delayed transition

    # Function to navigate to the questions screen
    def go_to_questions_screen(self, questions): # Define the go_to_questions_screen function
        # Store questions in QuestionScreen with a flag indicating cumulative review mode
        question_screen = self.manager.get_screen('questions') # Get the QuestionScreen instance
        question_screen.set_questions(questions, chapter=None, lesson=21, is_cumulative_review=True) # Set the questions
        self.manager.current = 'questions' # Navigate to the questions screen

# class to handle the chapter review result screen
class QuestionScreen(Screen): # Define the QuestionScreen class
    
    # Define the constructor
    def __init__(self, **kwargs): # Define the constructor
        super().__init__(**kwargs) # Call the superclass constructor
        self.questions = []  # To store the questions for the screen
        self.current_question_index = 0  # To track the current question index
        self.chapter = None  # To store the current chapter number
        self.lesson = None  # To store the current lesson number
        self.selected_answer = None  # To track selected answers for multiple choice
        self.awaiting_next_submission = False  # To prevent multiple submissions
        self.feedback_label = None # To store the feedback label
    
    # Function to set the questions
    def set_questions(self, questions, chapter, lesson, is_review=False, is_cumulative_review=False): # Define the set_questions function
        self.questions = questions # Store the questions
        self.chapter = chapter # Store the chapter number
        self.lesson = lesson # Store the lesson number
        self.is_review = is_review  # Flag to indicate if it's a chapter review
        self.is_cumulative_review = is_cumulative_review  # Flag for cumulative review
        self.current_question_index = 0 # Reset the current question index
        self.correct_answers = 0  # Initialize correct answers counter
        self.display_next_question() # Display the first question


    # Function to display the next question
    def display_next_question(self):  # Define the display_next_question function
        if not self.questions or self.current_question_index >= len(self.questions):  # Check if there are no questions
            self.ids.question_content.text = "No questions available."  # Update the question content

            # Handle the end of questions
            user_progress = UserProgress(self.manager.get_screen('main').user_id)  # Get user progress
            main_screen = self.manager.get_screen('main')  # Get the MainScreen instance

            # Fetch user_name from the database to ensure it's always updated
            try:  # Try to fetch the user name from the database
                with sqlite3.connect('progress.db') as conn:  # Connect to the database
                    cursor = conn.cursor()  # Create a cursor object
                    cursor.execute('SELECT name FROM users WHERE id = ?', (main_screen.user_id,))  # Execute an SQL query
                    result = cursor.fetchone()  # Fetch the first row from the result set
                    if result:  # Check if the result is found
                        user_name = result[0]  # Set the user name
                    else:  # Handle case where the user name is not found
                        user_name = "User"  # Set the default user name
            except sqlite3.Error as e:  # Handle database errors
                print(f"Database error while fetching user name: {e}")  # Debugging statement
                user_name = "User"  # Set the default user name

            if self.is_cumulative_review:  # For cumulative review
                # Transition to CumulativeReviewResultScreen
                result_screen = self.manager.get_screen('cumulative_review_result')  # Reference to the CumulativeReviewResultScreen
                result_screen.display_results(  # Display the results
                    total_questions=len(self.questions),  # Pass the total number of questions
                    correct_answers=self.correct_answers,  # Pass the correct answers
                    user_id=main_screen.user_id  # Pass the user ID
                )
                self.manager.current = 'cumulative_review_result'  # Navigate to the cumulative review result screen
            elif self.is_review:  # For chapter review
                # Transition to ChapterReviewResultScreen
                result_screen = self.manager.get_screen('chapter_review_result')  # Reference to the ChapterReviewResultScreen
                result_screen.display_results(  # Display the results
                    total_questions=len(self.questions),  # Pass the total number of questions
                    correct_answers=self.correct_answers,  # Pass the correct answers
                    chapter=self.chapter  # Pass the chapter number
                )
                self.manager.current = 'chapter_review_result'  # Navigate to the chapter review result screen
            else:  # For regular questions
                # Unlock the next lesson and save progress
                if self.lesson is not None and self.chapter is not None:  # Check if the lesson and chapter are set
                    total_lessons_in_chapter = len(chapters[self.chapter]['lessons'])  # Get the total lessons in the chapter
                    if self.lesson < total_lessons_in_chapter:  # Check if the lesson is not the last one
                        user_progress.lesson += 1  # Unlock the next lesson
                    else:  # Handle case where the lesson is the last one
                        pass  # No need to unlock the next lesson
                    user_progress.save_progress()  # Save the user progress 
                # Transition back to the main screen
                self.manager.current = 'main'  # Navigate to the main screen
                self.manager.get_screen('main').on_enter()  # Refresh the main screen if necessary
            return  # Exit the function

        # Proceed to display the next question
        self.awaiting_next_submission = False  # Reset the flag
        question = self.questions[self.current_question_index]  # Get the current question

        total_questions = len(self.questions)  # Get the total number of questions
        current_question_number = self.current_question_index + 1  # Get the current question number
        if hasattr(self.ids, 'progress_label'):  # Check if the progress label exists
            self.ids.progress_label.text = f"Question {current_question_number} of {total_questions}"  # Update the progress label

        self.ids.feedback_label.text = ""  # Clear the feedback label

        # Display the question text
        question_text = question.get('question', 'No question text available')  # Get the question text
        lines = question_text.split('\n')  # Split the question text into lines
        filtered_lines = [line for line in lines if not line.startswith(  # Filter out metadata
            ('MULTIPLE CHOICE QUESTION', 'Chapter:', 'Lesson:', 'Options:', 'Question:', 'Sample Solution:'))]  # Filter out metadata
        cleaned_question_text = "\n".join(filtered_lines).strip()  # Clean up the question text

        if question.get('type') == 'multiple_choice':  # For multiple choice questions
            options = question.get('options', {})  # Get the options
            formatted_options = "\n".join([f"{key}) {value}" for key, value in options.items()])  # Format the options
            cleaned_question_text = f"{cleaned_question_text}\n\n{formatted_options}"  # Append the options

        self.ids.question_content.text = cleaned_question_text  # Display the question text
        self.ids.answer_area.clear_widgets()  # Clear existing answer area widgets

        # Handle different question types
        if question.get('type') == 'multiple_choice':  # For multiple choice questions
            self.selected_answer = None  # Reset selected answer

            # Create a horizontal BoxLayout to hold the option buttons (A, B, C, D)
            options_layout = BoxLayout(
                orientation='horizontal',  # Set the orientation
                size_hint_y=None,  # Set the size hint for y-axis
                height=40,  # Slightly smaller height (was 50)
                spacing=5  # Reduced spacing for a tighter fit
            )

            for key in sorted(question.get('options', {}).keys()):  # Ensure options are in order
                btn = Button(
                    text=key,  # Display only the option letter
                    size_hint=(None, 1),  # Set the size hint
                    width=60  # Adjust width to be slightly smaller (was 80)
                )
                btn.bind(on_press=self.on_option_selected)  # Bind the button press event
                options_layout.add_widget(btn)  # Add the button to the options layout

            self.ids.answer_area.add_widget(options_layout)  # Add the options layout to the answer area

        elif question.get('type') == 'true_false':  # For true/false questions
            self.selected_answer = None  # Reset selected answer

            # Create a horizontal BoxLayout to hold the True and False buttons
            tf_layout = BoxLayout(
                orientation='horizontal',  # Set the orientation
                size_hint_y=None,  # Set the size hint for y-axis
                height=40,  # Slightly smaller height (was 50)
                spacing=10  # Adjusted spacing for better alignment
            )

            for option in ["True", "False"]:  # Add True and False buttons
                btn = Button(
                    text=option,  # Set the text
                    size_hint=(None, 1),  # Set the size hint
                    width=100  # Reduced width for a tighter fit (was 150)
                )
                btn.bind(on_press=self.on_option_selected)  # Bind the button press event
                tf_layout.add_widget(btn)  # Add the button to the true/false layout

            self.ids.answer_area.add_widget(tf_layout)  # Add the true/false layout to the answer area

        elif question.get('type') == 'write_code':  # For code writing questions
            code_input = CustomCodeInput(   # Create a CustomCodeInput widget
                hint_text="Enter your code here",   # Set the hint text
                multiline=True, # Allow multiple lines
                size_hint=(1, None), # Set the size hint
                height=80 # Reduced height for a tighter fit (was 100)
            )
            code_input.bind(minimum_height=code_input.setter('height')) # Bind the minimum height 
            scroll_view = ScrollView(size_hint=(1, None), height=80) # Adjusted height for a tighter fit
            scroll_view.add_widget(code_input) # Add the code input to the scroll view
            self.ids.answer_area.add_widget(scroll_view) # Add the code input to the answer area
            self.ids.user_input = code_input # Store the code input for later access

        else:  # For fill in the blank and scenarios
            text_input = TextInput(  # Create a TextInput for fill in the blank and scenarios
                hint_text="Enter your answer",  # Set the hint text
                multiline=False, # Single line input
                size_hint=(1, None), # Set the size hint
                height=40 # Reduced height for a tighter fit (was 50)
            )
            self.ids.answer_area.add_widget(text_input) # Add the text input to the answer area
            self.ids.user_input = text_input # Store the text input for later access

        # Conditionally display "Sample Solution" and "Code Comparison" buttons 
        if question.get('type') == 'write_code': # For code writing questions
            self.ids.sample_solution_label.opacity = 1 # Show the sample solution button
            self.ids.sample_solution_label.size_hint_y = None # Restore the size hint
            self.ids.code_comparison_label.opacity = 0 # Hide the code comparison button
            self.ids.code_comparison_label.size_hint_y = 0 # Hide the code comparison button
        else: # Hide the sample solution and code comparison buttons
            self.ids.sample_solution_label.opacity = 0 # Hide the sample solution button
            self.ids.sample_solution_label.size_hint_y = 0 # Hide the sample solution button
            self.ids.code_comparison_label.opacity = 0 # Hide the code comparison button
            self.ids.code_comparison_label.size_hint_y = 0 # Hide the code comparison button


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
        correct = False  # Initialize correct at the start
        print("submit_answer called") # Debugging output for function call

        if self.awaiting_next_submission: # Check if awaiting next submission
            # Move to the next question after showing feedback
            self.current_question_index += 1 # Move to the next question
            self.display_next_question() # Display the next question
            return # Exit the function

        if self.questions: # Check if there are questions available
            question = self.questions[self.current_question_index] # Get the current question
            question_type = question.get('type', '')  # Ensure question type is retrieved
            print(f"Submitting answer for question type: {question_type}") # Debugging output for question type

            user_answer = "" # Initialize user answer
            feedback = "" # Initialize feedback

            if question_type in ['multiple_choice', 'true_false']: # Check if the question type is multiple choice or true/false
                user_answer = self.selected_answer # Get the selected answer
                if user_answer: # Check if an answer is selected
                    correct = self.validate_answer(question, user_answer) # Validate the answer
                else: # Handle case where no answer is selected
                    feedback = "Please select an option." # Provide feedback to select an option
            elif question_type == 'fill_in_the_blank': # Check if the question type is fill in the blank
                user_answer = self.ids.user_input.text if hasattr(self.ids, 'user_input') else "" # Get the user input
                correct = self.validate_answer(question, user_answer) # Validate the answer
                user_code = self.collect_code_input() # Collect the user code input
                correct, feedback = self.validate_code_answer(question, user_code) # Validate the code answer
                self.display_feedback(correct, feedback, question.get('correct_answer', ''), user_code=user_code, question_type=question_type) # Display the feedback
            elif question_type == 'scenario': # Check if the question type is scenario
                user_response = self.collect_scenario_response() # Collect the user response
                correct, feedback = self.validate_scenario_answer(question, user_response) # Validate the scenario answer
            else: # Handle unrecognized question types
                feedback = "Unrecognized question type." # Provide feedback for unrecognized question types

            self.display_feedback(correct, feedback, question.get('correct_answer', ''), user_code=user_answer, question_type=question_type) # Display the feedback

            if correct: # Check if the answer is correct
                self.correct_answers += 1  # Increment correct answers if correct

            self.awaiting_next_submission = True # Set the flag to await next submission
        else: # Handle case where no questions are available
            self.display_feedback(False, "No questions available.", "", question_type="unknown")  # Display feedback for no questions

    # Function to collect code input***REMOVE BEFORE SUBMISSION***
    def bypass_validation(self): # Define the bypass_validation function
        if self.awaiting_next_submission:
            # Move to the next question after showing feedback
            self.current_question_index += 1 # Move to the next question
            self.display_next_question()  
            return

        if self.questions:
            question = self.questions[self.current_question_index]
            # Mark the answer as correct
            self.correct_answers += 1  # Increment correct answers
            self.awaiting_next_submission = True
            self.display_feedback(True, "Bypassed validation. Answer marked as correct.", "")
        else:
            self.display_feedback(False, "No questions available.", "")
    
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
    def validate_code_answer(self, question_data, user_code):  # Define the validate_code_answer function
        user_output, user_errors = run_user_code(user_code) # Run the user code
        correct, feedback = validate_answer_with_gpt( # Validate the answer with GPT
            question_data, user_code=user_code, user_output=user_output # Pass the question data, user code, and user output
        )  
        feedback_message = feedback  # Initialize feedback message

        if not correct: # Save the mistake if incorrect
            feedback_message += f"\n\nYour Output:\n{user_output or 'No output.'}" # Append user output to feedback
            if user_errors: # Check if errors are present
                feedback_message += f"\n\nErrors:\n{user_errors}" # Append errors to feedback
            self.save_mistake(question_data, user_code, feedback_message) # Save the mistake

            return correct, feedback_message # Return the validation result

    # Function to validate scenario answers
    def validate_scenario_answer(self, question_data, user_response): # Define the validate_scenario_answer function
        correct, feedback = validate_answer_with_gpt( # Validate the answer with GPT
            question_data=question_data, user_response=user_response # Pass the question data and user response
        )

        if not correct: # Save the mistake if incorrect
            self.save_mistake(question_data, user_response, feedback) # Save the mistake

        return correct, feedback # Return the validation result


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
    # Function to display feedback
    def display_feedback(self, correct, feedback, correct_answer, user_code="", question_type=""): # Define the display_feedback function
        feedback_label = self.ids.feedback_label  # Access the feedback label using ids
        
        if correct: # Check if the answer is correct
            feedback_label.text = "Correct!" # Display correct feedback
            feedback_label.color = (0, 1, 0, 1)  # Green color for correct feedback

            # Hide buttons for code comparison and sample solution when correct
            self.ids.sample_solution_label.opacity = 0 # Hide the sample solution
            self.ids.sample_solution_label.size_hint_y = 0 # Hide the sample solution
            self.ids.code_comparison_label.opacity = 0 # Hide the code comparison
            self.ids.code_comparison_label.size_hint_y = 0 # Hide the code comparison
        else: # Handle incorrect answers
            if question_type == 'write_code': # Check if the question type is write code
                feedback_label.text = f"\n{feedback}\n" # Display the feedback
                feedback_label.color = (1, 0, 0, 1)  # Red color for incorrect feedback
                feedback_label.text_size = (self.width, None) # Adjust text wrapping width
                feedback_label.size_hint_y = None # Set the size hint for y-axis
                feedback_label.height = feedback_label.texture_size[1] # Set the height based on the texture size
                if user_code: # Check if user code is provided
                    self.user_code = user_code # Store the user code
                else: # Handle case where user code is not provided
                    self.ids.sample_solution_label.opacity = 1 # Make the sample solution visible
                    self.ids.sample_solution_label.size_hint_y = None # Set the size hint for y-axis
                    self.ids.code_comparison_label.opacity = 1 # Make the code comparison visible
                    self.ids.code_comparison_label.size_hint_y = None # Set the size hint for y-axis
            elif question_type == 'scenario': # Check if the question type is scenario
                print("Displaying feedback for scenario questions") # Debugging output for scenario questions
                feedback_label.text = f"{feedback}\nCorrect Answer: {correct_answer}" # Display the feedback
                feedback_label.color = (1, 0, 0, 1)  # Red color for incorrect feedback 
            else: # Handle other question types
                feedback_label.text = f"Incorrect\nCorrect Answer: {correct_answer}" # Display the feedback
                feedback_label.color = (1, 0, 0, 1) # Red color for incorrect feedback

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
   
    # Function to show the sample solution
    def show_sample_solution(self): # Define the show_sample_solution function
        if self.questions and self.current_question_index < len(self.questions): # Check if questions are available
            question = self.questions[self.current_question_index] # Get the current question
            sample_solution_text = question.get('correct_answer', 'Sample solution not available.') # Get the sample solution text
        else: # Handle case where questions are not available
            sample_solution_text = "Sample solution not available." # Set the sample solution text

        # Use ScrollView to wrap content in the popup
        scroll_view = ScrollView(size_hint=(1, 1), bar_width=10) # Create a ScrollView
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[10, 10]) # Create a BoxLayout
        content.bind(minimum_height=content.setter('height')) # Bind the minimum height

        label = Label( # Create a Label
            text=sample_solution_text, # Set the text
            size_hint_y=None, # Set the size hint for y-axis
            text_size=(self.width * 0.8, None),  # Adjust to fit width within scrollable area
            halign='left', # Set the horizontal alignment
            valign='top', # Set the vertical alignment
            padding=(10, 10) # Add padding for better readability
        )
        label.bind(texture_size=label.setter('size')) # Bind the texture size
        content.add_widget(label) # Add the label to the content
 
        scroll_view.add_widget(content) # Add the content to the scroll view

        popup = Popup(title="Sample Solution", content=scroll_view, size_hint=(0.9, 0.9)) # Create a Popup
        popup.open() # Open the popup

    # Function to show code comparison
    def show_code_comparison(self): # Define the show_code_comparison function
        user_code_to_display = getattr(self, 'user_code', "No code provided.") # Get the user code to display

        # Ensure the method fetches the correct code from the question's data
        if self.questions and self.current_question_index < len(self.questions): # Check if questions are available
            question = self.questions[self.current_question_index] # Get the current question
            correct_code = question.get('correct_answer', 'Correct code not available.')   # Get the correct code   
        else: # Handle case where questions are not available
            correct_code = "Correct code not available." # Set the correct code

        # Create content for the popup with a ScrollView
        scroll_view = ScrollView(size_hint=(1, 1), bar_width=10) # Create a ScrollView
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[10, 10], spacing=20) # Create a BoxLayout
        content.bind(minimum_height=content.setter('height')) # Bind the minimum height

        # User Code Display
        user_code_text = f"User Code:\n{user_code_to_display}" if user_code_to_display else "User Code:\nNo code provided." # Set the user code text
        user_code_label = Label( # Create a Label
            text=user_code_text, # Set the text
            size_hint_y=None, # Set the size hint for y-axis
            text_size=(self.width * 0.8, None),  # Adjust text wrapping width
            halign='left', # Set the horizontal alignment
            valign='top', # Set the vertical alignment
            padding=(15, 15) # Add padding for better readability
        )
        user_code_label.bind(texture_size=user_code_label.setter('size')) # Bind the texture size

        # Correct Code Display
        correct_code_text = f"Correct Code:\n{correct_code}" # Set the correct code text
        correct_code_label = Label( # Create a Label
            text=correct_code_text, # Set the text
            size_hint_y=None, # Set the size hint for y-axis
            text_size=(self.width * 0.8, None),  # Adjust text wrapping width
            halign='left', # Set the horizontal alignment
            valign='top', # Set the vertical alignment
            padding=(10, 10) # Add padding for better readability
        )
        correct_code_label.bind(texture_size=correct_code_label.setter('size')) # Bind the texture size

        # Add user code and correct code labels to the main content in stacked order
        content.add_widget(user_code_label) # Add the user code label
        content.add_widget(correct_code_label) # Add the correct code label
        scroll_view.add_widget(content) # Add the content to the scroll view

        # Create and open a popup to display the content
        popup = Popup(title="Code Comparison", content=scroll_view, size_hint=(0.9, 0.9)) # Create a Popup
        popup.open() # Open the popup

# Custom CodeInput for enhanced code input
class CustomCodeInput(CodeInput):  # Define the CustomCodeInput class
    def __init__(self, **kwargs): # Define the constructor
        super(CustomCodeInput, self).__init__(**kwargs) # Call the superclass constructor
        self.lexer = PythonLexer()  # Enable Python syntax highlighting
        self.font_size = 14  # Adjust font size as needed
        self.padding = [10, 10, 10, 10]  # Add padding for better readability

    def insert_text(self, substring, from_undo=False): # Define the insert_text function
        if substring == '\t': # Check for Tab key
            substring = '    '  # Replace Tab with four spaces
        super(CustomCodeInput, self).insert_text(substring, from_undo=from_undo) # Call the superclass insert_text method

#Class to handle the chapter review result screen
class ChapterReviewResultScreen(Screen): # Define the ChapterReviewResultScreen class
    # Function to display the results
    def display_results(self, total_questions, correct_answers, chapter): # Define the display_results function
        self.total_questions = total_questions # Store the total number of questions
        self.correct_answers = correct_answers  # Store the number of correct answers
        self.chapter = chapter # Store the chapter number

        score_percentage = (correct_answers / total_questions) * 100 # Calculate the score percentage
        self.ids.score_label.text = f"Score: {correct_answers}/{total_questions} ({score_percentage:.2f}%)" # Display the score

        if score_percentage >= 70: # Check if the score is above 70%
            self.ids.result_label.text = "Congratulations! You passed the chapter review." # Display the passing message
            # Unlock the next chapter 
            user_progress = UserProgress(self.manager.get_screen('main').user_id) # Get the user progress
            if user_progress.chapter == chapter: # Check if the user is on the current chapter
                user_progress.chapter += 1 # Unlock the next chapter
                user_progress.lesson = 1 # Reset the lesson to 1
                user_progress.save_progress() # Save the user progress
        else: # Handle case where the score is below 70%
            self.ids.result_label.text = "You did not pass the review. Please try again." # Display the failure message

    # Function to retry the review
    def retry_review(self): # Define the retry_review function
        # Restart the chapter review
        chapter_review_screen = self.manager.get_screen('chapter_review') # Get the ChapterReviewScreen instance
        chapter_review_screen.start_chapter_review(self.manager.get_screen('main').user_id, self.chapter) # Start the chapter review
        self.manager.current = 'chapter_review' # Navigate to the chapter review screen

    # Function to continue to the main screen
    def continue_to_main(self): # Define the continue_to_main function
        # Go back to the main screen
        self.manager.get_screen('main').on_enter()  # Refresh the roadmap
        self.manager.current = 'main' # Navigate to the main screen

#Class to handle the cumulative review result screen
# Class to handle the cumulative review result screen
class CumulativeReviewResultScreen(Screen):  # Define the CumulativeReviewResultScreen class
    # Define the constructor 
    def on_enter(self):  # Define the on_enter function
        # Load certificate path from the database when entering the result screen
        try:  # Try to fetch the certificate path from the database
            with sqlite3.connect('progress.db') as conn:  # Connect to the database
                cursor = conn.cursor()  # Create a cursor object
                cursor.execute('SELECT certificate_path FROM certificates WHERE user_id = ?', (self.user_id,))  # Execute an SQL query
                result = cursor.fetchone()  # Fetch the first row from the result set
                if result and result[0]:  # Check if the result is found and not empty
                    self.certificate_path = result[0]  # Set the certificate path
                else:  # Handle case where the certificate path is not found
                    self.certificate_path = None  # Set the certificate path to None
        except sqlite3.Error as e:  # Handle database errors
            print(f"Database error while fetching certificate path: {e}")  # Debugging statement
            self.certificate_path = None  # Set the certificate path to None

    # Function to display the results
    def display_results(self, total_questions, correct_answers, user_id):  # Removed user_name from parameter list
        self.total_questions = total_questions  # Store the total number of questions
        self.correct_answers = correct_answers  # Store the number of correct answers
        self.user_id = user_id  # Store user ID for future reference

        # Fetch the user's name from the database
        user_name = None
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                if result:
                    user_name = result[0]
                else:
                    print(f"No user found with id {user_id}")
                    user_name = "User"  # Default name if user not found
        except sqlite3.Error as e:
            print(f"Database error while fetching user name: {e}")
            user_name = "User"  # Default name in case of an error

        score_percentage = (correct_answers / total_questions) * 100  # Calculate the score percentage
        self.ids.score_label.text = f"Score: {correct_answers}/{total_questions} ({score_percentage:.2f}%)"  # Display the score

        if score_percentage >= 70:  # Check if the score is above 70%
            self.ids.result_label.text = f"Congratulations, {user_name}! You passed the cumulative review."  # Display the passing message
            self.ids.certificate_button.disabled = False  # Enable the certificate download button
            self.generate_certificate(user_id=user_id)  # Generate the certificate if the user passed
        else:  # Handle case where the score is below 70%
            self.ids.result_label.text = f"Sorry, {user_name}. You did not pass the cumulative review. Please try again."  # Display the failure message
            self.ids.certificate_button.disabled = True  # Disable the certificate download button

    # Function to generate the certificate
    def generate_certificate(self, user_id):  # Removed user_name from parameters
        # Paths for certificate generation
        app_dir = os.path.dirname(os.path.abspath(__file__))  # Get the application directory
        certificates_dir = os.path.join(app_dir, "certificates")  # Set the certificates directory

        # Create the certificates directory if it doesn't exist
        if not os.path.exists(certificates_dir):  # Check if the certificates directory does not exist
            os.makedirs(certificates_dir)  # Create the certificates directory

        # Retrieve the user's name from the database using the user_id
        user_name = None
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                if result:
                    user_name = result[0]
                else:
                    print(f"No user found with id {user_id}")
                    return  # If no user is found, exit the function
        except sqlite3.Error as e:
            print(f"Database error while fetching user name: {e}")
            return  # Exit if there's a database error

        # Ensure that we have a valid user name
        if not user_name:
            print(f"User name not found for user_id {user_id}")
            return

        output_file_path = os.path.join(certificates_dir, f"user_{user_id}_certificate.pdf")  # Set the output file path

        # Generate the certificate using the template
        template_image_path = "Assets/Certificate of Completion.png"  # Set the template image path
        current_date = datetime.datetime.now().strftime("%B %d, %Y")  # Get the current date

        with Image.open(template_image_path) as img:  # Open the template image
            img_width, img_height = img.size  # Get the image size

            # Create a new PDF using reportlab
            c = canvas.Canvas(output_file_path, pagesize=(img_width, img_height))  # Create a canvas object
            c.drawImage(template_image_path, 0, 0, width=img_width, height=img_height)  # Draw the template image

            # Add the user's name and date to the certificate
            c.setFont("Helvetica-Bold", 50)  # Set the font and size
            c.setFillColorRGB(0, 0, 0)  # Set the fill color to black
            name_x, name_y = 830, 800  # Set the name coordinates
            c.drawString(name_x, name_y, user_name)  # Draw the user's name

            c.setFont("Helvetica-Bold", 32)  # Set the font and size
            date_x, date_y = 830, 625  # Set the date coordinates
            c.drawString(date_x, date_y, current_date)  # Draw the current date

            c.save()  # Save the canvas

        # Save certificate details to the database
        try:  # Try to save the certificate details to the database
            with sqlite3.connect('progress.db') as conn:  # Connect to the database
                cursor = conn.cursor()  # Create a cursor object
                cursor.execute('''
                    INSERT INTO certificates (user_id, certificate_path, date_issued)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET certificate_path = excluded.certificate_path, date_issued = excluded.date_issued
                ''', (user_id, output_file_path, current_date))

                conn.commit()  # Commit the changes
        except sqlite3.Error as e:  # Handle database errors
            print(f"Database error while saving certificate: {e}")  # Debugging statement

        self.certificate_path = output_file_path  # Set the certificate path

    # Function to download the certificate
    def download_certificate(self): # Define the download_certificate function
        # Use plyer to let the user download their certificate
        if self.certificate_path and os.path.exists(self.certificate_path): # Check if the certificate path exists
            try: # Try to download the certificate
                filechooser.open_file(path=self.certificate_path) # Open the file chooser at the certificate path
            except Exception as e:  # Handle download errors
                print(f"Error downloading the certificate: {e}")     # Debugging statement
        else: # Handle case where the certificate path is not found
            print("Certificate not found.") # Debugging statement

    # Function to retry the review
    def retry_review(self): # Define the retry_review function
        # Restart the cumulative review
        cumulative_review_screen = self.manager.get_screen('cumulative_review') #reference to the CumulativeReviewScreen
        cumulative_review_screen.start_cumulative_review(self.manager.get_screen('main').user_id) # Start the cumulative review
        self.manager.current = 'cumulative_review' # Navigate to the cumulative review screen

    # Function to continue to the main screen
    def continue_to_main(self): # Define the continue_to_main function
        # Go back to the main screen
        self.manager.get_screen('main').on_enter()  # Refresh the roadmap
        self.manager.current = 'main' # Navigate to the main screen

Builder.load_file("main.kv") # Load the Kivy file

#Function to start the app
class MyApp(App):   # Define the MyApp class
    user_id = None # Initialize the user ID
    def build(self): # Define the build function
        sm = ScreenManager() # Create a ScreenManager
        sm.add_widget(LoginScreen(name="login")) # Add the LoginScreen to the Screen
        sm.add_widget(MainScreen(name="main"))  # Add the MainScreen to the Screen
        sm.add_widget(LessonScreen(name="lesson")) # Add the LessonScreen to the Screen
        sm.add_widget(ProfileScreen(name="profile")) # Add the ProfileScreen to the Screen
        sm.add_widget(MistakesScreen(name="mistakes")) # Add the MistakesScreen to the Screen
        sm.add_widget(QuestionScreen(name="questions")) # Add the QuestionScreen to the Screen
        sm.add_widget(ChapterReviewScreen(name="chapter_review")) # Add the ChapterReviewScreen to the Screen
        sm.add_widget(ChapterReviewResultScreen(name="chapter_review_result")) # Add the ChapterReviewResultScreen to the Screen
        sm.add_widget(CumulativeReviewScreen(name="cumulative_review")) # Add the CumulativeReviewScreen to the Screen
        sm.add_widget(CumulativeReviewResultScreen(name="cumulative_review_result"))  # Add the CumulativeReviewResultScreen to the Screen
        return sm   # Return the ScreenManager

# Main entry point
if __name__ == "__main__":  # Check if the script is being run directly
    MyApp().run() # Run the Kivy application