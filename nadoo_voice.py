import os
from pathlib import Path
from dotenv import load_dotenv
import openai
import tkinter as tk
from tkinter import simpledialog, ttk, scrolledtext
import json

# Load environment variables from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client with your API key
openai.api_key = api_key


# Function to convert text to speech and save as an MP3 file
def text_to_speech(input_text, model="tts-1", voice="onyx", output_file="speech.mp3"):
    try:
        # Define the path for the output file
        speech_file_path = Path(__file__).parent / output_file

        client = openai.OpenAI()

        # Create the spoken audio from the input text
        response = client.audio.speech.create(
            model=model, voice=voice, input=input_text
        )

        # Stream the response to the file
        response.stream_to_file(speech_file_path)
        print(f"Audio file saved as {speech_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def gpt_prompt_for_chapter_analysis(chunk, last_chapter_title):
    """
    Analyzes a text chunk to identify chapters using GPT-4, with a fallback to GPT-3.5 if necessary.
    Returns the last identified chapter if no new chapters are found, along with the text provided in the response.

    :param chunk: Text chunk to be analyzed.
    :param last_chapter_title: Title of the last identified chapter to continue from.
    :return: A list of chapters found in the chunk, or the last chapter if no new chapters are found.
    """
    # Example JSON structure showing potential multiple chapters
    example_json = {
        "chapters": [
            {
                "chapter_title": "Chapter 1",
                "chapter_content": "Content of Chapter 1...",
            },
            {
                "chapter_title": "Chapter 2",
                "chapter_content": "Content of Chapter 2...",
            },
        ]
    }

    # Detailed prompt construction for GPT models
    prompt = (
        f"Assistive AI, your task is to analyze the text chunk provided and identify chapters within it. "
        f"Start from the last known chapter titled '{last_chapter_title}'. "
        f"Chapter Titles usually are written in CAPITAL LETTERS"
        f"They also usually take a whole line."
        f"Be carful not to include any other text in the chapter title and also that in the text the chapter titles are somethimes mentioned"
        f"Examine the text for any new chapter, and return their titles and full content. It is absolutly crucial that you return the full content of the chapters."
        f"No not change any of the text simply copy and past it."
        f"Be carfull not to add any styling to the text like /n or /t"
        f"Here is the text chunk for analysis: {chunk}."
        f"If no new chapters are found, simply use the last chapter for the rest of the found chapter content. "
        f"Your response should be in a JSON format similar to this example: {json.dumps(example_json)}"
    )

    client = openai.OpenAI()  # Ensure the OpenAI client is set up with an API key

    attempts = 0
    max_attempts = 2
    models = ["gpt-4-1106-preview", "gpt-3.5-turbo-1106"]

    while attempts < max_attempts + 1:
        model = models[attempts % len(models)]
        # print(f"Sending the following detailed prompt to {model}:")
        # print(prompt)

        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Please respond with a detailed analysis in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        response_content = response.choices[0].message.content
        # print(f"Received response from {model}:")
        # print(response_content)

        try:
            response_data = json.loads(response_content)

            return response_data  # Correct response with new chapters

        except json.JSONDecodeError:
            print(
                f"Error decoding JSON response from {model}. The response was not valid JSON."
            )

        attempts += 1

    # print("Failed to get a valid response after multiple attempts.")
    return []  # Return an empty list only if all attempts fail


def split_into_chunks(book_text, chunk_size=500):
    """
    Splits the book text into manageable chunks, trying to break at sentence endings.
    'chunk_size' is in characters, adjust based on testing.
    """
    chunks = []
    chunk_count = 0
    while book_text:
        # Take the first 'chunk_size' characters from the book text
        chunk = book_text[:chunk_size]

        # Ensure the chunk ends on a complete sentence where possible
        last_end = max(chunk.rfind("."), chunk.rfind("!"), chunk.rfind("?"))
        if last_end != -1 and len(chunk) - last_end < 200:
            # Adjust chunk to end at the last complete sentence
            chunk = chunk[: last_end + 1]
            # Adjust the remaining book text starting after the last complete sentence
            book_text = book_text[last_end + 1 :]
        else:
            # If no sentence ending is found, or it's too close to the end of the chunk, proceed as usual
            book_text = book_text[chunk_size:]

        chunks.append(chunk)
        chunk_count += 1

        # Print each chunk with spacing
        # print(f"Chunk {chunk_count}:\n{chunk}\n\n---\n")

    return chunks


def combine_chapter_responses(response_list):
    """
    Combines the chapter information from multiple responses into one list.
    If the same chapter appears in multiple responses, their content is combined.
    Assumes each response in response_list is already a list of dictionaries.
    """
    chapter_dict = {}
    for response in response_list:
        if isinstance(response, list):
            for chapter in response:
                title = chapter.get("chapter_title", "Untitled")
                content = chapter.get("chapter_content", "")

                if title in chapter_dict:
                    # Append content to existing chapter
                    # print(f"Appending content to existing chapter: {title}")
                    chapter_dict[title] += content
                else:
                    # Add new chapter
                    # print(f"Adding new chapter: {title}")
                    chapter_dict[title] = content
        else:
            print("Unexpected response format. Expected a list of dictionaries.")

    # Convert the dictionary back to a list of chapter dictionaries
    combined_chapters = [
        {"chapter_title": title, "chapter_content": content}
        for title, content in chapter_dict.items()
    ]
    print("Finished combining chapters.")
    return combined_chapters


# Function to process the entire book and return chapters in JSON
def process_entire_book(book_text):
    print("Processing entire book...")

    # Split the book into chunks
    print("Splitting book into chunks...")
    chunks = split_into_chunks(book_text)
    all_chapters = []
    last_chapter_title = ""  # Initialize with an empty string

    for chunk in chunks:
        print(f"Processing chunk: {chunk}")
        response = gpt_prompt_for_chapter_analysis(chunk, last_chapter_title)

        # Extract the chapters from the response
        chapters = response.get("chapters", [])

        # Check if the response contains any chapters
        if not chapters:
            print("No chapters found in response.")
            continue

        # Check if chapters list is not empty before updating last_chapter_title
        if chapters:
            # print(chapters)
            last_chapter = chapters[-1]

            # print(f"Last chapter : {last_chapter}")

            # Update the last chapter title
            last_chapter_title = last_chapter.get("chapter_title", last_chapter_title)

            # we will loop through the chapters and add them to the all_chapters list
            # We will first check if the chapter is already in the list if so we will append the content to the existing chapter
            # if not we will add the chapter to the list
            for chapter in chapters:
                title = chapter.get("chapter_title", "Untitled")
                content = chapter.get("chapter_content", "")
                chapter_found = False
                for chapter_dict in all_chapters:
                    if title == chapter_dict.get("chapter_title"):
                        chapter_found = True
                        chapter_dict["chapter_content"] += content
                        break
                if not chapter_found:
                    all_chapters.append(chapter)

    return all_chapters  # This will be a list of all chapter dictionaries


def start_conversion(mode_combobox, text_area):
    mode = mode_combobox.get()
    input_text = text_area.get("1.0", tk.END).strip()  # Get text from text area

    if mode == "Normal":
        output_file = simpledialog.askstring(
            "File Name", "Enter output file name (without extension):", parent=root
        )
        if input_text and output_file:
            text_to_speech(input_text, output_file=output_file + ".mp3")
        else:
            print("No input provided.")

    elif mode == "Book" and input_text:
        import threading

        chapters = process_entire_book(input_text)
        threads = []  # List to keep track of threads

        import time
        import threading
        import re

        # Function to sanitize filenames
        def sanitize_filename(filename):
            """Remove or replace invalid characters for file names."""
            invalid_chars = (
                r'[<>:"/\\|?*]'  # Regex pattern for invalid filename characters
            )
            return re.sub(
                invalid_chars, "_", filename
            )  # Replace invalid characters with underscore

        # Start timing
        start_time = time.time()

        # Process the book and create threads for text to speech
        chapters = process_entire_book(input_text)
        threads = []  # List to keep track of threads
        chapter_number = 1  # Initialize chapter number counter

        for chapter in chapters:
            title = chapter.get("chapter_title", "Untitled")
            text = chapter.get("chapter_content", "")

            # Combine the title and text, separated by a period for natural speech pause
            combined_text = f"{title}. {text}"

            # Modify and sanitize the title to include chapter number
            title_with_number = f"{chapter_number:02d}_{title}"
            sanitized_title = sanitize_filename(title_with_number)

            # Print the chapter title and a snippet of the content for debugging
            print(f"Processing chapter: {sanitized_title}")
            print(
                f"Content snippet: {combined_text[:100]}..."
            )  # Updated to show combined text

            # Create a thread for each text_to_speech call
            thread = threading.Thread(
                target=text_to_speech,
                kwargs={
                    "input_text": combined_text,
                    "output_file": f"{sanitized_title}.mp3",
                },
            )
            threads.append(thread)
            thread.start()

            chapter_number += 1  # Increment the chapter number for the next chapter

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # End timing and print total elapsed time
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Total processing time: {elapsed_time:.2f} seconds")

    else:
        print("No input provided.")


# Function to create and handle the GUI
def create_gui():
    root = tk.Tk()
    root.title("Text to Speech Converter")

    # Mode selection
    mode_label = tk.Label(root, text="Select Mode:")
    mode_label.pack()

    mode_combobox = ttk.Combobox(root, values=["Normal", "Book"])
    mode_combobox.pack()
    mode_combobox.set("Normal")

    # Text area for input
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10, width=50)
    text_area.pack(padx=10, pady=10)

    # Start button
    start_button = tk.Button(
        root, text="Start", command=start_conversion(mode_combobox, text_area)
    )
    start_button.pack()

    root.mainloop()


# Example usage
if __name__ == "__main__":
    create_gui()
