import os
from pathlib import Path
from dotenv import load_dotenv
import openai
import tkinter as tk
from tkinter import simpledialog

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


# Function to create and handle the GUI
def create_gui():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Get user input for text and file name
    input_text = simpledialog.askstring(
        "Input", "Enter text to convert to speech:", parent=root
    )
    output_file = simpledialog.askstring(
        "File Name", "Enter output file name (without extension):", parent=root
    )

    # Validate and process the input
    if input_text and output_file:
        text_to_speech(input_text, output_file=output_file + ".mp3")
    else:
        print("No input provided.")


# Example usage
if __name__ == "__main__":
    create_gui()
