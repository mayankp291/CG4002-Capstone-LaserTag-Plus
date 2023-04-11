import os

# Define the input file paths
file_paths = ['action.txt', 'gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt']

# Define the ranges of lines to remove
ranges = [(251, 300), (501, 550), (651, 700), (951, 1000), (1201, 1250)]

# Loop through each file path
for file_path in file_paths:
    # Read in the contents of the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Remove the specified lines for each range
    removed_lines = 0
    for start_line, end_line in ranges:
        start_line -= removed_lines
        end_line -= removed_lines
        del lines[start_line-1:end_line]
        removed_lines += (end_line - start_line + 1)
    
    # Write the updated contents to the file
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    # Print a message indicating the file has been updated
    print(f"{os.path.basename(file_path)} updated.")
