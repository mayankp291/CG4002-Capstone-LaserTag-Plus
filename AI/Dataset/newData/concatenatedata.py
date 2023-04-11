old_file_list = ['action.txt', 'gX.txt', 'gY.txt', 'gZ.txt', 'aX.txt', 'aY.txt', 'aZ.txt']
new_file_list = ['Redo grenade (unseen player) wo Madhan/action.txt', 'Redo grenade (unseen player) wo Madhan/gX.txt', 'Redo grenade (unseen player) wo Madhan/gY.txt', 'Redo grenade (unseen player) wo Madhan/gZ.txt', 'Redo grenade (unseen player) wo Madhan/aX.txt', 'Redo grenade (unseen player) wo Madhan/aY.txt', 'Redo grenade (unseen player) wo Madhan/aZ.txt']

def concatenate_files(list1, list2):
    for i in range(len(list1)):
        with open(list1[i], 'a') as f:
            with open(list2[i], 'r') as g:
                f.write(g.read())

concatenate_files(old_file_list, new_file_list)