#!/usr/bin/env python3
import os
import json
import openai

OUTPUT_PATH = "Output"
architecture_data = None

###############################################################################
# AI Agent for Generating Software Architecture and Files from ChatGPT
###############################################################################

# Ensure you have your OpenAI API key set in the environment:
# export OPENAI_API_KEY="your_openai_api_key_here"
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_software_description_from_user():
    """
    Prompt user to enter a description of the desired software system.
    """
    print("Please enter the description of the software system you'd like to build:")
    print("(For example: 'A To-Do list web application with user authentication, a database, and a responsive UI.')")
    description = input("> ")
    return description


def ask_chatgpt_for_architecture(software_description):
    """
    Prompt ChatGPT to provide:
      - Software architecture
      - Technical stacks
      - File scaffolding
      - Number of files needed
      - Estimated number of prompts
    Return the data as a dict.
    """
    system_message = {
        "role": "system",
        "content": (
            "You are an expert software architect. "
            "Given a software description, you will propose a high-level architecture. "
            "You will provide a JSON response with the following keys:\n\n"
            "software_architecture: A high-level description of the architecture.\n"
            "technical_stacks: A list of technologies to be used.\n"
            "file_scaffolding: A structured overview of files and their purposes.\n"
            "number_of_files: The total number of files.\n"
            "number_of_prompts: Estimated ChatGPT prompts needed to generate the software.\n"
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Here is the software description:\n{software_description}\n\n"
            "Please provide the JSON structure as instructed."
        )
    }

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            temperature=0.2
        )
        response_text = response.choices[0].message["content"]

        # Attempt to parse the response as JSON
        # In practice, you might need more sophisticated error handling.
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"Error while asking ChatGPT for architecture: {e}")
        return None


def display_architecture_proposal():
    """
    Nicely format the architecture data for the user to review.
    """
    print("\nProposed Software Architecture from ChatGPT:")
    print("---------------------------------------------------")
    print(f"Software Architecture:\n{architecture_data.get('software_architecture', '')}\n")
    print(f"Technical Stacks:\n{architecture_data.get('technical_stacks', [])}\n")
    print("File Scaffolding:")
    file_scaffolding = architecture_data.get('file_scaffolding', {})
    if isinstance(file_scaffolding, dict):
        for folder, files in file_scaffolding.items():
            print(f"  - {folder}/")
            if isinstance(files, list):
                for f in files:
                    print(f"    * {f}")
            elif isinstance(files, dict):
                for folder, files in files.items():
                    print(f"    - {folder}/")
    elif isinstance(file_scaffolding, list):
        for item in file_scaffolding:
            print(f"  * {item}")
    else:
        print(file_scaffolding)

    print(f"\nTotal Number of Files: {architecture_data.get('number_of_files', 0)}")
    print(f"Estimated Number of Prompts: {architecture_data.get('number_of_prompts', 1)}")
    print("---------------------------------------------------")


def get_user_approval():
    """
    Ask the user if they approve the architecture proposal.
    Returns True if approved, False otherwise.
    """
    while True:
        user_input = input("Do you approve this architecture proposal? (yes/no): ").strip().lower()
        if user_input in ["yes", "y"]:
            return True
        elif user_input in ["no", "n"]:
            return False
        else:
            print("Please type 'yes' or 'no'.")

def create_folder_or_file(path, item):
    if item == "":
        full_item = path
    else:
        full_item = os.path.join(path, item)
    if os.path.exists(full_item):
        return

    if "." in item:
        file_content = ask_chatgpt_for_file_content(path, item)
        if file_content:
            save_file_to_output(path, item, file_content)
        else:
            print(f"Failed to retrieve content for {item}.")
    else:
        os.makedirs(full_item)

def generate_software_files():
    create_folder_or_file(OUTPUT_PATH, "")

    file_scaffolding = architecture_data.get("file_scaffolding", {})
    file_list = []

    # If the scaffolding is a dict with folder -> [files], handle that:
    if isinstance(file_scaffolding, dict):
        for folder, files in file_scaffolding.items():
            create_folder_or_file(OUTPUT_PATH, folder)
            if isinstance(files, list):
                for f in files:
                    # Remove trailing slash if present
                    f = f.rstrip("/")
                    file_list.append((folder, f))
            elif isinstance(files, dict):
                for folder, comments in files.items():
                    create_folder_or_file(OUTPUT_PATH, folder)

    # If the scaffolding is a list of files
    elif isinstance(file_scaffolding, list):
        # e.g., ["database_connector.py/", "config.json/", ...]
        for f in file_scaffolding:
            f = f.rstrip("/")
            file_list.append(("", f))

    # Prompt ChatGPT to generate each file
    for folder, filename in file_list:
        print(f"\nRequesting ChatGPT to generate '{filename}' in folder '{folder}'...")
        file_content = ask_chatgpt_for_file_content(folder, filename)
        if file_content:
            save_file_to_output(folder, filename, file_content)
        else:
            print(f"Failed to retrieve content for {filename}.")


def ask_chatgpt_for_file_content(folder, filename):
    """
    Ask ChatGPT to generate the file content for each file based on the architecture.
    This is a simplified prompt. You can refine it for better instructions.
    """
    system_message = {
        "role": "system",
        "content": (
            "You are a software engineer. Given a file name, the folder structure, and the overall architecture, "
            "generate the content for that file. Be concise and ensure it fits the previously proposed architecture."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Software Architecture: {architecture_data.get('software_architecture', '')}\n"
            f"Technical Stacks: {architecture_data.get('technical_stacks', [])}\n"
            f"Folder: {folder}\n"
            f"Filename: {filename}\n\n"
            f"Please generate the file content now."
        )
    }

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            temperature=0.2
        )
        file_content = response.choices[0].message["content"]
        return file_content
    except Exception as e:
        print(f"Error while asking ChatGPT for file content: {e}")
        return None


def save_file_to_output(folder, filename, content):
    """
    Save the generated content to the 'Output' folder, creating subfolders as necessary.
    """
    # Construct the full path
    output_folder = os.path.join(OUTPUT_PATH, folder)
    create_folder_or_file(OUTPUT_PATH, folder)

    file_path = os.path.join(output_folder, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved file: {file_path}")
    except Exception as e:
        print(f"Error saving file {file_path}: {e}")


def ask_chatgpt_for_one_file_content(folder, filename):
    """
    Ask ChatGPT to generate one file content for each file based on the architecture.
    This is a simplified prompt. You can refine it for better instructions.
    """
    system_message = {
        "role": "system",
        "content": (
            "You are a software engineer. Given a file name, the folder structure, and the overall architecture, "
            "generate the content for that file. Be concise and ensure it fits the previously proposed architecture."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Software Architecture: {architecture_data.get('software_architecture', '')}\n"
            f"Technical Stacks: {architecture_data.get('technical_stacks', [])}\n"
            f"Folder: {folder}\n"
            f"Filename: {filename}\n\n"
            f"Please generate the file content now."
        )
    }

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            temperature=0.2
        )
        file_content = response.choices[0].message["content"]
        return file_content
    except Exception as e:
        print(f"Error while asking ChatGPT for file content: {e}")
        return None

def main():
    # 1. Get software description
    software_description = get_software_description_from_user()

    # 2. Ask ChatGPT for architecture
    global architecture_data
    architecture_data = ask_chatgpt_for_architecture(software_description)
    if not architecture_data:
        print("Could not retrieve a valid architecture proposal from ChatGPT. Exiting.")
        return

    # 3. Display architecture to user
    display_architecture_proposal()

    # 4. Ask for user approval
    if not get_user_approval():
        print("Architecture not approved. Exiting.")
        return
    else:
        print("Architecture approved. Proceeding with file generation...")

    # 5. Generate software files
    generate_software_files()

    print("\nAll done! Check the 'Output' folder for generated files.")


if __name__ == "__main__":
    main()
