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
        self.data[self.n-1] = None
        self.n = self.n - 1
        return v
    
class Node:
    def __init__(self, v):
        self.value = v
        self.next = None

class LinkList:
    def __init__(self):
        self.head=None
        self.tail=None
        self.n = 0
        self. steps = 0

    def len(self):
        return self.n
    
    def append(self, v):
        nd = Node(v)
        if self.tail == None:
           self.tail = self.head = nd
        else:
            self.tail.next = nd
            self.tail = nd
        self.n = self.n + 1
    
    def prepend(self ,v):
        nd = Node(v)
        nd.next = self.head
        self.head = nd
        if self.tail == None:
           self.tail = nd
        self.n = self.n + 1

    def get(self, i):
        nilai = self.head
        for k in range (i):
            nilai = nilai.next
            self.steps = self.steps + 1
        return nilai.value
    
    def insert(self, i, v):
        if i == 0:
            return self.prepend(v)
        before = self.head
        if i == self.n:
            return self.append(v)
        for k in range (i-1):
            before = before.next
            self.steps = self.steps + 1
        nd = Node(v)
        nd.next = before.next
        before.next = nd
        self.n = self.n + 1
    
    def delete(self, i):
        if i == 0:
            v = self.head.value
            if self.n == 1:
                self.head = self.tail = None
            else:
                self.head = self.head.next
        else:
            before = self.head
            for n in range (i-1):
                before = before.next
                self.steps = self.steps + 1
            trash = before.next
            v = trash.value
            before.next = trash.next
            if trash == self.tail:
                self.tail = before
        self.n = self.n - 1
        return v





    


#test

