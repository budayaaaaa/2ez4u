from M1_pesanan import Array

class Stack:
    def __init__(self):
        self.items = Array()

    def size(self):
        return self.items.len()
    
    def push(self, x):
        return self.items.append(x)
    
    def pop(self):
        if self.items.len() == 0:
            return None
        return self.items.delete(self.items.len() - 1)

    def peek(self):
        return self.items.get(self.items.len() - 1)
    
    def kosong(self):
        return self.items.len() == 0
    
def adalah_angka(teks):
    return teks[0] >= "0" and teks[0] <= "9"


def adalah_operator(teks):
    return teks == "+" or teks == "-" or teks == "*" or teks == "/"


def prioritas(operator):
    if operator == "*" or operator == "/":
        return 2
    if operator == "+" or operator == "-":
        return 1
    return 0


def pecah_token(ekspresi):
    token = Array()
    angka = ""

    for huruf in ekspresi:
        if adalah_angka(huruf):
            angka = angka + huruf
        else:
            if angka != "":
                token.append(angka)
                angka = ""

            if huruf == " ":
                pass
            elif adalah_operator(huruf) or huruf == "(" or huruf == ")":
                token.append(huruf)
            else:
                raise ValueError("karakter tidak dikenal: " + huruf)

    if angka != "":
        token.append(angka)

    if token.len() == 0:
        raise ValueError("ekspresi kosong")

    return token


def ke_postfix(ekspresi):
    token = pecah_token(ekspresi)
    stack = Stack()
    hasil = Array()

    for i in range(token.len()):
        t = token.get(i)

        if adalah_angka(t):
            hasil.append(t)

        elif t == "(":
            stack.push(t)

        elif t == ")":
            while not stack.kosong() and stack.peek() != "(":
                hasil.append(stack.pop())
            if stack.kosong():
                raise ValueError("kurung tutup tidak punya pasangan")
            stack.pop()

        else:
            while not stack.kosong() and prioritas(stack.peek()) >= prioritas(t):
                hasil.append(stack.pop())
            stack.push(t)

    while not stack.kosong():
        operator = stack.pop()
        if operator == "(":
            raise ValueError("kurung buka tidak ditutup")
        hasil.append(operator)

    return hasil


def hitung(postfix):
    stack = Stack()

    for i in range(postfix.len()):
        t = postfix.get(i)

        if adalah_angka(t):
            stack.push(int(t))
        else:
            if stack.size() < 2:
                raise ValueError("angka kurang untuk operator " + t)

            kanan = stack.pop()
            kiri = stack.pop()

            if t == "+":
                stack.push(kiri + kanan)
            elif t == "-":
                stack.push(kiri - kanan)
            elif t == "*":
                stack.push(kiri * kanan)
            elif t == "/":
                if kanan == 0:
                    raise ValueError("tidak bisa membagi dengan nol")
                stack.push(kiri // kanan)

    if stack.size() != 1:
        raise ValueError("ekspresi tidak valid")

    return stack.pop()

class Queue:
    def __init__(self):
        self.items = Array()
    
    def enqueue(self, v):
        return self.items.append(v)
    
    def dequeue(self):
        if self.items.len() == 0:
            return None
        return self.items.delete(0)
    
    def len(self):
        return self.items.len()
    
class CircularQueue:
    def __init__(self, kapasitas = 4):
        self.data = [None]*kapasitas
        self.capacity = kapasitas
        self.front = 0
        self.rear = 0
        self.count = 0
        self.geser = 0
        self.salin = 0

    def len(self):
        return self.count
    
    def ambil(self, j):
        return self.data[(self.front + j) % self.capacity]
    
    def grow(self):
        baru = [None]*2*self.capacity
        for j in range (self.count):
            baru[j] = self.data[(self.front + j) % self.capacity]
            self.salin = self.salin + 1
        self.data = baru
        self.capacity = self.capacity*2
        self.front = 0
        self.rear = self.count
    
    def enqueue(self, v):
        if self.count == self.capacity:
            self.grow()
        self.data[self.rear] = v
        self.rear = self.rear + 1 % self.capacity
        self.count = self.count + 1
    
    def dequeue(self):
        if self.count == 0:
            return None
        v = self.data[self.front]
        self.data[self.front] = None
        self.front = (self.front + 1) % self.capacity
        self.count = self.count -1
        return v
    
    def enqueue_front(self, v):
        if self.count == self.capacity:
            self.grow()
        self.front = (self.front - 1) % self.capacity
        self.data[self.front] = v
        self.count = self.count + 1

    def dequeue_back(self):
        if self.count == 0:
            return None
        self.rear = (self.rear - 1) % self.capacity
        v = self.data[self.rear]
        self.data[self.rear] = None
        self.count = self.count - 1
        return v
    
class Riwayat:
    def __init__(self):
        self.undo = Stack()
        self.redo = Stack()

    def undo_len(self):
        return self.undo.size()

    def redo_len(self):
        return self.redo.size()

    def catat(self, aksi):
        self.undo.push(aksi)
        self.redo = Stack()

    def pilih_antrean(self, nama, q_naif, q_circular):
        if nama == "naif":
            return q_naif
        return q_circular

    def undo_last(self, q_naif, q_circular):
        if self.undo.kosong():
            return None

        aksi = self.undo.pop()
        jenis = aksi[0]

        if jenis == "ENQUEUE":
            pesanan = aksi[1]
            q_naif.dequeue_back()
            q_circular.dequeue_back()
            pesan = "Undo enqueue: " + pesanan[0] + " dikeluarkan lagi dari belakang."
        else:
            nama = aksi[1]
            daftar = aksi[2]
            antrean = self.pilih_antrean(nama, q_naif, q_circular)
            i = daftar.len() - 1
            while i >= 0:
                antrean.enqueue_front(daftar.get(i))
                i = i - 1
            pesan = "Undo dequeue " + nama + ": " + str(daftar.len()) + " pesanan dikembalikan ke depan."

        self.redo.push(aksi)
        return pesan + " Undo " + str(self.undo_len()) + ", redo " + str(self.redo_len()) + "."

    def redo_last(self, q_naif, q_circular):
        if self.redo.kosong():
            return None

        aksi = self.redo.pop()
        jenis = aksi[0]

        if jenis == "ENQUEUE":
            pesanan = aksi[1]
            q_naif.enqueue(pesanan)
            q_circular.enqueue(pesanan)
            pesan = "Redo enqueue: " + pesanan[0] + " masuk lagi ke belakang."
        else:
            nama = aksi[1]
            daftar = aksi[2]
            antrean = self.pilih_antrean(nama, q_naif, q_circular)
            for i in range(daftar.len()):
                antrean.dequeue()
            pesan = "Redo dequeue " + nama + ": " + str(daftar.len()) + " pesanan keluar lagi dari depan."

        self.undo.push(aksi)
        return pesan + " Undo " + str(self.undo_len()) + ", redo " + str(self.redo_len()) + "."

    def history(self):
        hasil = Array()
        for i in range(self.undo.size()):
            aksi = self.undo.get(i)
            if aksi[0] == "ENQUEUE":
                hasil.append("ENQUEUE " + aksi[1][0])
            else:
                hasil.append("DEQUEUE " + aksi[1] + " x" + str(aksi[2].len()))
        return hasil




