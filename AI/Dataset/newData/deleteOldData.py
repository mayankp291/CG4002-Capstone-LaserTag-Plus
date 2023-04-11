def delete_line_and_corresponding_lines(line_number, file_name, other_files):
    # Open the file in read mode
    with open(file_name, "r") as file:
        lines = file.readlines()

    # Remove the line at the specified index
    lines.pop(line_number)

    # Open the file in write mode and write the modified content
    with open(file_name, "w") as file:
        file.writelines(lines)

    # Open each other file in read mode and read the content
    for other_file_name in other_files:
        with open(other_file_name, "r") as other_file:
            other_lines = other_file.readlines()

        # Remove the line at the specified index
        other_lines.pop(line_number)

        # Open the other file in write mode and write the modified content
        with open(other_file_name, "w") as other_file:
            other_file.writelines(other_lines)



def get_first_action(file_name, action):

    with open(file_name, "r") as file:
        lines = file.readlines()
        for count, line in enumerate(lines):
            if line.strip() == action:
                return count

    return -1

def main():
    file_list = ['gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt']

    main_file_to_check = "action.txt"
    action = "3"

    line_number = get_first_action(main_file_to_check, action)

    while line_number >= 0:
        delete_line_and_corresponding_lines(line_number, main_file_to_check, file_list)
        line_number = get_first_action(main_file_to_check, action)


if __name__ == "__main__":
    main()
