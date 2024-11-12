from dotenv import load_dotenv  # Import the load_dotenv function from the dotenv module to load environment variables
import os # Import the os module for environment variables
import random   # Import the random module for random number generation
from colorama import Fore   # Import the Fore class from the colorama module for colored output
from config import chapters # Import the chapters dictionary from the config module for lesson details
from openai import OpenAI  # Import the OpenAI class from the openai module for interacting with the OpenAI API
from fuzzywuzzy import fuzz # Import the fuzz function from the fuzzywuzzy module for string similarity comparison
import re # Import the re module for regular expressions operations
import sqlite3 # Import the sqlite3 module for database operations 

# Load the environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") # Retrieve the OpenAI API key from the environment variables

client = OpenAI(api_key=api_key) # Create an OpenAI client with the API key

stored_questions = set()  # Store seen questions globally

# Function to determine if a question is unique based on a similarity threshold
def is_question_unique(new_question, threshold=70): # Set the default threshold to 70
    for stored_question in stored_questions: # Iterate over the stored questions
        similarity = fuzz.ratio(new_question.lower(), stored_question.lower()) # Calculate the similarity ratio
        if similarity > threshold: # Check if the similarity is above the threshold
            return False # Return False if the question is not unique
    return True # Return True if the question is unique

# Function to store the question in the global set
def store_question(question_text): # Define the store_question function with the question_text parameter
    stored_questions.add(question_text) # Add the question to the stored questions set

# Function to reset the similarity database 
def reset_similarity_database(): # Define the reset_similarity_database function
    global stored_questions # Access the global stored_questions set
    stored_questions.clear() # Clear the stored questions set

# Function to generate lesson content or retrieve it from the database
def generate_lesson_content(progress, chapter, lesson): # Define the generate_lesson_content function with the progress, chapter, and lesson parameters
    try: # Try block to handle exceptions
        # Check if the lesson content is already stored in the database
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute a query to retrieve the stored content
                '''
                SELECT content
                FROM lesson_content
                WHERE user_id = ? AND chapter = ? AND lesson = ?
                ''',
                (progress.user_id, chapter, lesson) # Provide the user ID, chapter, and lesson as parameters
            )
            row = cursor.fetchone() # Fetch the row from the database
            if row: # Check if the row is not empty
                return row[0]  # Return the stored content 

        chapter_title = chapters[chapter]["title"] # Retrieve the chapter title
        lesson_title = chapters[chapter]["lessons"][lesson]["title"] # Retrieve the lesson title

        prompt = ( # Define the prompt string
            f"Provide an educational and engaging lesson on the following topic:\n" # Include the prompt for the lesson content
            f"Chapter: {chapter_title}\n" # Include the chapter title
            f"Lesson: {lesson_title}\n" # Include the lesson title
            f"The lesson should include 2-3 paragraphs explaining the concept, examples, " # Include the requirements for the lesson content
            f"and key points to remember." # Include the requirements for the lesson content
        )

        response = client.chat.completions.create( # Call the OpenAI API to generate the lesson content
            model="gpt-3.5-turbo", # Use the GPT-3.5-turbo model
            messages=[{"role": "system", "content": "You are a Python tutor."}, # Define the system message
                      {"role": "user", "content": prompt}], # Define the user message
            temperature=0.7, # Set the temperature to 0.7 
            max_tokens=1000 # Limit the token count for the response
        )

        lesson_content = response.choices[0].message.content.strip() # Extract the content from the API response

        # Store the generated content in the database
        with sqlite3.connect('progress.db') as conn: # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute a query to store the generated content
                '''
                INSERT INTO lesson_content (user_id, chapter, lesson, content) 
                VALUES (?, ?, ?, ?)
                ''',
                (progress.user_id, chapter, lesson, lesson_content) # Provide the user ID, chapter, lesson, and content as parameters
            ) 
            conn.commit() # Commit the transaction

        return lesson_content # Return the generated lesson content

    except Exception as e: # Catch any exceptions
        return "Unable to retrieve or generate lesson content." # Return a default message

# Function to generate questions based on the lesson content
def generate_questions_from_content(chapter, lesson, content, question_count, max_retries=2): # Define the generate_questions_from_content function with the chapter, lesson, content, question_count, and max_retries parameters
    questions = []  # Initialize an empty list to store the questions
    allowed_types = determine_question_types(chapters[chapter]['lessons'][lesson]['title'].lower()) # Determine the allowed question types based on the lesson title and store in allowed_types

    #function to send request to OpenAI API with retries
    def send_request_with_retries(prompt, retries_left): # Define the send_request_with_retries function with the prompt and retries_left parameters
        try: # Try block to handle exceptions
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
                raise ValueError("Invalid API response.") # Raise a ValueError

            return response.choices[0].message.content.strip() # Return the content from the API response

        except Exception as e: # Catch any exceptions
            if retries_left > 0: # Check if there are retries left
                return send_request_with_retries(prompt, retries_left - 1) # Retry the request
            else: # If no retries left
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
                continue  # Try generating another question

            question_data = parse_response(question_text, question_type) # Parse the response to extract the question data

            if question_data and "question" in question_data and is_question_unique(question_data["question"]): # Check if the question data is valid and the question is unique
                questions.append(question_data) # Append the question data to the questions list
                store_question(question_data["question"])   # Store the question to avoid duplicates
            else: # If the question is not unique
                continue  # Skip duplicates or invalid questions

        except Exception as e: # Catch any exceptions
            print(f"Error generating question: {e}") # Log the error

    if len(questions) < question_count: # Check if not enough questions were generated
        print("Not enough unique questions generated.") # Log a warning message

    return questions # Return the generated questions

# Function to determine the allowed question types based on the lesson title
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

# Function to build a prompt based on the question type, chapter, and lesson
def build_prompt(chapter, lesson, question_type): # Define the build_prompt function with the chapter, lesson, and question_type parameters

    chapter_title = chapters.get(chapter, {}).get('title', "General Python Knowledge") # Retrieve the chapter title with a fallback value
    lesson_title = chapters.get(chapter, {}).get('lessons', {}).get(lesson, {}).get('title', "Fundamental Concepts") # Retrieve the lesson title with a fallback value

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
 
    return prompt # Return the generated prompt

# Function to parse the response from the OpenAI API
def parse_response(response_text, question_type): # Define the parse_response function with the response_text and question_type parameters
    try: # Try block to handle exceptions
        lines = response_text.split('\n') # Split the response text into lines
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
            return None # Return None
    except Exception as e: # Catch any exceptions
        return None # Return None

# Function to parse a true/false question
def parse_true_false(lines): # Define the parse_true_false function with the lines parameter

    try: # Try block to handle exceptions
        # Step 1: Clean and filter out empty lines 
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines

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
        return None # Return None

# Function to parse a scenario-based question
def parse_scenario(lines): # Define the parse_scenario function with the lines parameter

    try:
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

        return { # Return the structured question data
            "type": "scenario", # Include the question type
            "question": scenario_text, # Include the scenario text
            "correct_answer": correct_answer # Include the answer text
        }

    except Exception as e:  # Catch any exceptions
        return None # Return None

# Function to parse a multiple-choice question
def parse_multiple_choice(lines): # Define the parse_multiple_choice function with the lines parameter

    try: # Try block to handle exceptions
        # Step 1: Clean each line and remove empty lines
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines

        # Step 2: Filter out headers and unnecessary symbols
        question_lines = [ # Filter out headers and unnecessary symbols
            re.sub(r'^[#*>\-]+\s?', '', line)  # Remove common markdown symbols
            for line in cleaned_lines  # Iterate over the cleaned lines
            if not re.match(r'^(chapter|lesson|multiple[- ]?choice.*)$', line, re.IGNORECASE) # Filter out headers
        ]

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
                continue  # Move to the next line

            # Detect the correct answer
            if "correct answer:" in line.lower(): # Check if the line contains 'Correct Answer:'
                match = re.search(r'correct answer:\s*([A-Da-d])', line, re.IGNORECASE) # Match the correct answer pattern
                if match: # Check if the correct answer pattern is matched
                    correct_answer = match.group(1).upper() # Extract the correct answer
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
        return None # Return None

# Function to parse a fill-in-the-blank question
def parse_fill_in_the_blank(lines): # Define the parse_fill_in_the_blank function with the lines parameter

    try:
        # Step 1: Clean and filter lines
        cleaned_lines = [line.strip() for line in lines if line.strip()] # Clean and filter out empty lines
        # Step 2: Extract the question line with a placeholder
        question_line = next( # Extract the question line with a placeholder
            (line for line in cleaned_lines if 'Insert' in line or '________' in line), # Find lines with placeholders
            None # Return None if no valid line found
        )

        if not question_line:   # If no valid question line found
            raise ValueError("No valid blank or placeholder found in the question.") # Raise a ValueError

        # Step 3: Validate if the blank is properly placed
        if (
            question_line.endswith('? ________') or  # Avoid if blank follows a question mark
            question_line.endswith('.') or           # Avoid if sentence ends with a period
            question_line == '________'              # Avoid if it's a lone blank
        ):
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

        # Step 5: Format the question with consistent blanks
        formatted_question = re.sub(r'(_{2,}|\[.*?\]|-{3,}|Insert answer)', '________', question_line).strip() # Format the question with consistent blanks
        formatted_question = re.sub(r'\s*\([^)]*\)', '', formatted_question).strip() # Remove any parentheses from the question

        # Step 6: Return the structured question data
        return { # Return the structured question data
            "type": "fill_in_the_blank", # Include the question type
            "question": formatted_question, # Include the formatted question
            "correct_answer": correct_answer, # Include the correct answer
        }

    except Exception as e: # Catch any exceptions
        return None # Return None

# Function to parse a code challenge question
def parse_code_challenge(lines): # Define the parse_code_challenge function with the lines parameter

    try: # Try block to handle exceptions

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

        # Return 'question' instead of 'task' for consistency with retry logic
        return {
            "type": "write_code", # Include the question type
            "question": task_text,  # Align with the retry logic
            "correct_answer": correct_answer   # Include the solution code
        }

    except Exception as e: # Catch any exceptions
        return None # Return None

# Function to generate review questions for a specific chapter
def generate_review_questions(progress, chapter): # Define the generate_review_questions function with the progress and chapter parameters

    questions = [] # Initialize an empty list to store the questions
    lessons = chapters[chapter]['lessons'] # Retrieve the lessons for the specified chapter

    lesson_question_counts = {} # Initialize an empty dictionary to store the question counts per lesson

    for lesson_num, lesson in lessons.items(): # Iterate over the lessons
        if lesson_num == 8: # Check if the lesson number is 8
            continue  # Skip the review test lesson

        base_question_count = lesson.get('complexity', 1) # Retrieve the base question count for the lesson based on complexity level set in the config.py file

        mistake_exists = False # Initialize the mistake_exists variable as False
        try: # Try block to handle exceptions
            with sqlite3.connect('progress.db') as conn: # Connect to the database
                cursor = conn.cursor() # Create a cursor object
                cursor.execute( # Execute a query to check for mistakes
                    '''
                    SELECT 1
                    FROM mistakes
                    WHERE user_id = ? AND chapter = ? AND lesson = ?
                    LIMIT 1
                    ''',
                    (progress.user_id, chapter, lesson_num) # Provide the user ID, chapter, and lesson number as parameters
                )
                mistake_exists = cursor.fetchone() is not None # Check if a mistake exists
        except sqlite3.Error as e: # Catch any exceptions
            print(f"Failed to retrieve mistakes from database: {e}") # Log the error

        # If the user made any mistakes in this lesson, add one extra question
        if mistake_exists: # Check if a mistake exists
            total_question_count = base_question_count + 1 # Increment the question count
        else: # If no mistakes exist
            total_question_count = base_question_count # Use the base question count

        lesson_question_counts[lesson_num] = total_question_count # Store the total question count for the lesson

    # Now, generate questions for each lesson
    for lesson_num, question_count in lesson_question_counts.items(): # Iterate over the lesson question counts
    
        lesson_content = generate_lesson_content(progress, chapter, lesson_num)  # Retrieve the lesson content from the database or generate it if not available

        generated_questions = generate_questions_from_content( # Generate questions based on the lesson content
            chapter, lesson_num, lesson_content, question_count=question_count # Provide the chapter, lesson number, lesson content, and question count as parameters
        )

        for question in generated_questions: # Iterate over the generated questions
            question['original_lesson'] = lesson_num  # Add original_lesson to question data
            
        questions.extend(generated_questions) # Extend the questions list with the generated questions

    random.shuffle(questions) # Shuffle the questions
    return questions # Return the generated questions

# Function to fill in missing questions to meet the required count
def fill_missing_questions(existing_questions, chapter, total_needed): # Define the fill_missing_questions function with the existing_questions, chapter, and total_needed parameters
    
    while len(existing_questions) < total_needed: # Loop until we have enough questions
        lesson = random.randint(1, 7) # Randomly select a lesson
        lesson_content = generate_lesson_content(chapter, lesson) # Generate the lesson content
        new_question = generate_questions_from_content(chapter, lesson, lesson_content, 1) # Generate a new question
        existing_questions.extend(new_question) # Extend the existing questions list
    return existing_questions # Return the existing questions

# Function to generate a cumulative review with 100 questions plus mistakes from chapter reviews
def generate_cumulative_review(progress): # Define the generate_cumulative_review function with the progress parameter
    questions = [] # Initialize an empty list to store the questions

    # Collect mistakes from chapter reviews (lessons where lesson = 8)
    try: # Try block to handle exceptions
        with sqlite3.connect('progress.db') as conn:  # Connect to the database
            cursor = conn.cursor() # Create a cursor object
            cursor.execute( # Execute a query to retrieve mistakes from chapter reviews
                '''
                SELECT chapter, original_lesson
                FROM mistakes
                WHERE user_id = ? AND lesson = 8
                ''',
                (progress.user_id,)
            )
            mistakes = cursor.fetchall() # Fetch all the mistakes
    except sqlite3.Error as e: # Catch any exceptions
        mistakes = [] # Set mistakes to an empty list
 
    # For each mistake, generate a question based on the chapter and original lesson
    for mistake in mistakes: # Iterate over the mistakes
        chapter, original_lesson = mistake # Unpack the mistake
        lesson_content = generate_lesson_content(progress, chapter, original_lesson) # Retrieve the lesson content from the database or generate it if not available
        generated_questions = generate_questions_from_content( # Generate questions based on the lesson content
            chapter, original_lesson, lesson_content, question_count=1 # Provide the chapter, original lesson, lesson content, and question count as parameters
        )
        # Add the question to the list
        for question in generated_questions: # Iterate over the generated questions
            question['chapter'] = chapter # Add the chapter to the question data
            question['lesson'] = original_lesson # Add the original lesson to the question data
            question['original_lesson'] = original_lesson # Add the original lesson to the question data
        questions.extend(generated_questions) # Extend the questions list with the generated questions

    # Now, generate random questions from all chapters until we reach 100 + number of mistakes
    total_needed = 100 + len(mistakes) # Calculate the total number of questions needed
    while len(questions) < total_needed: # Loop until we have enough questions
        chapter = random.randint(1, 20) # Randomly select a chapter
        lesson = random.randint(1, 7) # Randomly select a lesson
        # Retrieve the lesson content
        lesson_content = generate_lesson_content(progress, chapter, lesson) # Generate the lesson content
        generated_questions = generate_questions_from_content( # Generate questions based on the lesson content
            chapter, lesson, lesson_content, question_count=1 # Provide the chapter, lesson, lesson content, and question count as parameters
        )
        for question in generated_questions: # Iterate over the generated questions
            question['chapter'] = chapter # Add the chapter to the question data
            question['lesson'] = lesson # Add the lesson to the question data
        questions.extend(generated_questions) # Extend the questions list with the generated questions

    random.shuffle(questions) # Shuffle the questions
    return questions[:total_needed] # Return the first 100 + number of mistakes questions

# Function to validate answers using GPT-3 for coding challenges and scenario-based questions
def validate_answer_with_gpt(question_data, user_response=None, user_code=None, user_output=None): # Define the validate_answer_with_gpt function with the question_data, user_response, user_code, and user_output parameters
    try: # Try block to handle exceptions 
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
        
        print("Sending Prompt to GPT:")
        print(validation_prompt)

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
        print("Received Response from GPT:")
        print(gpt_response)
        # Prioritize "Incorrect" over "Correct" to avoid misinterpretation
        if "incorrect" in gpt_response.lower(): # Check if the response contains 'incorrect'
            return False, gpt_response  # Invalid response
        elif "correct" in gpt_response.lower():     # Check if the response contains 'correct'
            return True, gpt_response  # Valid response
        else: # If neither 'correct' nor 'incorrect' is found
            return False, "Unexpected response from GPT. Please review the feedback." # Return an unexpected response message

    except ValueError as ve: # Catch ValueError exceptions
        return False, str(ve)   # Return False and the error message

    except Exception as e:  # Catch any exceptions
        return False, "An error occurred during validation." # Return False and an error message