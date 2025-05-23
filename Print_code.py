import os

def get_allowed_extensions() -> set[str]:
    """
    Ask the user which file extensions to keep.
    The user may separate extensions with spaces or commas and may omit the dot.
      e.g.  py java  OR  .py,.java  OR  py,java
    Returns a set like {'.py', '.java'}.
    An empty reply means: keep every file type.
    """
    raw = input("Enter file extensions to include "
                "(e.g.  py java js  – leave blank for ALL): ").strip()

    if not raw:                       # empty → match everything
        return set()

    # split on space or comma, remove empties, normalise, add dot if missing
    exts = {
        (("." + ext) if not ext.startswith(".") else ext).lower()
        for ext in raw.replace(",", " ").split()
        if ext.strip()
    }
    return exts


def print_files_in_directory(directory: str,
                             base_dir_len: int,
                             allowed_exts: set[str]):
    folders_to_skip = {".git"}

    with open("output.txt", "a", encoding='utf-8') as output_file:
        try:
            items = os.listdir(directory)
        except FileNotFoundError:
            print(f"Error: Directory not found: {directory}")
            return
        except PermissionError:
            print(f"Error: Permission denied for directory: {directory}")
            return

        for item in items:
            item_path = os.path.join(directory, item)
            relative_path = item_path[base_dir_len:].lstrip(os.sep)

            if os.path.isfile(item_path):
                _, extension = os.path.splitext(item)
                extension = extension.lower()

                # Skip file if it is not in the wanted set (unless set is empty → match all)
                if allowed_exts and extension not in allowed_exts:
                    print(f"Skipped (ext): {relative_path}")
                    continue

                try:
                    with open(item_path, 'r', encoding='utf-8', errors='ignore') as file:
                        lines = file.readlines()

                        def filter_comments(lines):
                            in_block_comment = False
                            result = []
                            for line in lines:
                                stripped = line.strip()

                                if in_block_comment:
                                    if "*/" in stripped:
                                        in_block_comment = False
                                        line = line.split("*/", 1)[1]
                                        stripped = line.strip()
                                    else:
                                        continue

                                if not in_block_comment and "/*" in stripped:
                                    slash_slash_pos = stripped.find("//")
                                    slash_star_pos = stripped.find("/*")
                                    if slash_slash_pos != -1 and slash_slash_pos < slash_star_pos:
                                        line = line.split("//", 1)[0]
                                    else:
                                        in_block_comment = True
                                        if "*/" in stripped[slash_star_pos+2:]:
                                            in_block_comment = False
                                            line = (line.split("/*", 1)[0] +
                                                    line.split("*/", 1)[1])
                                        else:
                                            line = line.split("/*", 1)[0]

                                if not in_block_comment and "//" in stripped:
                                    line = line.split("//", 1)[0]

                                if line.strip():
                                    result.append(line)
                            return result

                        code_lines = filter_comments(lines)
                        filtered_code_lines = [
                            ln for ln in code_lines
                            if not ln.strip().startswith(("import ", "from ", "package "))
                            and not ln.isspace()
                        ]
                        code = "".join(filtered_code_lines).strip()

                        if code:
                            output_file.write(f"```{relative_path}\n")
                            output_file.write(f"{code}\n```\n\n")
                            print(f"Processed: {relative_path}")
                        else:
                            print(f"Skipped (empty/filtered): {relative_path}")

                except PermissionError:
                    print(f"Skipped (permission): {relative_path}")
                except Exception as e:
                    print(f"Skipped (error: {type(e).__name__}): {relative_path}")

            elif os.path.isdir(item_path):
                if item in folders_to_skip:
                    print(f"Skipping dir: {relative_path}{os.sep}")
                    continue

                print(f"Entering: {relative_path}{os.sep}")
                print_files_in_directory(item_path, base_dir_len, allowed_exts)


output_filename = "output.txt"
if os.path.exists(output_filename):
    try:
        os.remove(output_filename)
        print(f"Removed existing {output_filename}")
    except OSError as e:
        print(f"Error removing existing {output_filename}: {e}")

main_directory = input("Enter the main directory path: ").strip()
if not os.path.isdir(main_directory):
    print(f"Error: The provided path '{main_directory}' is not a valid directory.")
    exit(1)

allowed_extensions = get_allowed_extensions()

normalized_main_dir = os.path.abspath(main_directory)
base_dir_length = len(normalized_main_dir) + len(os.sep)

print(f"\nStarting processing in: {normalized_main_dir}")
print("-" * 30)
print_files_in_directory(normalized_main_dir, base_dir_length, allowed_extensions)
print("-" * 30)
print(f"Processing complete. Output written to {output_filename}")

# Clean up trailing newlines from the output file
if os.path.exists(output_filename):
    try:
        # Determine the byte sequence for two OS-specific newlines
        # This accounts for \n becoming \r\n on Windows, for example.
        expected_trailing_bytes = (os.linesep + os.linesep).encode('utf-8')
        len_expected_bytes = len(expected_trailing_bytes)

        with open(output_filename, 'rb+') as f:
            f.seek(0, os.SEEK_END)  # Go to the end of the file
            size = f.tell()         # Get the current size

            if size >= len_expected_bytes:  # Check if file is long enough
                f.seek(-len_expected_bytes, os.SEEK_END)  # Go to the start of the potential trailing sequence
                last_bytes = f.read(len_expected_bytes)   # Read the sequence

                if last_bytes == expected_trailing_bytes:  # Check if it matches
                    f.truncate(size - len_expected_bytes)  # Truncate the file
                    print(f"Removed final OS-specific newlines (length {len_expected_bytes}) from {output_filename}")
            # else: No specific action needed if file is too short or doesn't end with the expected sequence
    except Exception as e:
        print(f"Error during final cleanup of {output_filename}: {e}")