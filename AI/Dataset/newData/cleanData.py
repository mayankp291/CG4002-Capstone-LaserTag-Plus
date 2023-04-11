import numpy as np

# Define the input file paths
files = ['gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt', 'action.txt']

# Define the buckets as a dictionary
buckets = {0: [], 1: [], 2: [], 3: []}
action_lines = []

with open('action.txt', 'r') as f:
    action_lines = f.readlines()
    for line in action_lines:
        line = line.strip()
        if line.startswith('0'):
            buckets[0].append(line)
        elif line.startswith('1'):
            buckets[1].append(line)
        elif line.startswith('2'):
            buckets[2].append(line)
        elif line.startswith('3'):
            buckets[3].append(line)

for label, contents in buckets.items():
    print(f"Label {label}: {len(contents)} actions")


block_counts = np.zeros(4)
cycle_flags = [False] * 4
parsed_file_datas = {}
for curr_file_index, file in enumerate(files):
    print(f"Current file {file}")
    with open(file, 'r') as f:
        lines = f.readlines()
        block_actions = 0
        curr_label = None
        prev_label = None
        people = 0
        curr_cycle = ""
        data_to_overwrite = ""
        for count in range(len(action_lines)):
            
            prev_label = curr_label
            curr_label = action_lines[count].strip()

            if curr_label != prev_label and prev_label is not None and curr_label is not None:
                block_counts[int(prev_label)] += 1
                print(f"Block for label {prev_label}: {block_actions} actions")
                print(block_counts)

                if any(block_counts[i] > block_counts[j] + 2 for i in range(len(block_counts)) for j in range(len(block_counts)) if i != j):
                    curr_cycle = ""
                
                if block_actions < 20:
                    cycle_flags[int(prev_label)] = True
                    print(len(lines[count - block_actions: count]))
                    print(set(action_lines[count - block_actions: count]))
                    curr_block = "".join(lines[count - block_actions: count])
                    curr_cycle += curr_block
                else:
                    print(len(lines[count - block_actions: count - block_actions + 20]))
                    print(set(action_lines[count - block_actions: count - block_actions + 20]))
                    curr_block = "".join(lines[count - block_actions: count - block_actions + 20])
                    curr_cycle += curr_block

                if len(set(block_counts)) == 1:
                    if any(flag for flag in cycle_flags):
                        curr_cycle = ""
                    data_to_overwrite += curr_cycle
                    curr_cycle = ""
                    people += 1
                    cycle_flags = [False] * 4

                block_actions = 1
                continue

            
            block_actions += 1

        block_counts[int(prev_label)] += 1
        print(f"Block for label {prev_label}: {block_actions} actions")
        print(block_counts)

        if any(block_counts[i] > block_counts[j] + 2 for i in range(len(block_counts)) for j in range(len(block_counts)) if i != j):
            curr_cycle = ""
        
        print(len(lines[count - block_actions: count - block_actions + 20]))
        print(set(action_lines[count - block_actions + 1: count - block_actions + 21]))
        if block_actions < 20:
            curr_cycle = ""
        else:
            curr_block = "".join(lines[count - block_actions + 1: count - block_actions + 21])
            curr_cycle += curr_block

        if len(set(block_counts)) == 1:
            data_to_overwrite += curr_cycle
            people += 1
        
        
        parsed_file_datas[file] = data_to_overwrite
        
        if curr_file_index < len(files) - 1:
            block_counts = np.zeros(4)

for label, block_count in enumerate(block_counts):
    print(f"Label {label}: {int(block_count)} blocks")

print(f"Minimum number of people: {people}")


# for file, file_data in parsed_file_datas.items():
#     with open(file, "w") as f:
#         f.write(file_data)
                

