# List the filenames you want to modify
file_list = ['gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt', 'action.txt']

# Loop over each file
for file_name in file_list:
    # Open the file for reading and writing
    with open(file_name, 'r+') as file:
        # Move the file pointer to the end of the file
        file.seek(0, 2)
        # Find the position of the last newline character
        pos = file.tell() - 1
        while pos > 0 and file.read(1) != "\n":
            pos -= 1
            file.seek(pos, 0)
        # Truncate the file at the last newline character
        if pos > 0:
            file.seek(pos, 0)
            file.truncate()
        # Add a newline character to the end of the file
        file.write("\n")
print("Done!")