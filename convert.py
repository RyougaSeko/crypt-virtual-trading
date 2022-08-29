
path = 'pairs.txt'
li = []
base_asset = input('Enter Base asset: \n')

with open(path) as f:
    s = f.read()
    words = s.split('\n')
    # print(words)
    
for word in words:
    if word.split('_')[1] == base_asset:
        print(word)

# print(base_asset)

