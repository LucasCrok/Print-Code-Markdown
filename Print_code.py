import os

def print_files_in_directory(directory, base_dir_len):
    folders_to_skip = {".git"} 
    
    with open("output.txt", "a", encoding='utf-8') as output_file:
        try:
            items = os.listdir(directory)
        except FileNotFoundError:
            # Keep full path for top-level errors
            print(f"Error: Directory not found: {directory}")
            return
        except PermissionError:
            # Keep full path for top-level errors
            print(f"Error: Permission denied for directory: {directory}")
            return
            
        for item in items:
            item_path = os.path.join(directory, item)
            # Calculate relative path for cleaner printing
            relative_path = item_path[base_dir_len:].lstrip(os.sep) 

            if os.path.isfile(item_path):
                # Removed "Trying file" print
                _, extension = os.path.splitext(item)
                try:
                    with open(item_path, 'r', encoding='utf-8', errors='ignore') as file: 
                        lines = file.readlines()

                        # --- (filter_comments function remains the same) ---
                        def filter_comments(lines):
                            in_block_comment = False
                            result = []
                            for line in lines:
                                stripped = line.strip()
                                # Basic C/Java/JS style comment handling
                                # Check for block comment end first
                                if in_block_comment:
                                    if "*/" in stripped:
                                        in_block_comment = False
                                        line = line.split("*/", 1)[1] # Get content after */
                                        stripped = line.strip() # Re-strip
                                    else:
                                        continue # Skip the line entirely if still in block comment

                                # Check for block comment start
                                if not in_block_comment and "/*" in stripped:
                                    slash_slash_pos = stripped.find("//")
                                    slash_star_pos = stripped.find("/*")
                                    if slash_slash_pos != -1 and slash_slash_pos < slash_star_pos:
                                        line = line.split("//", 1)[0] # Treat as single line comment
                                    else:
                                        in_block_comment = True
                                        if "*/" in stripped[slash_star_pos+2:]:
                                             in_block_comment = False
                                             line = line.split("/*", 1)[0] + line.split("*/", 1)[1]
                                        else:
                                             line = line.split("/*", 1)[0] # Keep content before /*

                                # Check for single line comment (if not already handled)
                                if not in_block_comment and "//" in stripped:
                                     line = line.split("//", 1)[0]
                                
                                if line.strip():
                                    result.append(line)
                                    
                            return result
                        # --- (End of filter_comments function) ---

                        code_lines = filter_comments(lines)
                        
                        filtered_code_lines = [line for line in code_lines
                                               if not line.strip().startswith(("import ", "from ", "package ")) 
                                               and not line.isspace()]

                        code = "".join(filtered_code_lines).strip()
                        
                        if code: 
                            output_file.write(f"```{relative_path}\n") # Use relative path in output file too
                            output_file.write(f"{code}\n")
                            output_file.write("```\n\n")
                            # Print only the relative path/filename on success
                            print(f"Processed: {relative_path}") 
                        else:
                            # Print only the relative path/filename for skipped empty files
                            print(f"Skipped (empty/filtered): {relative_path}") 

                except PermissionError:
                    # Print only the relative path/filename for permission errors
                    print(f"Skipped (permission): {relative_path}")
                except Exception as e: 
                    # Print only the relative path/filename for other errors
                    print(f"Skipped (error: {type(e).__name__}): {relative_path}")

            elif os.path.isdir(item_path):
                if item in folders_to_skip:
                    # Print only the relative path/dirname for skipped dirs
                    print(f"Skipping dir: {relative_path}{os.sep}") 
                    continue  
                
                # Print only the relative path/dirname when entering
                print(f"Entering: {relative_path}{os.sep}") 
                print_files_in_directory(item_path, base_dir_len) # Recurse

# --- Main execution part ---
output_filename = "output.txt"
if os.path.exists(output_filename):
    try:
        os.remove(output_filename)
        print(f"Removed existing {output_filename}")
    except OSError as e:
        print(f"Error removing existing {output_filename}: {e}")
        # exit(1) # Optional: exit if removal fails

main_directory = input("Enter the main directory path: ").strip() # Strip whitespace

if os.path.isdir(main_directory):
    # Normalize path and get its length for relative path calculation
    normalized_main_dir = os.path.abspath(main_directory)
    base_dir_length = len(normalized_main_dir) + len(os.sep) # Include separator length
    
    print(f"\nStarting processing in: {normalized_main_dir}")
    print("-" * 30) # Separator
    print_files_in_directory(normalized_main_dir, base_dir_length)
    print("-" * 30) # Separator
    print(f"Processing complete. Output written to {output_filename}")
else:
    print(f"Error: The provided path '{main_directory}' is not a valid directory.")