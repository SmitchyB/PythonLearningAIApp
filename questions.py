
from dotenv import load_dotenv  # Import the load_dotenv function from the dotenv module
import os # Import the os module
import random   # Import the random module
from colorama import Fore   # Import the Fore class from the colorama module
from config import chapters # Import the chapters dictionary from the config module
from openai import OpenAI  # Import the OpenAI class from the openai module
import logging # Import the logging module for logging messages
from fuzzywuzzy import fuzz # Import the fuzz function from the fuzzywuzzy module for string similarity
import re # Import the re module for regular expressions
import sqlite3 # Import the sqlite3 module for database operations
# Configure logging to display only your function logs
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
format = Fore.CYAN + "%(asctime)s %(levelname)s: %(message)s" + Fore.RESET
# Load the environment variables
load_dotenv()

# Retrieve the API key
api_key = os.getenv("OPENAI_API_KEY")

# Check if the API key is not found
if not api_key:
    # Raise a ValueError
    raise ValueError("API key not found. Check your .env file.")

# Create an OpenAI client
client = OpenAI(api_key=api_key)

stored_questions = set()  # Store seen questions globally

# Define the is_question_unique function
def is_question_unique(new_question, threshold=70): # Set the default threshold to 70
    """Check if a new question is unique based on similarity.""" 
    for stored_question in stored_questions: # Iterate over the stored questions
        similarity = fuzz.ratio(new_question.lower(), stored_question.lower()) # Calculate the similarity ratio
        if similarity > threshold: # Check if the similarity is above the threshold
            return False # Return False if the question is not unique
    return True # Return True if the question is unique

# Define the store_question function
def store_question(question_text): # Define the store_question function with the question_text parameter
    """Store a unique question to avoid duplicates."""
    stored_questions.add(question_text) # Add the question to the stored questions set

# Define the reset_similarity_database function
def reset_similarity_database(): # Define the reset_similarity_database function
    """Clear the stored questions between lessons."""
    global stored_questions # Access the global stored_questions set
    stored_questions.clear() # Clear the stored questions set

# Define the generate_lesson_content function
def generate_lesson_content(progress, chapter, lesson):
    """Retrieve or generate lesson content for a specific lesson."""
    try:
        # Check if the lesson content is already stored in the database
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
                logging.info(f"Retrieved stored content for Chapter {chapter} Lesson {lesson}")
                return row[0]  # Return the stored content

        # If content is not found, generate it
        chapter_title = chapters[chapter]["title"]
        lesson_title = chapters[chapter]["lessons"][lesson]["title"]

        prompt = (
            f"Provide an educational and engaging lesson on the following topic:\n"
            f"Chapter: {chapter_title}\n"
            f"Lesson: {lesson_title}\n"
            f"The lesson should include 2-3 paragraphs explaining the concept, examples, "
            f"and key points to remember."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a Python tutor."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        lesson_content = response.choices[0].message.content.strip()

        # Store the generated content in the database
        with sqlite3.connect('progress.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO lesson_content (user_id, chapter, lesson, content)
                VALUES (?, ?, ?, ?)
                ''',
                (progress.user_id, chapter, lesson, lesson_content)
            )
            conn.commit()
            logging.info(f"Stored generated content for Chapter {chapter} Lesson {lesson}")

        return lesson_content

    except Exception as e:
        logging.error(f"Error generating or retrieving lesson content: {e}")
        return "Unable to retrieve or generate lesson content."


# Define the generate_questions_from_content function
def generate_questions_from_content(chapter, lesson, content, question_count, max_retries=2): # Define the generate_questions_from_content function with the chapter, lesson, content, question_count, and max_retries parameters
    """Generate a set of questions based on the lesson content with retry functionality."""
    questions = []  # Initialize an empty list to store the questions
    allowed_types = determine_question_types(chapters[chapter]['lessons'][lesson]['title'].lower()) # Determine the allowed question types based on the lesson title and store in allowed_types

    def send_request_with_retries(prompt, retries_left): # Define the send_request_with_retries function with the prompt and retries_left parameters
        """Send request to OpenAI API with retry support.""" 
        try: # Try block to handle exceptions
            logging.debug(f"Sending request to OpenAI API. Retries left: {retries_left}") # Log the API request

            response = client.chat.completions.create( # Call the OpenAI API to generate the content
                model="gpt-3.5-turbo", # Use the GPT-3.5-turbo model 
                messages=[  # Define the messages to send to the API
                    {"role": "system", "content": "You are a Python tutor."}, # Define the system message
                    {"role": "user", "content": prompt} # Define the user message
                ],
                temperature=0.7, # Set the temperature to 0.7 for diversity
                max_tokens=400 # Limit the token count for the response
            )

            if not response or not response.choices: # Check if the response is empty or improperly formatted
                logging.warning("API response is empty or improperly formatted.") # Log a warning message
                raise ValueError("Invalid API response.") # Raise a ValueError

            return response.choices[0].message.content.strip() # Return the content from the API response

        except Exception as e: # Catch any exceptions
            logging.error(f"API request failed: {e}") # Log the error
            if retries_left > 0: # Check if there are retries left
                return send_request_with_retries(prompt, retries_left - 1) # Retry the request
            else: # If no retries left
                logging.error("Exceeded maximum retries for API request.") # Log an error message
                return None # Return None

    while len(questions) < question_count: # Loop until the desired number of questions is generated
        try: # Try block to handle exceptions
            question_type = random.choice(allowed_types)  # Random question type
            prompt = ( # Define the prompt string
                f"Based on the content below, generate a unique and non-repetitive {question_type} question:\n" # Prompt to generate a unique question
                f"\"{content}\"\n" # Include the lesson content in the prompt
                f"Ensure it covers a specific aspect of the lesson and is distinct from other potential questions." # Include the requirements for the question
                f"\n{build_prompt(chapter, lesson, question_type)}" # Include the generated prompt based on the question type
            )

            question_text = send_request_with_retries(prompt, max_retries) # Send the request to the API with retries

            if not question_text: # Check if the question text is empty
                logging.warning("Failed to generate a valid question after retries.") # Log a warning message
                continue  # Try generating another question

            question_data = parse_response(question_text, question_type) # Parse the response to extract the question data

            if question_data and "question" in question_data and is_question_unique(question_data["question"]): # Check if the question data is valid and the question is unique
                questions.append(question_data) # Append the question data to the questions list
                store_question(question_data["question"])   # Store the question to avoid duplicates
            else: # If the question is not unique
                continue  # Skip duplicates or invalid questions

        except Exception as e: # Catch any exceptions
            logging.error(f"Error generating question: {e}") # Log the error

    if len(questions) < question_count: # Check if not enough questions were generated
        logging.warning("Not enough unique questions generated.") # Log a warning message

    return questions # Return the generated questions

# Define the determine_question_types function
def determine_question_types(title): # Define the determine_question_types function with the title parameter
    """Determine allowed question types based on the lesson title."""
    if any(keyword in title for keyword in ["introduction", "overview", "getting started", # Check if the title contains introductory keywords
                                            "what is", "setting up", "first", "installing"]):
        # No code challenges allowed for introductory lessons 
        return ["multiple_choice", "true_false", "fill_in_the_blank", "scenario"] # Return the allowed question types
    elif any(keyword in title for keyword in ["review", "test"]): # Check if the title contains review or test keywords
        # Review lessons can have all types except write_code
        return ["multiple_choice", "true_false", "fill_in_the_blank", "scenario"] # Return the allowed question types
    else:   
        # For other advanced lessons, all question types are allowed
        return ["multiple_choice", "true_false", "fill_in_the_blank", "scenario", "write_code"] # Return the allowed question types

# Define the map_choice_to_type function
def map_choice_to_type(choice): # Define the map_choice_to_type function with the choice parameter
    logging.debug(f"map_choice_to_type received choice: {choice}") # Log the choice received by the function
    return { # Return the corresponding question type based on the choice
        '1': 'multiple_choice', # Return 'multiple_choice' for choice 1
        '2': 'true_false', # Return 'true_false' for choice 2
        '3': 'fill_in_the_blank', # Return 'fill_in_the_blank' for choice 3
        '4': 'write_code', # Return 'write_code' for choice 4
        '5': 'scenario' # Return 'scenario' for choice 5
    }.get(choice, 'multiple_choice') # Return 'multiple_choice' by default

# Define the generate_python_question function for the testing mode
def generate_python_question(choice, max_retries=2): # Define the generate_python_question function with the choice and max_retries parameters
    """Generate a Python-related question for testing purposes with retry support."""
    try:
        logging.debug("Starting generate_python_question function.") # Log a debug message

        question_type = map_choice_to_type(choice) # Map the choice to a question type
        logging.debug(f"Mapped question type: {question_type}") # Log the mapped question type

        prompt = build_prompt(None, None, question_type) # Build a prompt based on the question type
        if not prompt: # Check if the prompt is empty
            logging.error("Prompt generation failed or returned empty.") # Log an error message
            return None # Return None if the prompt is empty

        logging.debug(f"Generated prompt: {prompt}") # Log the generated prompt

        # Check if the API client is initialized properly.
        if not hasattr(client, 'chat'): # Check if the client has the 'chat' attribute
            logging.error("API client is not properly initialized.") # Log an error message
            return None # Return None if the client is not properly initialized

        # Helper function to call the API with retries
        def send_request_with_retries(retries_left): # Define the send_request_with_retries function with the retries_left parameter
            try:
                logging.debug(f"Sending request to OpenAI API. Retries left: {retries_left}") # Log the API request

                response = client.chat.completions.create( # Call the OpenAI API to generate the content
                    model="gpt-3.5-turbo", # Use the GPT-3.5-turbo model
                    messages=[ # Define the messages to send to the API
                        {"role": "system", "content": "You are a Python tutor."}, # Define the system message
                        {"role": "user", "content": prompt}, # Define the user message
                    ],
                    temperature=0.7, # Set the temperature to 0.7 for diversity
                    max_tokens=500 # Limit the token count for the response
                )

                logging.debug(f"Received API response: {response}") # Log the API response

                if not response or not response.choices: # Check if the response is empty or improperly formatted
                    logging.warning("API response is empty or improperly formatted.") # Log a warning message
                    raise ValueError("Invalid API response.") # Raise a ValueError

                return response.choices[0].message.content.strip() # Return the content from the API response

            except Exception as e: # Catch any exceptions
                logging.error(f"API request failed: {e}") # Log the error
                if retries_left > 0: # Check if there are retries left
                    return send_request_with_retries(retries_left - 1) # Retry the request
                else: # If no retries left
                    logging.error("Exceeded maximum retries for API request.") # Log an error message
                    return None # Return None

        # Call the helper function with retries
        question_text = send_request_with_retries(max_retries) # Send the request to the API with retries
        if not question_text: # Check if the question text is empty
            logging.error("Failed to generate a valid question after retries.") # Log an error message
            return None # Return None if the question text is empty

        logging.debug(f"Extracted question text: {question_text}") # Log the extracted question text

        question_data = parse_response(question_text, question_type) # Parse the response to extract the question data
        if not question_data:
            logging.warning("Invalid question format. Retrying...") # Log a warning message

            # If retries are exhausted, return None.
            if max_retries > 0: # Check if there are retries left
                return generate_python_question(choice, max_retries - 1) # Retry generating the question
            else: # If no retries left
                logging.error("Max retries exhausted. Unable to generate a valid question.") # Log an error message
                return None # Return None

        logging.debug(f"Parsed question data: {question_data}") # Log the parsed question data

        if "question" in question_data: # Check if the question data contains the 'question' key
            logging.debug("Successfully generated question.") # Log a success message
            return question_data # Return the question data
        else: # If the question data is missing the 'question' key 
            logging.error("Parsed question data is missing the 'question' key.")    # Log an error message
            return None # Return None

    except Exception as e: # Catch any exceptions
        logging.error(f"Error generating Python question: {e}") # Log the error
        return None # Return None

# Define the build_prompt function
def build_prompt(chapter, lesson, question_type):
    """Generate a prompt based on the given question type, chapter, and lesson.""" 
    
    # Retrieve the chapter and lesson titles with fallback values.
    chapter_title = chapters.get(chapter, {}).get('title', "General Python Knowledge") # Retrieve the chapter title with a fallback value
    lesson_title = chapters.get(chapter, {}).get('lessons', {}).get(lesson, {}).get('title', "Fundamental Concepts") # Retrieve the lesson title with a fallback value

    logging.debug(f"Building prompt with chapter: {chapter_title}, lesson: {lesson_title}, question type: {question_type}") # Log the prompt building process

    if question_type == "multiple_choice": # Check if the question type is 'multiple_choice'
        prompt = ( # Define the prompt string
            f"### MULTIPLE CHOICE QUESTION\n" # Include the question type in the prompt
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n\n" # Include the chapter and lesson titles in the prompt
            f"Question:\n" # Include the question section in the prompt
            f"[Insert question text here]\n\n" # Include a placeholder for the question text
            f"Options:\n" # Include the options section in the prompt
            f"A) [Option A]\n" # Include the option A placeholder
            f"B) [Option B]\n" # Include the option B placeholder
            f"C) [Option C]\n"  # Include the option C placeholder
            f"D) [Option D]\n\n" # Include the option D placeholder
            f"Correct Answer: [Correct Option Letter]" # Include the correct answer placeholder
        ) 

    elif question_type == "true_false": # Check if the question type is 'true_false'
        prompt = ( # Define the prompt string
            f"### TRUE/FALSE QUESTION\n"    # Include the question type in the prompt
            f"Chapter: {chapter_title}\n"  # Include the chapter title in the prompt    
            f"Lesson: {lesson_title}\n\n" # Include the lesson title in the prompt
            f"Question:\n" # Include the question section in the prompt
            f"[Insert question text here]\n\n" # Include a placeholder for the question text
            f"Correct Answer: [True/False]" # Include the correct answer placeholder
        )

    elif question_type == "fill_in_the_blank":  # Check if the question type is 'fill_in_the_blank'
        prompt = ( # Define the prompt string
            f"### FILL IN THE BLANK QUESTION\n" # Include the question type in the prompt
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n\n" # Include the lesson title in the prompt
            f"Question:\n" # Include the question section in the prompt
            f"[Insert question text with '________']\n\n" # Include a placeholder for the question text
            f"Correct Answer: [Insert correct answer]" # Include the correct answer placeholder
        )

    elif question_type == "scenario": # Check if the question type is 'scenario'
        prompt = ( # Define the prompt string
            f"### SCENARIO QUESTION\n" # Include the question type in the prompt
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n\n" # Include the lesson title in the prompt
            f"Scenario:\n" # Include the scenario section in the prompt
            f"[Describe the scenario. Ensure the correct answer is explained in a complete sentence.]\n\n" # Include a placeholder for the scenario description
            f"Correct Answer:\n" # Include the correct answer section in the prompt
            f"[Provide a descriptive, multi-word answer.]" # Include a placeholder for the correct answer
        )

    elif question_type == "write_code": # Check if the question type is 'write_code'
        prompt = ( # Define the prompt string
            f"### CODE CHALLENGE\n" # Include the question type in the prompt
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n\n" # Include the lesson title in the prompt
            f"Task:\n" # Include the task section in the prompt
            f"Write a Python function to solve a given problem. " # Include the task description
            f"For example, create a function that calculates the factorial of a number.\n\n" # Include an example task
            f"Sample Solution:\n" # Include the sample solution section in the prompt
            f"```python\n" # Start the code block
            f"def factorial(n):\n" # Include a sample solution
            f"    if n == 0:\n" # Include a sample solution
            f"        return 1\n" # Include a sample solution
            f"    return n * factorial(n - 1)\n" # Include a sample solution
            f"```\n" # End the code block
            f"Now, generate a new coding challenge with a task description and sample solution." # Include the task description
        )
    else: # If the question type is unknown
        raise ValueError(f"Unknown question type: {question_type}") # Raise a ValueError with the unknown question type
 
    logging.debug(f"Generated prompt: {prompt}") # Log the generated prompt
    return prompt # Return the generated prompt

# Define the parse_response function
def parse_response(response_text, question_type): # Define the parse_response function with the response_text and question_type parameters
    """Parse the response based on question type with detailed logging.""" 
    try: # Try block to handle exceptions
        logging.debug("Raw response (line-by-line):") # Log the raw response
        lines = response_text.split('\n') # Split the response text into lines
        for i, line in enumerate(lines): # Iterate over the lines
            logging.debug(f"Line {i + 1}: {repr(line)}") # Log the line number and content

        # Handle different question types
        if question_type == "multiple_choice": # Check if the question type is 'multiple_choice'
            return parse_multiple_choice(lines) # Parse the multiple-choice question
        elif question_type == "fill_in_the_blank": # Check if the question type is 'fill_in_the_blank'
            return parse_fill_in_the_blank(lines) # Parse the fill-in-the-blank question
        elif question_type == "write_code": # Check if the question type is 'write_code'
            return parse_code_challenge(lines) # Parse the code challenge question
        elif question_type == "true_false": # Check if the question type is 'true_false'
            return parse_true_false(lines) # Parse the true/false question
        elif question_type == "scenario": # Check if the question type is 'scenario'
            return parse_scenario(lines) # Parse the scenario-based question
        else: # If the question type is unknown
            logging.warning(f"Unknown question type: {question_type}") # Log a warning message
            return None # Return None
    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing response: {e}") # Log the error
        return None # Return None

# Define the parse_true_false function
def parse_true_false(lines): # Define the parse_true_false function with the lines parameter
    """Parse and validate True/False questions with improved handling."""
    try: # Try block to handle exceptions
        # Step 1: Clean and filter out empty lines 
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines
        logging.debug(f"Cleaned lines: {cleaned_lines}") # Log the cleaned lines

        # Step 2: Extract the question
        question = None # Initialize the question variable as None
        for line in cleaned_lines: # Iterate over the cleaned lines
            # Skip headers like '### TRUE/FALSE QUESTION'
            if line.startswith("###") or "Chapter" in line or "Lesson" in line: # Check if the line contains headers
                continue # Skip the header lines

            # If we find a valid question line, set it as the question
            if line.lower().startswith("question:"): # Check if the line starts with 'Question:'
                question = line.split(":", 1)[-1].strip()  # Extract after 'Question:'
            elif not question: # If the question is not set
                question = line  # Fallback: take the first non-header line as the question

        if not question: # Check if the question is empty
            raise ValueError("Failed to extract a valid question.") # Raise a ValueError

        # Step 3: Extract the correct answer from the last line
        answer_line = cleaned_lines[-1].lower() # Extract the last line
        correct_answer = "true" if "true" in answer_line else "false" # Extract the correct answer

        # Step 4: Return the structured question data
        return { # Return the structured question data
            "type": "true_false", # Include the question type
            "question": question, # Include the question text
            "correct_answer": correct_answer, # Include the correct answer
        } 
    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing True/False question: {e}") # Log the error
        return None # Return None

# Define the parse_scenario function
def parse_scenario(lines): # Define the parse_scenario function with the lines parameter
    """Parse scenario-based questions and extract the scenario and correct answer."""
    try:
        logging.debug("Parsing Scenario Question:") # Log the parsing process

        scenario = [] # Initialize an empty list to store the scenario
        answer = [] # Initialize an empty list to store the answer
        current_section = None # Initialize the current_section variable as None

        for line in lines: # Iterate over the lines
            stripped = line.strip().lower() # Strip and convert to lowercase

            if not stripped: # Check if the line is empty
                continue # Skip empty lines

            if re.match(r"(###\s*)?scenario\s*:", stripped): # Check if the line contains 'Scenario:'
                current_section = "scenario" # Set the current section to 'scenario'
                continue # Move to the next line
            elif re.match(r"(###\s*)?correct\s*answer\s*:", stripped): # Check if the line contains 'Correct Answer:'
                current_section = "answer" # Set the current section to 'answer'
                continue # Move to the next line

            if current_section == "scenario": # Check if the current section is 'scenario'
                scenario.append(line.strip()) # Append the line to the scenario list
            elif current_section == "answer": # Check if the current section is 'answer'
                answer.append(line.strip()) # Append the line to the answer list
 
        scenario_text = " ".join(scenario).strip() # Join the scenario lines
        correct_answer = " ".join(answer).strip() # Join the answer lines

        if not scenario_text or not correct_answer: # Check if the scenario or answer text is empty
            raise ValueError("Incomplete scenario: Missing answer.") # Raise a ValueError

        logging.info(f"Extracted Scenario: {scenario_text}") # Log the extracted scenario
        logging.info(f"Extracted Answer: {correct_answer}") # Log the extracted answer

        return { # Return the structured question data
            "type": "scenario", # Include the question type
            "question": scenario_text, # Include the scenario text
            "correct_answer": correct_answer # Include the answer text
        }

    except Exception as e:  # Catch any exceptions
        logging.error(f"Error during scenario parsing: {e}") # Log the error
        return None # Return None

# Define the parse_multiple_choice function
def parse_multiple_choice(lines): # Define the parse_multiple_choice function with the lines parameter

    """Parse multiple-choice questions with improved handling."""
    try: # Try block to handle exceptions
        logging.debug("Parsing Multiple-Choice Question (line-by-line):") # Log the parsing process

        # Step 1: Clean each line and remove empty lines
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines
        logging.debug(f"Cleaned lines: {cleaned_lines}") # Log the cleaned lines

        # Step 2: Filter out headers and unnecessary symbols
        question_lines = [ # Filter out headers and unnecessary symbols
            re.sub(r'^[#*>\-]+\s?', '', line)  # Remove common markdown symbols
            for line in cleaned_lines  # Iterate over the cleaned lines
            if not re.match(r'^(chapter|lesson|multiple[- ]?choice.*)$', line, re.IGNORECASE) # Filter out headers
        ]
        logging.debug(f"Filtered lines: {question_lines}") # Log the filtered lines

        # Step 3: Initialize variables
        question = [] # Initialize an empty list to store the question
        options = {} # Store options as a dictionary
        correct_answer = None # Initialize the correct answer as None

        # Step 4: Extract the question, options, and correct answer
        for line in question_lines: # Iterate over the question lines
            # Detect options like 'A) Integer'
            option_match = re.match(r'^([A-Da-d])\)\s*(.*)', line) # Match the option pattern
            if option_match: # Check if the option pattern is matched
                label = option_match.group(1).upper() # Extract the option label
                option_text = option_match.group(2).strip() # Extract the option text
                options[label] = option_text  # Store as { 'A': 'Integer', ... }
                logging.debug(f"Option {label}: {option_text}") # Log the option
                continue  # Move to the next line

            # Detect the correct answer
            if "correct answer:" in line.lower(): # Check if the line contains 'Correct Answer:'
                match = re.search(r'correct answer:\s*([A-Da-d])', line, re.IGNORECASE) # Match the correct answer pattern
                if match: # Check if the correct answer pattern is matched
                    correct_answer = match.group(1).upper() # Extract the correct answer
                    logging.debug(f"Correct Answer: {correct_answer}") # Log the correct answer
                continue # Move to the next line
 
            # Collect question text
            question.append(line) # Append the line to the question list

        # Step 5: Validate parsed data
        question_text = "\n".join(question).strip() # Join the question lines
        if not question_text or not options or correct_answer is None: # Check if the question text, options, or correct answer is missing
            raise ValueError("Incomplete multiple-choice question.") # Raise a ValueError

        # Step 6: Return structured data
        return { # Return the structured question data
            "type": "multiple_choice", # Include the question type
            "question": question_text, # Include the question text
            "options": options,  # Now stored as a dictionary with labels
            "correct_answer": correct_answer, # Include the correct answer
        }

    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing multiple-choice question: {e}") # Log the error
        return None # Return None

# Define the parse_fill_in_the_blank function
def parse_fill_in_the_blank(lines): # Define the parse_fill_in_the_blank function with the lines parameter
    """Parse fill-in-the-blank questions and extract the correct answer.""" 
    try:
        # Step 1: Clean and filter lines
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines
        logging.debug(f"Cleaned lines: {cleaned_lines}") # Log the cleaned lines

        # Step 2: Extract the question line with a placeholder
        question_line = next( # Extract the question line with a placeholder
            (line for line in cleaned_lines if 'Insert' in line or '________' in line), # Find lines with placeholders
            None # Return None if no valid line found
        )

        if not question_line:   # If no valid question line found
            raise ValueError("No valid blank or placeholder found in the question.") # Raise a ValueError

        logging.debug(f"Extracted Question Line: {question_line}") # Log the extracted question line

        # Step 3: Validate if the blank is properly placed
        if (
            question_line.endswith('? ________') or  # Avoid if blank follows a question mark
            question_line.endswith('.') or           # Avoid if sentence ends with a period
            question_line == '________'              # Avoid if it's a lone blank
        ):
            logging.warning(f"Invalid placement of blank in question: {question_line}") # Log a warning message
            raise ValueError("Improperly formatted fill-in-the-blank question.") # Raise a ValueError

        # Step 4: Extract the correct answer
        answer_pattern = re.search(r'\(([^)]+)\)', question_line) # Extract the answer in parentheses
        correct_answer = answer_pattern.group(1).strip() if answer_pattern else None # Extract the correct answer

        # If no answer found in parentheses, look for "Correct Answer:" line
        if not correct_answer: # Check if the correct answer is missing
            answer_line = next( # Extract the correct answer line
                (line for line in cleaned_lines if line.lower().startswith("correct answer:")), # Find the line with 'Correct Answer:'
                None # Return None if no valid line found
            )
            if answer_line: # Check if the answer line is found
                correct_answer = answer_line.split(":", 1)[-1].strip() # Extract the correct answer

            if not correct_answer: # Check if the correct answer is still missing
                raise ValueError("No valid answer found in parentheses or 'Correct Answer:' line.") # Raise a ValueError

        logging.debug(f"Extracted Correct Answer: {correct_answer}") # Log the extracted correct answer

        # Step 5: Format the question with consistent blanks
        formatted_question = re.sub(r'(_{2,}|\[.*?\]|-{3,}|Insert answer)', '________', question_line).strip() # Format the question with consistent blanks
        formatted_question = re.sub(r'\s*\([^)]*\)', '', formatted_question).strip() # Remove any parentheses from the question
        logging.debug(f"Formatted Question (With '________'): {formatted_question}") # Log the formatted question

        # Step 6: Return the structured question data
        return { # Return the structured question data
            "type": "fill_in_the_blank", # Include the question type
            "question": formatted_question, # Include the formatted question
            "correct_answer": correct_answer, # Include the correct answer
        }

    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing fill-in-the-blank: {e}") # Log the error
        return None # Return None

# Define the parse_code_challenge function
def parse_code_challenge(lines):
    """Parse code challenges with clear task and solution extraction."""
    try: # Try block to handle exceptions
        logging.info(f"Parsing code challenge. Raw input: {lines}") # Log the parsing process

        task_lines = []  # Store task description
        solution_lines = []  # Store solution code

        in_solution_block = False  # Track whether inside solution block

        for line in lines: # Iterate over the lines
            stripped_line = line.strip() # Strip the line

            if stripped_line.startswith("```python"): # Check if the line starts with '```python'
                in_solution_block = True # Enter the solution block 
                continue    

            elif stripped_line == "```": # Check if the line contains '```'
                in_solution_block = False   # Exit the solution block
                continue 

            if in_solution_block: # Check if inside the solution block
                solution_lines.append(line) # Append the line to the solution block
            else: # If not inside the solution block
                task_lines.append(line) # Append the line to the task description

        # Join and clean lines
        task_text = "\n".join(task_lines).strip() # Join and clean the task lines
        correct_answer = "\n".join(solution_lines).strip() # Join and clean the solution lines

        if not task_text or not correct_answer: # Check if the task or solution is missing
            raise ValueError("Incomplete code challenge: Missing task or solution.") # Raise a ValueError

        logging.info(f"Extracted Task:\n{task_text}") # Log the extracted task
        logging.info(f"Extracted Solution:\n{correct_answer}") # Log the extracted solution

        # Return 'question' instead of 'task' for consistency with retry logic
        return {
            "type": "write_code", # Include the question type
            "question": task_text,  # Align with the retry logic
            "correct_answer": correct_answer   # Include the solution code
        }

    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing code challenge: {e}") # Log the error
        return None # Return None

# Define the generate_review_questions function
def generate_review_questions(progress, chapter):
    """Generate review questions for a specific chapter based on lesson complexities and mistakes."""
    questions = []
    lessons = chapters[chapter]['lessons']

    # Determine question counts per lesson
    lesson_question_counts = {}

    for lesson_num, lesson in lessons.items():
        if lesson_num == 8:
            continue  # Skip the review test lesson

        # Get the base question count from lesson complexity
        base_question_count = lesson.get('complexity', 1)

        # Check if the user made mistakes in this lesson
        mistake_exists = False
        try:
            with sqlite3.connect('progress.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    SELECT 1
                    FROM mistakes
                    WHERE user_id = ? AND chapter = ? AND lesson = ?
                    LIMIT 1
                    ''',
                    (progress.user_id, chapter, lesson_num)
                )
                mistake_exists = cursor.fetchone() is not None
        except sqlite3.Error as e:
            logging.error(f"Failed to retrieve mistakes from database: {e}")

        # If the user made any mistakes in this lesson, add one extra question
        if mistake_exists:
            total_question_count = base_question_count + 1
        else:
            total_question_count = base_question_count

        lesson_question_counts[lesson_num] = total_question_count

    # Now, generate questions for each lesson
    for lesson_num, question_count in lesson_question_counts.items():
        # Retrieve the lesson content from the database
        lesson_content = generate_lesson_content(progress, chapter, lesson_num)

        # Generate questions for this lesson
        generated_questions = generate_questions_from_content(
            chapter, lesson_num, lesson_content, question_count=question_count
        )
        questions.extend(generated_questions)

    # Shuffle the questions
    random.shuffle(questions)
    return questions


# Define the fill_missing_questions function
def fill_missing_questions(existing_questions, chapter, total_needed): # Define the fill_missing_questions function with the existing_questions, chapter, and total_needed parameters
    """Fill in any missing questions to meet the required count.""" 
    while len(existing_questions) < total_needed: # Loop until we have enough questions
        lesson = random.randint(1, 7) # Randomly select a lesson
        lesson_content = generate_lesson_content(chapter, lesson) # Generate the lesson content
        new_question = generate_questions_from_content(chapter, lesson, lesson_content, 1) # Generate a new question
        existing_questions.extend(new_question) # Extend the existing questions list
    return existing_questions # Return the existing questions

# Define the generate_cumulative_review function
def generate_cumulative_review(progress): # Define the generate_cumulative_review function with the progress parameter

    """Generate the cumulative review with 100 questions plus mistakes from chapter reviews."""
    questions = [] # Initialize an empty list to store the questions

    # Collect all mistakes from chapter reviews
    for chapter in range(1, 21): # Iterate over the chapters
        mistake_count = progress.cumulative_review_mistakes.get(chapter, 0) # Retrieve the mistake count
        if mistake_count > 0: # Check if there are mistakes
            lesson_content = generate_lesson_content(chapter, 8)  # Review content
            questions.extend(generate_questions_from_content(lesson_content, mistake_count))

    # Add random questions from all chapters until we reach 100 total questions
    while len(questions) < 100: # Loop until we have 100 questions
        chapter = random.randint(1, 20) # Randomly select a chapter
        lesson = random.randint(1, 7) # Randomly select a lesson
        lesson_content = generate_lesson_content(chapter, lesson) # Generate the lesson content
        questions.extend(generate_questions_from_content(lesson_content, 1)) # Generate questions based on the lesson content

    random.shuffle(questions)  # Shuffle the questions for randomness
    return questions[:100] # Return the first 100 questions

# Define the generate_questions_from_content function
def validate_answer_with_gpt(question_data, user_response=None, user_code=None, user_output=None): # Define the validate_answer_with_gpt function with the question_data, user_response, user_code, and user_output parameters
    """Use GPT to validate both coding challenges and scenario-based answers."""
    try: # Try block to handle exceptions 
        logging.debug("Sending validation request to GPT.") # Log the validation request

        # Ensure question_data is valid
        if not isinstance(question_data, dict): # Check if the question_data is not a dictionary
            raise ValueError("question_data must be a dictionary.") # Raise a ValueError

        question_type = question_data.get('type', 'scenario') # Retrieve the question type

        # Construct the prompt based on question type
        if question_type == "write_code":  # Check if the question type is 'write_code'
            validation_prompt = ( # Define the validation prompt
                f"You are a Python tutor. A student has provided a solution to the following coding challenge.\n\n" # Include the tutor role
                f"### Coding Challenge\n{question_data.get('question', 'No question provided.')}\n\n" # Include the question text
                f"Sample Solution:\n{question_data.get('solution', 'No solution provided.')}\n\n" # Include the sample solution
                f"Student's Code:\n{user_code or 'No code provided.'}\n\n" # Include the student's code
                f"Student's Code Output:\n{user_output or 'No output provided.'}\n" # Include the student's code output
                f"Is the student's solution correct? Start your response with 'Correct' or 'Incorrect'." # Include the validation instructions
            ) 
        elif question_type == "scenario": # Check if the question type is 'scenario'
            validation_prompt = ( # Define the validation prompt
                f"You are a Python tutor. A student has responded to the following scenario-based question.\n\n" # Include the tutor role
                f"### Scenario Question\n{question_data.get('question', 'No question provided.')}\n\n" # Include the question text
                f"Expected Answer:\n{question_data.get('answer', 'No answer provided.')}\n\n" # Include the expected answer
                f"Student's Response:\n{user_response or 'No response provided.'}\n" # Include the student's response
                f"Is the student's response correct? Start your response with 'Correct' or 'Incorrect'." # Include the validation instructions
            )
        else: # If the question type is unknown
            raise ValueError(f"Unsupported question type: {question_type}") # Raise a ValueError for unsupported question types

        # Send the request to GPT
        response = client.chat.completions.create( # Call the OpenAI API to generate the content
            model="gpt-3.5-turbo", # Use the GPT-3.5-turbo model
            messages=[ # Define the messages to send to the API
                {"role": "system", "content": "You are a Python tutor."}, # Define the system message
                {"role": "user", "content": validation_prompt} # Define the user message
            ],
            temperature=0.7, # Set the temperature to 0.7 for diversity
            max_tokens=150 # Limit the token count for the response
        )

        gpt_response = response.choices[0].message.content.strip() # Extract the content from the API response
        logging.info(f"GPT Validation Response: {gpt_response}") # Log the GPT validation response

        # Prioritize "Incorrect" over "Correct" to avoid misinterpretation
        if "incorrect" in gpt_response.lower(): # Check if the response contains 'incorrect'
            logging.info("Validation marked as Incorrect.") # Log the validation as incorrect
            return False, gpt_response  # Invalid response
        elif "correct" in gpt_response.lower():     # Check if the response contains 'correct'
            logging.info("Validation marked as Correct.") # Log the validation as correct
            return True, gpt_response  # Valid response
        else: # If neither 'correct' nor 'incorrect' is found
            logging.warning("Unexpected GPT response format.") # Log a warning message
            return False, "Unexpected response from GPT. Please review the feedback." # Return an unexpected response message

    except ValueError as ve: # Catch ValueError exceptions
        logging.error(f"ValueError: {ve}") # Log the ValueError
        return False, str(ve)   # Return False and the error message

    except Exception as e:  # Catch any exceptions
        logging.error(f"Error during GPT validation: {e}") # Log the error
        return False, "An error occurred during validation." # Return False and an error message
