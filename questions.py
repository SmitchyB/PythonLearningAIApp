
from dotenv import load_dotenv  # Import the load_dotenv function from the dotenv module
import os # Import the os module
import random   # Import the random module
from colorama import Fore   # Import the Fore class from the colorama module
from config import chapters # Import the chapters dictionary from the config module
from openai import OpenAI  # Import the OpenAI class from the openai module
import logging # Import the logging module for logging messages
from fuzzywuzzy import fuzz # Import the fuzz function from the fuzzywuzzy module for string similarity
from difflib import SequenceMatcher # Import the SequenceMatcher class from the difflib module for string similarity
import re # Import the re module for regular expressions

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
def generate_lesson_content(chapter, lesson): # Define the generate_lesson_content function with the chapter and lesson parameters
    """Generate more detailed lesson content using the OpenAI API."""
    try:
        # Fetch the chapter and lesson titles from the config
        chapter_title = chapters[chapter]["title"] # Retrieve the chapter title
        lesson_title = chapters[chapter]["lessons"][lesson]["title"] # Retrieve the lesson title

        # Build the prompt for generating the lesson content
        prompt = ( # Define the prompt string
            f"Provide an educational and engaging lesson on the following topic:\n" # Prompt gpt to provide an educational and engaging lesson
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n" # Include the lesson title in the prompt
            f"The lesson should include 2-3 paragraphs explaining the concept, examples, " # Include the requirements for the lesson content
            f"and key points to remember." # Include the requirements for the lesson content
        )

        # Call the OpenAI API to generate the content
        response = client.chat.completions.create( # Call the OpenAI API to generate the content
            model="gpt-3.5-turbo", # Use the GPT-3.5-turbo model
            messages=[{"role": "system", "content": "You are a Python tutor."}, # Define the system message
                      {"role": "user", "content": prompt}],
            temperature=0.7, # Set the temperature to 0.7 for diversity
            max_tokens=1000  # Allow for more content
        )

        # Return the generated content
        return response.choices[0].message.content.strip() # Return the generated content

    except Exception as e: # Catch any exceptions
        logging.error(f"Error generating lesson content: {e}") # Log the error
        return "Unable to generate lesson content." # Return a default message

# Define the generate_questions_from_content function
def generate_questions_from_content(chapter, lesson, content, question_count): # Define the generate_questions_from_content function with the chapter, lesson, content, and question_count parameters
    """Generate a set of questions based on the lesson content."""
    questions = [] # Initialize an empty list to store the questions
    allowed_types = determine_question_types(chapters[chapter]['lessons'][lesson]['title'].lower()) # Determine the allowed question types based on the lesson title

    while len(questions) < question_count: # Loop until the desired number of questions is generated
        try: # Try to generate a question
            question_type = random.choice(allowed_types) # Choose a random question type from the allowed types
            prompt = ( # Define the prompt for generating the question
                f"Based on the content below, generate a unique and non-repetitive {question_type} question:\n" # Prompt to generate a unique and non-repetitive question
                f"\"{content}\"\n" # Include the lesson content in the prompt
                f"Ensure it covers a specific aspect of the lesson and is distinct from other potential questions." # Include additional requirements for the question
                f"\n{build_prompt(chapter, lesson, question_type)}" # Include the specific prompt for the question type
            )

            response = client.chat.completions.create( # Call the OpenAI API to generate the question
                model="gpt-3.5-turbo", # Use the GPT-3.5-turbo model
                messages=[{"role": "system", "content": "You are a Python tutor."}, # Define the system message
                          {"role": "user", "content": prompt}],
                temperature=0.7, # Set the temperature to 0.7 for diversity
                max_tokens=300 # Limit the token count for the question
            )

            question_data = parse_response(response.choices[0].message.content.strip(), question_type) # Parse the generated question

            if question_data and "question" in question_data and is_question_unique(question_data["question"]): # Check if the question is unique
                questions.append(question_data) # Add the question to the list of questions
                store_question(question_data["question"]) # Store the question to avoid duplicates
            else: # If the question is not unique
                continue  # Try generating another question if a duplicate or invalid one is found.

        except Exception as e: # Catch any exceptions
            logging.error(f"Error generating question: {e}") # Log the error

    if len(questions) < question_count: # Check if not enough questions were generated
        logging.warning("Not enough unique questions generated.") # Log a warning message

    return questions # Return the list of generated questions

# Define the determine_question_types function
def determine_question_types(title): # Define the determine_question_types function with the title parameter
    """Determine allowed question types based on the lesson title."""
    if any(keyword in title for keyword in ["introduction", "overview", "getting started", "what is", "Setting Up", "First", "Installing"]): # Check if the title contains any introduction-related keywords
        return ["multiple_choice", "true_false", "fill_in_the_blank"] # Return the allowed question types for introduction lessons
    else: # For other lessons
        return ["multiple_choice", "true_false", "fill_in_the_blank", "scenario", "write_code"] # Return the allowed question types for other lessons

# Define the build_prompt function
def build_prompt(chapter, lesson, question_type): # Define the build_prompt function with the chapter, lesson, and question_type parameters
    chapter_title = chapters[chapter]['title'] # Retrieve the chapter title
    lesson_title = chapters[chapter]['lessons'][lesson]['title'] # Retrieve the lesson title

    if question_type == "multiple_choice": # Check if the question type is multiple choice
        return ( # Return the specific prompt for multiple-choice questions
            f"Create a multiple-choice question for:\n" # Prompt to create a multiple-choice question
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n" # Include the lesson title in the prompt
            f"Provide four answer options labeled A, B, C, D and indicate the correct one." # Include additional requirements for the question
        )
    elif question_type == "true_false": # Check if the question type is true/false
        return ( # Return the specific prompt for true/false questions
            f"Create a true/false question related to:\n" # Prompt to create a true/false question
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n" # Include the lesson title in the prompt
            f"Clearly state the correct answer (True or False)." # Include additional requirements for the question
        )
    elif question_type == "fill_in_the_blank": # Check if the question type is fill-in-the-blank
        return ( # Return the specific prompt for fill-in-the-blank questions
            f"Create a fill-in-the-blank question for:\n" # Prompt to create a fill-in-the-blank question
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n" # Include the lesson title in the prompt
            f"The question must contain '________'. Provide the correct answer in parentheses." # Include additional requirements for the question
        )
    elif question_type == "scenario": # Check if the question type is scenario-based
        return ( # Return the specific prompt for scenario-based questions
            f"Create a scenario-based question for:\n" # Prompt to create a scenario-based question
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n" # Include the lesson title in the prompt
            f"The scenario should present a problem, requiring the student to apply concepts from the lesson." # Include additional requirements for the question
        )
    elif question_type == "write_code": # Check if the question type is a code challenge
        return ( # Return the specific prompt for code challenges
            f"Create a coding challenge for:\n" # Prompt to create a coding challenge
            f"Chapter: {chapter_title}\n" # Include the chapter title in the prompt
            f"Lesson: {lesson_title}\n" # Include the lesson title in the prompt
            f"Provide a sample solution." # Include additional requirements for the question
        )

# Define the parse_response function
def parse_response(response_text, question_type): # Define the parse_response function with the response_text and question_type parameters
    """Parse the response based on question type."""
    try: # Try to parse the response
        lines = response_text.split('\n') # Split the response text into lines

        if question_type == "multiple_choice": # Check if the question type is multiple choice
            parsed = parse_multiple_choice(lines) # Parse the multiple-choice question
            if not parsed: # Check if the question was not parsed successfully
                logging.error(f"Malformed multiple-choice question: {response_text}") # Log an error message
            return parsed # Return the parsed question

        elif question_type == "fill_in_the_blank": # Check if the question type is fill-in-the-blank
            parsed = parse_fill_in_the_blank(lines) # Parse the fill-in-the-blank question
            if not parsed: # Check if the question was not parsed successfully
                logging.error(f"Malformed fill-in-the-blank question: {response_text}") # Log an error message
            return parsed # Return the parsed question

        elif question_type == "write_code": # Check if the question type is a code challenge
            return parse_code_challenge(lines) # Parse the code challenge

        elif question_type == "true_false": # Check if the question type is true/false
            return parse_true_false(lines) # Parse the true/false question

        elif question_type == "scenario": # Check if the question type is scenario-based
            return parse_scenario(lines) # Parse the scenario question

        else: # For unknown question types
            logging.warning(f"Unknown question type: {question_type}") # Log a warning message
            return None # Return None for unknown question types

    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing response: {e}") # Log the error
        return None # Return None if an error occurs

# Define the parse_true_false function
def parse_true_false(lines): # Define the parse_true_false function with the lines parameter
    """Parse and validate True/False questions with better handling for misplaced 'True or False:' prompts."""
    try: # Try to parse the true/false question
        # Step 1: Clean and filter out empty lines
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines

        # Step 2: Find the first line containing the actual question
        question = None # Initialize the question variable
        for line in cleaned_lines: # Iterate over the cleaned lines
            if line.lower().startswith("true or false:"): # Check if the line starts with 'True or False:'
                # Include the full content after 'True or False:'
                question = line.split(":", 1)[-1].strip() # Extract the question content
            elif not question: # If we missed the first pattern, take the first valid line as the question
                # If we missed the first pattern, take the first valid line as the question
                question = line # Set the question to the current line
        if not question: # If no valid question is found
            raise ValueError("Failed to extract a valid question.") # Raise a ValueError
        # Step 3: Extract the correct answer from the last line
        answer_line = cleaned_lines[-1].lower() # Get the last line in lowercase
        correct_answer = "true" if "true" in answer_line else "false" # Determine the correct answer based on the last line
        # Step 4: Return the structured question data
        return { # Return the structured question data
            "type": "true_false", # Set the question type to 'true_false'
            "question": question, # Set the question text
            "correct_answer": correct_answer, # Set the correct answer
        }
    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing True/False question: {e}") # Log the error
        return None # Return None if an error occurs

# Define the parse_scenario function
def parse_scenario(lines): # Define the parse_scenario function with the lines parameter
    """Parse scenario-based questions with detailed logging."""
    logging.info(f"Starting to parse scenario question. Raw input: {lines}") # Log the raw input for debugging
    try: # Try to parse the scenario question
        question = " ".join(line.strip() for line in lines if line.strip()) # Join the non-empty lines into a single question
        logging.info(f"Extracted scenario: {question}") # Log the extracted scenario

        return { # Return the structured question data
            "type": "scenario", # Set the question type to 'scenario'
            "question": question # Set the question text
        } # Return the structured question data
    except Exception as e: # Catch any exceptions
        logging.error(f"Error during scenario parsing: {e}") # Log the error
        return None # Return None if an error occurs

# Define the parse_multiple_choice function
def parse_multiple_choice(lines): # Define the parse_multiple_choice function with the lines parameter
    """Parse multiple-choice questions with improved handling of headers, spaces, and options.""" 
    try: # Try to parse the multiple-choice question
        # Step 1: Clean each line and remove empty lines
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines
        # Step 2: Filter out chapter/lesson headers and extra titles
        question_lines = [ # Filter out chapter/lesson headers and extra titles
            line for line in cleaned_lines  # Filter out chapter/lesson headers and extra titles
            if not re.match(r'^(chapter|lesson|multiple[- ]?choice question[:]?.*)$', line, re.IGNORECASE) # Filter out chapter/lesson headers and extra titles
        ]
        # Step 3: Extract the question (first valid line)
        question = None # Initialize the question variable
        for i, line in enumerate(question_lines): # Iterate over the question lines
            if not re.match(r'^[A-D]\)', line):  # Ensure it's not an option line
                question = line # Set the question to the current line
                question_lines = question_lines[i + 1:]  # Remaining lines are options and answers
                break # Break the loop after finding the question
        if not question: # If no valid question is found
            raise ValueError("Question not found.") # Raise a ValueError
        # Step 4: Extract answer options and correct answer
        options = [] # Initialize the options list
        correct_answer = None # Initialize the correct answer
        for line in question_lines: # Iterate over the question lines
            # Detect the correct answer in the line containing 'Correct Answer:'
            if "correct answer:" in line.lower(): # Check if the line contains 'Correct Answer:'
                match = re.search(r'correct answer:\s*([A-D])', line, re.IGNORECASE) # Extract the correct answer
                if match: # If a match is found
                    correct_answer = match.group(1).upper() # Set the correct answer
                break  # No need to process further after finding the correct answer
            # Extract valid options with labels (A, B, C, D)
            option_match = re.match(r'^[A-D]\)\s*(.*)', line) # Match the option line
            if option_match: # If a valid option is found
                options.append(option_match.group(1).strip()) # Add the option to the list
        # Step 5: Validate extracted components
        if not question or not options or correct_answer is None: # Check if any component is missing
            raise ValueError("Incomplete multiple-choice question.") # Raise a ValueError
        # Step 6: Return structured data
        return { # Return the structured question data
            "type": "multiple_choice", # Set the question type to 'multiple_choice'
            "question": question, # Set the question text
            "options": options, # Set the answer options
            "correct_answer": correct_answer, # Set the correct answer
        }
    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing multiple-choice question: {e}") # Log the error
        return None # Return None if an error occurs

# Define the parse_fill_in_the_blank function
def parse_fill_in_the_blank(lines): # Define the parse_fill_in_the_blank function with the lines parameter
    """Parse fill-in-the-blank questions, ensuring proper separation of question and answer."""
    try: # Try to parse the fill-in-the-blank question
        # Step 1: Clean and filter lines
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines
        logging.debug(f"Cleaned lines: {cleaned_lines}") # Log the cleaned lines for debugging

        # Step 2: Identify the question line and the answer (within parentheses)
        question_line = next( # Extract the question line
            (line for line in cleaned_lines if '________' in line or '_____' in line or '---' in line), # Find the line with '________' or '_____' or '---'
            cleaned_lines[0] # Default to the first line if not found
        )
        # Step 3: Extract the answer from the last line (inside parentheses)
        answer_match = re.search(r'\(([^)]+)\)', cleaned_lines[-1]) # Extract the answer from the last line
        if answer_match: # If an answer is found
            correct_answer = answer_match.group(1).strip()  # Extract the answer without parentheses
        else: # If no answer is found
            raise ValueError("No valid answer found.") # Raise a ValueError
        # Step 4: Remove the answer from the question line for display
        formatted_question = re.sub(r'\(([^)]+)\)', "", question_line).strip() # Remove the answer from the question line
        # Step 5: Replace blanks with '________' for consistency
        formatted_question = re.sub(r'(_{2,}|\[.*?\]|-{3,}|________+)', "________", formatted_question) # Replace blanks with '________'
        # Step 6: Return structured data
        return { # Return the structured question data
            "type": "fill_in_the_blank", # Set the question type to 'fill_in_the
            "question": formatted_question, # Set the question text
            "correct_answer": correct_answer, # Set the correct answer
        }
    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing fill-in-the-blank: {e}") # Log the error
        return None # Return None if an error occurs

# Define the parse_code_challenge function
def parse_code_challenge(lines): # Define the parse_code_challenge function with the lines parameter
    """Parse code challenges with separate question and solution handling.""" 
    logging.info(f"Parsing code challenge. Raw input: {lines}") # Log the raw input for debugging

    try: # Try to parse the code challenge 
        code_start = lines.index('```python') + 1 if '```python' in lines else 0    # Find the start of the code block
        code_end = lines.index('```', code_start) if '```' in lines[code_start:] else len(lines) # Find the end of the code block

        question_text = "\n".join(lines[:code_start]).strip() # Extract the question text
        solution_code = "\n".join(lines[code_start:code_end]).strip() # Extract the solution code

        logging.info(f"Extracted question: {question_text}") # Log the extracted question text
        logging.info(f"Extracted solution:\n{solution_code}") # Log the extracted solution code

        return { # Return the structured question data
            "type": "code_question", # Set the question type to 'code_question'
            "question": question_text, # Set the question text
            "solution": solution_code # Set the solution code
        }

    except Exception as e: # Catch any exceptions
        logging.error(f"Error parsing code challenge: {e}") # Log the error
        return None # Return None if an error occurs

# Define the generate_review_questions function
def generate_review_questions(progress, chapter): # Define the generate_review_questions function with the progress and chapter parameters
    """Generate review questions for a specific chapter."""
    questions = [] # Initialize an empty list to store the questions

    # Collect all missed lesson questions from this chapter
    missed_questions = progress.lesson_mistakes.get(chapter, {}) # Retrieve the missed questions for the chapter
    for lesson, mistake_count in missed_questions.items(): # Iterate over the missed questions
        if mistake_count > 0: # Check if there are missed questions
            lesson_content = generate_lesson_content(chapter, lesson) # Generate the lesson content
            questions.extend(generate_questions_from_content(lesson_content, mistake_count)) # Generate questions based on the lesson content

    # Add additional questions to fill up the review
    total_questions = chapters[chapter]['lessons'][8]['question_count'] # Retrieve the total question count for the review
    while len(questions) < total_questions: # Loop until enough questions are generated
        lesson = random.randint(1, 7)   # Randomly select a lesson
        lesson_content = generate_lesson_content(chapter, lesson) # Generate the lesson content
        new_questions = generate_questions_from_content(lesson_content, 1) # Generate new questions
        questions.extend(new_questions) # Add the new questions to the list

    random.shuffle(questions)  # Shuffle the questions for variety
    return questions[:total_questions] # Return the required number of questions

# Define the generate_cumulative_review function
def generate_cumulative_review(progress):
    """Generate the cumulative review with 100 questions plus mistakes from chapter reviews."""
    questions = []

    # Collect all mistakes from chapter reviews
    for chapter in range(1, 21):
        mistake_count = progress.cumulative_review_mistakes.get(chapter, 0)
        if mistake_count > 0:
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