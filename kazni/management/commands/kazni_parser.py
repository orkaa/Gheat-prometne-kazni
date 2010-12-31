file = open('kazni.csv', 'r')
count = 0
for line in file:
    count += 1
    line = line.split(';')
    print count, line[6]
