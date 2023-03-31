old_file_list = ['action.txt', 'gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt']
new_file_list = ['dataCollect/action.txt', 'dataCollect/gX.txt', 'dataCollect/gY.txt', 'dataCollect/gZ.txt', 'dataCollect/aX.txt', 'dataCollect/aY.txt', 'dataCollect/aZ.txt']

def concatenate_files(list1, list2):
    for i in range(len(list1)):
        with open(list1[i], 'a') as f:
            with open(list2[i], 'r') as g:
                f.write(g.read())

concatenate_files(old_file_list, new_file_list)