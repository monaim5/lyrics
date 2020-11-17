

with open(r'C:\Users\mon\Desktop\test.txt') as f:
    txt = f.readlines()


for i in range(len(txt)):
    txt[i] = txt[i].strip()

print('["' + '", "'.join(txt) + '"]')
