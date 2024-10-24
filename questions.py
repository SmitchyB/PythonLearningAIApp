
from dotenv import load_dotenv  # Import the load_dotenv function from the dotenv module
import os # Import the os module
import random   # Import the random module
from colorama import Fore   # Import the Fore class from the colorama module
from config import chapters # Import the chapters dictionary from the config module
from openai import OpenAI  # Import the OpenAI class from the openai module
import logging # Import the logging module for logging messages
from fuzzywuzzy import fuzz # Import the fuzz function from the fuzzywuzzy module for string similarity
import re # Import the re module for regular expressions
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
                max_tokens=400 # Limit the token count for the question
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
def determine_question_types(title):
    """Determine allowed question types based on the lesson title."""
    if any(keyword in title for keyword in ["introduction", "overview", "getting started", 
                                            "what is", "setting up", "first", "installing"]):
        # No code challenges allowed for introductory lessons
        return ["multiple_choice", "true_false", "fill_in_the_blank", "scenario"]
    elif any(keyword in title for keyword in ["review", "test"]):
        # Review lessons can have all types except write_code
        return ["multiple_choice", "true_false", "fill_in_the_blank", "scenario"]
    else:
        # For other advanced lessons, all question types are allowed
        return ["multiple_choice", "true_false", "fill_in_the_blank", "scenario", "write_code"]

def map_choice_to_type(choice):
    logging.debug(f"map_choice_to_type received choice: {choice}")
    return {
        '1': 'multiple_choice',
        '2': 'true_false',
        '3': 'fill_in_the_blank',
        '4': 'write_code',
        '5': 'scenario'
    }.get(choice, 'multiple_choice')

# In questions.py
def generate_python_question(choice, max_retries=2):
    """Generate a Python-related question for testing purposes with retry support."""
    try:
        logging.debug("Starting generate_python_question function.")

        question_type = map_choice_to_type(choice)
        logging.debug(f"Mapped question type: {question_type}")

        prompt = build_prompt(None, None, question_type)
        if not prompt:
            logging.error("Prompt generation failed or returned empty.")
            return None

        logging.debug(f"Generated prompt: {prompt}")

        # Check if the API client is initialized properly.
        if not hasattr(client, 'chat'):
            logging.error("API client is not properly initialized.")
            return None

        # Helper function to call the API with retries
        def send_request_with_retries(retries_left):
            try:
                logging.debug(f"Sending request to OpenAI API. Retries left: {retries_left}")

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a Python tutor."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=500
                )

                logging.debug(f"Received API response: {response}")

                if not response or not response.choices:
                    logging.warning("API response is empty or improperly formatted.")
                    raise ValueError("Invalid API response.")

                return response.choices[0].message.content.strip()

            except Exception as e:
                logging.error(f"API request failed: {e}")
                if retries_left > 0:
                    return send_request_with_retries(retries_left - 1)
                else:
                    logging.error("Exceeded maximum retries for API request.")
                    return None

        # Call the helper function with retries
        question_text = send_request_with_retries(max_retries)
        if not question_text:
            logging.error("Failed to generate a valid question after retries.")
            return None

        logging.debug(f"Extracted question text: {question_text}")

        question_data = parse_response(question_text, question_type)
        if not question_data:
            logging.warning("Invalid question format. Retrying...")

            # If retries are exhausted, return None.
            if max_retries > 0:
                return generate_python_question(choice, max_retries - 1)
            else:
                logging.error("Max retries exhausted. Unable to generate a valid question.")
                return None

        logging.debug(f"Parsed question data: {question_data}")

        if "question" in question_data:
            logging.debug("Successfully generated question.")
            return question_data
        else:
            logging.error("Parsed question data is missing the 'question' key.")
            return None

    except Exception as e:
        logging.error(f"Error generating Python question: {e}")
        return None



# Define the build_prompt function
def build_prompt(chapter, lesson, question_type):
    """Generate a prompt based on the given question type, chapter, and lesson."""
    
    # Retrieve the chapter and lesson titles with fallback values.
    chapter_title = chapters.get(chapter, {}).get('title', "General Python Knowledge")
    lesson_title = chapters.get(chapter, {}).get('lessons', {}).get(lesson, {}).get('title', "Fundamental Concepts")

    logging.debug(f"Building prompt with chapter: {chapter_title}, lesson: {lesson_title}, question type: {question_type}")

    if question_type == "multiple_choice":
        prompt = (
            f"### MULTIPLE CHOICE QUESTION\n"
            f"Chapter: {chapter_title}\n"
            f"Lesson: {lesson_title}\n\n"
            f"Question:\n"
            f"[Insert question text here]\n\n"
            f"Options:\n"
            f"A) [Option A]\n"
            f"B) [Option B]\n"
            f"C) [Option C]\n"
            f"D) [Option D]\n\n"
            f"Correct Answer: [Correct Option Letter]"
        )

    elif question_type == "true_false":
        prompt = (
            f"### TRUE/FALSE QUESTION\n"
            f"Chapter: {chapter_title}\n"
            f"Lesson: {lesson_title}\n\n"
            f"Question:\n"
            f"[Insert question text here]\n\n"
            f"Correct Answer: [True/False]"
        )

    elif question_type == "fill_in_the_blank":
        prompt = (
            f"### FILL IN THE BLANK QUESTION\n"
            f"Chapter: {chapter_title}\n"
            f"Lesson: {lesson_title}\n\n"
            f"Question:\n"
            f"[Insert question text with '________']\n\n"
            f"Correct Answer: [Insert correct answer]"
        )

    elif question_type == "scenario":
        prompt = (
            f"### SCENARIO QUESTION\n"
            f"Chapter: {chapter_title}\n"
            f"Lesson: {lesson_title}\n\n"
            f"Scenario:\n"
            f"[Describe the scenario. Ensure the correct answer is explained in a complete sentence.]\n\n"
            f"Correct Answer:\n"
            f"[Provide a descriptive, multi-word answer.]"
        )

    elif question_type == "write_code":
        prompt = (
            f"### CODE CHALLENGE\n"
            f"Chapter: {chapter_title}\n"
            f"Lesson: {lesson_title}\n\n"
            f"Task:\n"
            f"Write a Python function to solve a given problem. "
            f"For example, create a function that calculates the factorial of a number.\n\n"
            f"Sample Solution:\n"
            f"```python\n"
            f"def factorial(n):\n"
            f"    if n == 0:\n"
            f"        return 1\n"
            f"    return n * factorial(n - 1)\n"
            f"```\n"
            f"Now, generate a new coding challenge with a task description and sample solution."
        )
    else:
        raise ValueError(f"Unknown question type: {question_type}")

    logging.debug(f"Generated prompt: {prompt}")
    return prompt
# Define the parse_response function
def parse_response(response_text, question_type):
    """Parse the response based on question type with detailed logging."""
    try:
        logging.debug("Raw response (line-by-line):")
        lines = response_text.split('\n')
        for i, line in enumerate(lines):
            logging.debug(f"Line {i + 1}: {repr(line)}")

        # Handle different question types
        if question_type == "multiple_choice":
            return parse_multiple_choice(lines)
        elif question_type == "fill_in_the_blank":
            return parse_fill_in_the_blank(lines)
        elif question_type == "write_code":
            return parse_code_challenge(lines)
        elif question_type == "true_false":
            return parse_true_false(lines)
        elif question_type == "scenario":
            return parse_scenario(lines)
        else:
            logging.warning(f"Unknown question type: {question_type}")
            return None
    except Exception as e:
        logging.error(f"Error parsing response: {e}")
        return None

# Define the parse_true_false function
def parse_true_false(lines):
    """Parse and validate True/False questions with improved handling."""
    try:
        # Step 1: Clean and filter out empty lines
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        logging.debug(f"Cleaned lines: {cleaned_lines}")

        # Step 2: Extract the question
        question = None
        for line in cleaned_lines:
            # Skip headers like '### TRUE/FALSE QUESTION'
            if line.startswith("###") or "Chapter" in line or "Lesson" in line:
                continue

            # If we find a valid question line, set it as the question
            if line.lower().startswith("question:"):
                question = line.split(":", 1)[-1].strip()  # Extract after 'Question:'
            elif not question:
                question = line  # Fallback: take the first non-header line as the question

        if not question:
            raise ValueError("Failed to extract a valid question.")

        # Step 3: Extract the correct answer from the last line
        answer_line = cleaned_lines[-1].lower()
        correct_answer = "true" if "true" in answer_line else "false"

        # Step 4: Return the structured question data
        return {
            "type": "true_false",
            "question": question,
            "correct_answer": correct_answer,
        }
    except Exception as e:
        logging.error(f"Error parsing True/False question: {e}")
        return None

# Define the parse_scenario function
def parse_scenario(lines):
    """Parse scenario-based questions and extract the scenario and correct answer."""
    try:
        logging.debug("Parsing Scenario Question:")

        scenario = []
        answer = []
        current_section = None

        for line in lines:
            stripped = line.strip().lower()

            if not stripped:
                continue

            if re.match(r"(###\s*)?scenario\s*:", stripped):
                current_section = "scenario"
                continue
            elif re.match(r"(###\s*)?correct\s*answer\s*:", stripped):
                current_section = "answer"
                continue

            if current_section == "scenario":
                scenario.append(line.strip())
            elif current_section == "answer":
                answer.append(line.strip())

        scenario_text = " ".join(scenario).strip()
        answer_text = " ".join(answer).strip()

        if not scenario_text or not answer_text:
            raise ValueError("Incomplete scenario: Missing answer.")

        logging.info(f"Extracted Scenario: {scenario_text}")
        logging.info(f"Extracted Answer: {answer_text}")

        return {
            "type": "scenario",
            "question": scenario_text,
            "answer": answer_text
        }

    except Exception as e:
        logging.error(f"Error during scenario parsing: {e}")
        return None

# Define the parse_multiple_choice function
def parse_multiple_choice(lines):

    """Parse multiple-choice questions with improved handling."""
    try:
        logging.debug("Parsing Multiple-Choice Question (line-by-line):")

        # Step 1: Clean each line and remove empty lines
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        logging.debug(f"Cleaned lines: {cleaned_lines}")

        # Step 2: Filter out headers and unnecessary symbols
        question_lines = [
            re.sub(r'^[#*>\-]+\s?', '', line) 
            for line in cleaned_lines 
            if not re.match(r'^(chapter|lesson|multiple[- ]?choice.*)$', line, re.IGNORECASE)
        ]
        logging.debug(f"Filtered lines: {question_lines}")

        # Step 3: Initialize variables
        question = []
        options = {} # Store options as a dictionary
        correct_answer = None

        # Step 4: Extract the question, options, and correct answer
        for line in question_lines:
            # Detect options like 'A) Integer'
            option_match = re.match(r'^([A-Da-d])\)\s*(.*)', line)
            if option_match:
                label = option_match.group(1).upper() # Extract the option label
                option_text = option_match.group(2).strip() # Extract the option text
                options[label] = option_text  # Store as { 'A': 'Integer', ... }
                logging.debug(f"Option {label}: {option_text}")
                continue  # Move to the next line

            # Detect the correct answer
            if "correct answer:" in line.lower():
                match = re.search(r'correct answer:\s*([A-Da-d])', line, re.IGNORECASE)
                if match:
                    correct_answer = match.group(1).upper()
                    logging.debug(f"Correct Answer: {correct_answer}")
                continue

            # Collect question text
            question.append(line)

        # Step 5: Validate parsed data
        question_text = "\n".join(question).strip()
        if not question_text or not options or correct_answer is None:
            raise ValueError("Incomplete multiple-choice question.")

        # Step 6: Return structured data
        return {
            "type": "multiple_choice",
            "question": question_text,
            "options": options,  # Now stored as a dictionary with labels
            "correct_answer": correct_answer,
        }

    except Exception as e:
        logging.error(f"Error parsing multiple-choice question: {e}")
        return None

# Define the parse_fill_in_the_blank function
def parse_fill_in_the_blank(lines):
    """Parse fill-in-the-blank questions and extract the correct answer."""
    try:
        # Step 1: Clean and filter lines
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        logging.debug(f"Cleaned lines: {cleaned_lines}")

        # Step 2: Extract the question text with a placeholder
        question_line = next(
            (line for line in cleaned_lines if 'Insert' in line or '________' in line),
            None
        )

        if not question_line:
            raise ValueError("No valid blank or placeholder found in the question.")

        logging.debug(f"Extracted Question Line: {question_line}")

        # Step 3: Extract the correct answer
        answer_pattern = re.search(r'\(([^)]+)\)', question_line)
        correct_answer = answer_pattern.group(1).strip() if answer_pattern else None

        # If no answer found in parentheses, look for "Correct Answer:" line
        if not correct_answer:
            answer_line = next(
                (line for line in cleaned_lines if line.lower().startswith("correct answer:")),
                None
            )
            if answer_line:
                correct_answer = answer_line.split(":", 1)[-1].strip()

            if not correct_answer:
                raise ValueError("No valid answer found in parentheses or 'Correct Answer:' line.")

        logging.debug(f"Extracted Correct Answer: {correct_answer}")

        # Step 4: Format the question with consistent blanks
        formatted_question = re.sub(r'(_{2,}|\[.*?\]|-{3,}|Insert answer)', '________', question_line).strip()
        formatted_question = re.sub(r'\s*\([^)]*\)', '', formatted_question).strip()
        logging.debug(f"Formatted Question (With '________'): {formatted_question}")

        # Step 5: Return the structured question data
        return {
            "type": "fill_in_the_blank",
            "question": formatted_question,
            "correct_answer": correct_answer,
        }

    except Exception as e:
        logging.error(f"Error parsing fill-in-the-blank: {e}")
        return None
# Define the parse_code_challenge function
def parse_code_challenge(lines):
    """Parse code challenges with clear task and solution extraction."""
    try:
        logging.info(f"Parsing code challenge. Raw input: {lines}")

        task_lines = []  # Store task description
        solution_lines = []  # Store solution code

        in_solution_block = False  # Track whether inside solution block

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("```python"):
                in_solution_block = True
                continue

            elif stripped_line == "```":
                in_solution_block = False
                continue

            if in_solution_block:
                solution_lines.append(line)
            else:
                task_lines.append(line)

        # Join and clean lines
        task_text = "\n".join(task_lines).strip()
        solution_code = "\n".join(solution_lines).strip()

        if not task_text or not solution_code:
            raise ValueError("Incomplete code challenge: Missing task or solution.")

        logging.info(f"Extracted Task:\n{task_text}")
        logging.info(f"Extracted Solution:\n{solution_code}")

        # Return 'question' instead of 'task' for consistency with retry logic
        return {
            "type": "write_code",
            "question": task_text,  # Align with the retry logic
            "solution": solution_code
        }

    except Exception as e:
        logging.error(f"Error parsing code challenge: {e}")
        return None




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

def validate_answer_with_gpt(question_data, user_code=None, user_output=None):
    """Use GPT to validate both coding challenges and scenario-based answers."""
    try:
        logging.debug("Sending validation request to GPT.")

        # Construct the prompt based on the question type
        validation_prompt = (
            f"You are a Python tutor. A student has provided a solution to the following coding challenge.\n\n"
            f"### Coding Challenge\n{question_data['question']}\n\n"
            f"Sample Solution:\n{question_data['solution']}\n\n"
            f"Student's Code:\n{user_code}\n\n"
            f"Student's Code Output:\n{user_output}\n"
            f"Is the student's solution correct? Respond only with 'Correct' or 'Incorrect' at the beginning, followed by any feedback."
        )

        # Send the prompt to GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Python tutor."},
                {"role": "user", "content": validation_prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )

        # Extract the GPT response
        gpt_response = response.choices[0].message.content.strip()
        logging.info(f"GPT Validation Response: {gpt_response}")

        # Determine correctness based on the first word
        if gpt_response.lower().startswith("correct"):
            return True, gpt_response  # Correct answer with feedback
        else:
            return False, gpt_response  # Incorrect answer with feedback

    except Exception as e:
        logging.error(f"Error during GPT validation: {e}")
        return False, "An error occurred during validation."