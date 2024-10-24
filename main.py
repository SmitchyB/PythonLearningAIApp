from colorama import Fore, init # Import the Fore and init functions from colorama
import sqlite3 # Import the sqlite3 module
import bcrypt # Import the bcrypt module
from config import chapters # Import the chapters dictionary from config.py
from questions import validate_answer_with_gpt, generate_python_question, generate_lesson_content, generate_questions_from_content, generate_review_questions, generate_cumulative_review # Import functions from questions.py
import logging # Import the logging module
from fuzzywuzzy import fuzz # Import the fuzz function from fuzzywuzzy
import subprocess # Import the subprocess module
import sys # Import the sys module

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
# Helper function to run the user's code
def run_user_code(code):
    """Execute the user's code safely and capture the output."""
    try:
        # Use subprocess to run the code and capture both stdout and stderr
        result = subprocess.run(
            [sys.executable, "-c", code],  # Run code with the current Python interpreter
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "Execution timed out."
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
    def __init__(self, user_id): # Define the __init__ method
        self.user_id = user_id # Initialize the user ID
        self.chapter = 1 # Initialize the chapter to 1
        self.lesson = 1 # Initialize the lesson to 1
        self.lesson_scores = {}  # Track lesson scores

    def update_score(self, correct, total): # Define the update_score method
        """Update the score for the current lesson."""
        if self.chapter not in self.lesson_scores: # Check if chapter is not in lesson scores
            self.lesson_scores[self.chapter] = [] # Initialize the chapter in lesson scores
        self.lesson_scores[self.chapter].append({ # Append the lesson score
            'lesson': self.lesson, # Add the lesson number
            'correct': correct, # Add the number of correct answers
            'total': total # Add the total number of questions
        })
    def save_progress(self): # Define the save_progress method
        """Save the user's progress to the database."""
        try: # Try to save the user's progress
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute an SQL query
                    'UPDATE users SET chapter = ?, lesson = ? WHERE id = ?', # Update the user's chapter and lesson
                    (self.chapter, self.lesson, self.user_id) # Pass the chapter, lesson, and user ID as parameters
                )
                conn.commit() # Commit the transaction
                logging.info(f"Progress saved: Chapter {self.chapter}, Lesson {self.lesson}") # Log the progress update
        except sqlite3.Error as e: # Handle database errors
            logging.error(f"Failed to save progress: {e}") # Log the error
    
    # Updated function signature to accept chapter
    def calculate_chapter_score(self): # Define the calculate_chapter_score method
        """Calculate the cumulative chapter score."""
        total_correct = sum(score['correct'] for score in self.lesson_scores.get(self.chapter, [])) # Calculate the total correct answers
        total_questions = sum(score['total'] for score in self.lesson_scores.get(self.chapter, [])) # Calculate the total questions
        score = calculate_percentage_score(total_correct, total_questions) # Calculate the percentage score
        return score
    
# Calculate the percentage score
def calculate_percentage_score(correct, total): # Define the calculate_percentage_score function
    """Calculate the percentage score.""" 
    return (correct / total) * 100 if total > 0 else 0 # Calculate the percentage score

# Function to generate the lesson content, questions and track user progress
def play_lesson(progress): # Define the play_lesson function
    """Play a single lesson with generated content and questions."""
    chapter = progress.chapter # Get the current chapter
    lesson = progress.lesson # Get the current lesson

    # Fetch the chapter and lesson titles
    chapter_title = chapters[chapter]["title"] # Get the chapter title
    lesson_title = chapters[chapter]["lessons"][lesson]["title"] # Get the lesson title
    question_count = chapters[chapter]["lessons"][lesson]["question_count"] # Get the question count

    print(Fore.CYAN + f"\n--- {chapter_title} ---") # Print the chapter title
    print(Fore.CYAN + f"--- Lesson {lesson}: {lesson_title} ---") # Print the lesson title

    # Generate the lesson content
    lesson_content = generate_lesson_content(chapter, lesson) # Generate the lesson content
    print(Fore.YELLOW + "\nLesson Content:\n") # Print the lesson content title
    print(lesson_content) # Print the lesson content

    # Generate questions based on the lesson content
    available_questions = generate_questions_from_content(chapter, lesson, lesson_content, question_count) # Generate questions

    correct_answers = 0 # Initialize the number of correct answers

    # Ask the questions and validate answers
    for i, question_data in enumerate(available_questions): # Iterate over the questions
        print(f"\nQuestion {i + 1}/{question_count}:") # Print the question number
        correct = ask_question_and_validate(question_data) # Ask the question and validate the answer

        if correct: # Check if the answer is correct
            print(Fore.GREEN + "Correct!") # Print a success message
            correct_answers += 1 # Increment the correct answers count
        else:
            print(Fore.RED + f"Wrong! The correct answer was: {question_data.get('correct_answer', 'N/A')}") # Print the correct answer

    # Track the score
    progress.update_score(correct_answers, question_count) # Update the score

    print(f"\nLesson {lesson} complete! You answered {correct_answers} out of {question_count} correctly.") # Print the lesson completion message
    progress.save_progress() # Save the progress

# Function to ask questions and validate answers
def ask_question_and_validate(question_data):
    """Display the question, get user input, and validate the answer."""
    if not question_data or 'question' not in question_data:
        logging.error(f"Invalid question data: {question_data}")
        raise ValueError("Error: Question data is missing or invalid.")

    # Display the question
    print(Fore.CYAN + f"\n{question_data['question']}")

    # Display the options with labels and texts
    if question_data['type'] == "multiple_choice" and 'options' in question_data:
        # Log and print each option as it is processed
        for label, option_text in question_data['options'].items():
            print(f"{label}: {option_text}")

        # Get user input and validate it
        user_answer = input("Enter the letter of your answer (A, B, C, D): ").strip().upper()

        # Validate input
        if user_answer not in question_data['options']:
            logging.warning(f"Invalid input received: {user_answer}")
            print(Fore.RED + "Invalid input. Please enter a valid option letter (A, B, C, D).")
            return False

        # Check if the answer is correct
        correct = user_answer == question_data['correct_answer']
        if correct:
            print(Fore.GREEN + "Correct!")
        else:
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}) {question_data['options'][question_data['correct_answer']]}")
        return correct
        
    elif question_data['type'] == "true_false": # Check if the question type is true or false
        user_answer = input("True or False? ").strip().lower() # Get the user's answer
        logging.debug(f"User Answer: {user_answer} | Expected Answer: {question_data['correct_answer']}")
        correct = user_answer == question_data['correct_answer'].lower() # Check if the user's answer is correct
        if correct:
            print(Fore.GREEN + "Correct!")
        else:
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}")
        return correct

    elif question_data['type'] == "fill_in_the_blank": # Check if the question type is fill in the blank
        user_answer = input("Fill in the blank: ").strip().lower() # Get the user's answer
        logging.debug(f"User Answer: {user_answer} | Expected Answer: {question_data['correct_answer']}")
        correct = user_answer == question_data.get('correct_answer', '').lower() # Check if the user's answer is correct
        if correct:
            print(Fore.GREEN + "Correct!")
        else:
            print(Fore.RED + f"Incorrect. The correct answer was {question_data['correct_answer']}")
        return correct

    elif question_data['type'] == "write_code":
        print(Fore.CYAN + "\nWrite your code solution below. Use multiple lines if needed. Type 'END' on a new line when finished:")

        # Collect multi-line user code input
        user_code = ""
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            user_code += line + "\n"

        logging.debug(f"User's Code:\n{user_code}")

        # Run the user's code and capture output or errors
        user_output, user_errors = run_user_code(user_code)

        if user_errors:
            print(f"\nYour code produced the following error:\n{user_errors}")
            logging.error(f"User's Code Error: {user_errors}")
        else:
            print(f"\nYour code produced the following output:\n{user_output}")
            logging.info(f"User's Code Output: {user_output}")

        # Validate the user's solution using GPT
        is_correct, feedback = validate_answer_with_gpt(
            question_data, user_code=user_code, user_output=user_output
        )

        # Display the result based on GPT validation
        if is_correct:
            print(Fore.GREEN + "Correct! Well done.")
        else:
            print(Fore.RED + "Incorrect. Review the feedback below:")
            print(Fore.YELLOW + feedback)

        return is_correct

    elif question_data['type'] == "scenario":
        user_answer = input("Describe your response to the scenario: ").strip()

        # Secondary GPT Call to Validate the Answer
        is_correct = validate_answer_with_gpt(
            question_data['question'], 
            question_data['answer'], 
            user_answer
        )

        if is_correct:
            print(Fore.GREEN + "Correct!")
        else:
            print(Fore.RED + f"Incorrect. The correct answer was: {question_data.get('answer', 'N/A')}")

        return is_correct

# Function to generate review questions
def review_test(progress): # Define the review_test function
    """Conduct the chapter review and return whether the user passed.""" 
    chapter = progress.chapter # Get the current chapter
    questions = generate_review_questions(progress, chapter) # Generate review questions
    correct_answers = 0 # Initialize the number of correct answers

    print(Fore.MAGENTA + f"\n--- Review Test: {chapters[chapter]['title']} ---") # Print the review test title
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score

    for i, question_data in enumerate(questions): # Iterate over the questions
        print(f"\nQuestion {i + 1}/{len(questions)}:") # Print the question number
        if ask_question_and_validate(question_data): # Ask the question and validate the answer
            correct_answers += 1 # Increment the correct answers count
        else: # Handle incorrect answers
            progress.add_review_mistake(chapter) # Track the review mistakes

    if correct_answers >= int(len(questions) * 0.7): # Check if the user passed the review
        print(Fore.GREEN + "Congratulations! You passed the review.\n") # Print a success message
        return True # Return True for passing the review
    else: # Handle failing the review
        print(Fore.RED + "You did not pass the review. Try again!\n") # Print an error message
        return False # Return False for failing the review

#Function to generate cumulative review questions
def cumulative_review_test(progress): # Define the cumulative_review_test function
    """Conduct the cumulative review covering all chapters and return pass status.""" 
    questions = generate_cumulative_review(progress) # Generate cumulative review questions
    correct_answers = 0 # Initialize the number of correct answers
 
    print(Fore.MAGENTA + "\n--- Final Cumulative Review: All Chapters ---") # Print the cumulative review title
    print(Fore.YELLOW + f"You need {int(len(questions) * 0.7)} correct answers to pass.\n") # Print the passing score

    for i, question_data in enumerate(questions): # Iterate over the questions
        print(f"\nQuestion {i + 1}/{len(questions)}:") # Print the question number
        if ask_question_and_validate(question_data): # Ask the question and validate the answer
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
def play_game(): # Define the play_game function
    """Main game loop to guide the user through lessons and reviews.""" 
    progress = welcome() # Welcome the user and get progress object

    while progress.chapter <= 20: # Loop through chapters
        print(Fore.CYAN + f"\n--- Chapter {progress.chapter}: {chapters[progress.chapter]['title']} ---\n") # Print the chapter title

        while progress.lesson <= 7: # Loop through lessons
            play_lesson(progress)  # Play and track each lesson
            progress.lesson += 1  # Increment to the next lesson
            progress.save_progress()

        # Run the chapter review after completing all lessons
        if review_test(progress): # Run the review test
            progress.chapter += 1  # Move to the next chapter
            progress.lesson = 1  # Reset to the first lesson
            progress.save_progress() # Save the progress
        else:
            print(Fore.RED + "You need to pass the review to unlock the next chapter.") # Print an error message

    print(Fore.GREEN + "Congratulations! You've completed the course!") # Print a success message

    # Handle Cumulative Review (Chapter 21)
    print(Fore.CYAN + "\n--- Final Cumulative Review: All Chapters ---") # Print the cumulative review title
    if cumulative_review_test(progress):  # Run cumulative review
        print(Fore.GREEN + "Congratulations! You've completed the course!") # Print a success message
    else: # Handle failing the cumulative review
        print(Fore.RED + "You need to pass the cumulative review to complete the course.") # Print an error message

    print(Fore.GREEN + "Thank you for playing! Your progress is saved.") # Print a closing message

def enter_testing_mode():
    """Enter a testing mode to validate question types without lesson generation."""
    print("Testing Mode: Choose the type of question to generate:")
    print("1: Multiple Choice")
    print("2: True/False")
    print("3: Fill in the Blank")
    print("4: Write Code")
    print("5: Scenario")

    choice = input("Enter your choice (1-5): ")

    # Generate the question based on user input.
    question_data = generate_python_question(choice)

    if question_data:
        # Use `ask_question_and_validate()` directly.
        is_correct = ask_question_and_validate(question_data)
    else:
        print("Failed to generate a valid question.")
#Function to welcome users  
def welcome():
    while True:
        print("\n--- Welcome ---")
        print("1) Log In")
        print("2) Register")
        print("3) Testing Mode")

        choice = input("Select an option (1/2/3): ").strip()

        if choice == '1':
            user = login_user()
            if user:
                progress = UserProgress(user[0])  # Restore user progress
                progress.chapter = user[4]        # Load saved chapter
                progress.lesson = user[5]         # Load saved lesson
                return progress  # Return progress to continue the game loop

        elif choice == '2':
            register_user()
            print(Fore.GREEN + "\nRegistration complete! Please log in.")

        elif choice == '3':
            enter_testing_mode()  # Launch testing mode
        else:
            print(Fore.RED + "Invalid choice. Please select 1, 2, or 3.")


# Main entry point
if __name__ == "__main__":
    welcome()  # Start with the welcome screen
