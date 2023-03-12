# Open the six files in append mode
file1 = open("file1.txt", "a")
file2 = open("file2.txt", "a")
file3 = open("file3.txt", "a")
file4 = open("file4.txt", "a")
file5 = open("file5.txt", "a")
file6 = open("file6.txt", "a")

# Write some data to each file
file1.write("More data for file 1\n")
file2.write("More data for file 2\n")
file3.write("More data for file 3\n")
file4.write("More data for file 4\n")
file5.write("More data for file 5\n")
file6.write("More data for file 6\n")

# Close all the files
file1.close()
file2.close()
file3.close()
file4.close()
file5.close()
file6.close()


import csv

# define data to save
data = [
    ['John', 'Doe', 28],
    ['Jane', 'Smith', 32],
    ['Bob', 'Johnson', 45]
]

# define CSV filename
filename = 'data.csv'

# open file in write mode
with open(filename, mode='w', newline='') as file:
    
    # create a writer object
    writer = csv.writer(file)
    
    # write header row
    writer.writerow(['First Name', 'Last Name', 'Age'])
    
    # write data rows
    for row in data:
        writer.writerow(row)
        
print(f"Data saved to {filename} successfully.")