import os
from subprocess import call
import logging

path_to_watch = "./media" # ./media

print("Hi it's Sid")

old = os.listdir(path_to_watch)

while True:
    new = os.listdir(path_to_watch)
    if len(new) > len(old):
        newfile = list(set(new) - set(old))
        filenameLength = len(str(newfile[0]))
        x = int(filenameLength) - 3
        filenameAppend = str(newfile[0])[0:x]
        textName = filenameAppend + ".txt"
        old = new
        extension = os.path.splitext(path_to_watch + "/" + newfile[0])[1]
        if extension == ".py":
            print(newfile[0])
            
        else: # Exception handling; implement logging function
            continue            
    else:
        continue