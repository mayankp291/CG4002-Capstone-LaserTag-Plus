file_list1 = ['action.txt', 'gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt']
file_list2 = ['clean/clean_action.txt', 'clean/clean_gX.txt', 'clean/clean_gY.txt', 'clean/clean_gZ.txt', 'clean/clean_aX.txt', 'clean/clean_aY.txt', 'clean/clean_aZ.txt']

combined_content = ""

for i in range(len(file_list1)):
    file_path1 = file_list1[i]
    file_path2 = file_list2[i]
    
    with open(file_path1, "r") as file1, open(file_path2, "r") as file2:
        content1 = file1.read()
        content2 = file2.read()
        combined_content = content1 + "\n" + content2
        
        
    # Write the combined content to the output file
    with open(file_path1, "w") as output_file:
        output_file.write(combined_content)

