# List of input file names
input_file_names = ['dataCollectMadhan/action.txt', 'dataCollectMadhan/gX.txt', 'dataCollectMadhan/gY.txt', 'dataCollectMadhan/gZ.txt', 'dataCollectMadhan/aX.txt', 'dataCollectMadhan/aY.txt', 'dataCollectMadhan/aZ.txt']
# List of output file names
output_file_names = ['action.txt', 'gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt']

# List of line numbers to extract for each file
line_numbers = [[1251, 1300]]

# Loop through each input file
for i in range(len(input_file_names)):
    # Open the input and output files
    with open(input_file_names[i], "r") as input_file, open(output_file_names[i], "a") as output_file:
        # Loop through each line number range for the current input file
        for start, end in line_numbers[i]:
            # Loop through the lines of the input file until we reach the start line
            for j, line in enumerate(input_file):
                if j == start - 1:
                    break
            # Loop through the lines of the input file until we reach the end line
            for k in range(start - 1, end):
                output_file.write(next(input_file))
