import subprocess
import sys # Import sys to get the current python executable
import os  # Import os to check file paths

def main():
    while True:
        print("\nChoose an option:")
        print("1. User Analytics and Reporting")
        print("2. User Behaviour Analysis")
        print("3. User Feedback Analysis")
        print("Type 'exit' to quit.")

        choice = input("Enter your choice: ").strip()

        # Define script paths (use raw strings for Windows paths)
        script_paths = {
            '1': r"C:\Users\shash\Desktop\ccmicroservice\useranalytics.py",
            '2': r"C:\Users\shash\Desktop\ccmicroservice\behavior_analysis.py",
            '3': r"C:\Users\shash\Desktop\ccmicroservice\feedback_analysis_supabase.py" # Corrected name
        }

        if choice.lower() == 'exit':
            print("Exiting program.")
            break
        elif choice in script_paths:
            # Get the full path from the dictionary
            script_to_run = script_paths[choice]
            run_script(script_to_run)
        else:
            print("Invalid choice. Please select a valid option (1, 2, 3, or exit).")

def run_script(script_path):
    # Check if the file actually exists before trying to run it
    if not os.path.exists(script_path):
        print(f"\nError: Script not found at path: {script_path}")
        return

    try:
        print(f"\nRunning {os.path.basename(script_path)}...\n")
        # Use sys.executable to ensure the same Python interpreter is used
        # This is more reliable than hardcoding "python" or "python3"
        subprocess.run([sys.executable, script_path], check=True)
        print(f"\nFinished running {os.path.basename(script_path)}.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running {os.path.basename(script_path)}:")
        print(e) # Print the error details
    except FileNotFoundError:
        # This might catch cases where sys.executable is not found, though unlikely
        print(f"Error: Python executable not found or script path incorrect: {script_path}")
    except Exception as e:
        # Catch other potential errors during execution
        print(f"An unexpected error occurred while trying to run {os.path.basename(script_path)}:")
        print(e)


if __name__ == "__main__":
    main()