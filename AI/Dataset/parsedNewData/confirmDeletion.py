import os

# Define the input file paths
file_paths = ['action.txt', 'gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt']

# Define the buckets as a dictionary
buckets = {0: [], 1: [], 2: [], 3: []}

# Read the contents of action.txt and bucket them into four labels
with open('action.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('0'):
            buckets[0].append(line)
        elif line.startswith('1'):
            buckets[1].append(line)
        elif line.startswith('2'):
            buckets[2].append(line)
        elif line.startswith('3'):
            buckets[3].append(line)

# Apply the same labeling to the other five files based on line number
for file_path in file_paths:
    # Determine which bucket the file belongs to
    if 'action' in file_path:
        continue
    
    # Read the file and label the lines based on line number
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if i < len(buckets[0]) and line == buckets[0][i]:
                buckets[0][i] = file_path
            elif i < len(buckets[1]) and line == buckets[1][i]:
                buckets[1][i] = file_path
            elif i < len(buckets[2]) and line == buckets[2][i]:
                buckets[2][i] = file_path
            elif i < len(buckets[3]) and line == buckets[3][i]:
                buckets[3][i] = file_path

# Print the contents of the buckets
for label, contents in buckets.items():
    print(f"Label {label}: {len(contents)}")
