#import csv

# with open("pesanan.csv", newline='') as pesanan:
#     rows = csv.reader(pesanan, delimiter=',')
#     data = []
#     for row in rows:
#         data.append(row)

class Array:
    def __init__(self, capacity = 4):
        self.data = [None]*capacity
        self.cap = capacity
        self.n = 0
    def len(self):
        return self.n
    def get(self, i):
        return self.data[i]
    def grow(self):
        new = [None]*(self.n*2)
        for n in (self.n):
            new[n]=self.data[n]
        self.data = new
        self.cap = self.cap*2
    def append(self, v):
        if self.n == self.cap:
            self.grow(self)
        self.data[self.n] = v
        self.n = self.n + 1
    def insert(self, i, v):
        if self.n == self.cap:
            self.grow(self)
        for i in range(self.n - i):
            offset = self.n - i
            self.data[offset] = self.data[offset - 1]

#test

