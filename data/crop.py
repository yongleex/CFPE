import os

root = "./case8" 

# os.system("cd case1")

for name in os.listdir(root):
    p1 = root+os.sep+name
    p2 = root+os.sep+"out_"+name
    comm = f"pdfcrop {p1} {p2}"
    os.system(comm)
    print(name)
