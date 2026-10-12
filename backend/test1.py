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
        self.shift = 0

    def len(self):
        return self.n
    
    def get(self, i):
        return self.data[i]
    
    def grow(self):
        new = [None]*(self.cap*2)
        for n in range(self.n):
            new[n]=self.data[n]
        self.data = new
        self.cap = self.cap*2

    def append(self, v):
        if self.n == self.cap:
            self.grow()
        self.data[self.n] = v
        self.n = self.n + 1

    def insert(self, i, v):
        if self.n == self.cap:
            self.grow()
        for k in range(self.n - i):
            offset = self.n - k
            self.data[offset] = self.data[offset - 1]
            self.shift = self.shift + 1
        self.data[i] = v
        self.n = self.n + 1

    def delete(self ,i):
        v = self.data[i]
        for k in range(i, self.n - 1):
            self.data[k] = self.data[k+1]
            self.shift = self.shift+1
        self.data[n-1] = None
        self.n = self.n - 1
        return v
    


#test

