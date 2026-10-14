BATAS_INSERTION = 20000

class Pencacah:
    def __init__(self):
        self.perbandingan = 0
        self.pemindahan = 0


def nilai_kunci(pesanan, kunci):
    if kunci == "harga":
        return int(pesanan[4])
    if kunci == "selesai":
        if pesanan[7] == "":
            return 999999
        return int(pesanan[7])
    return pesanan[0]


def insertion_sort(daftar, kunci):
    hitung = Pencacah()

    for i in range(1, len(daftar)):
        sekarang = daftar[i]
        nilai_sekarang = nilai_kunci(sekarang, kunci)
        j = i - 1

        while j >= 0:
            hitung.perbandingan = hitung.perbandingan + 1
            if nilai_kunci(daftar[j], kunci) > nilai_sekarang:
                daftar[j + 1] = daftar[j]
                hitung.pemindahan = hitung.pemindahan + 1
                j = j - 1
            else:
                break

        daftar[j + 1] = sekarang
        hitung.pemindahan = hitung.pemindahan + 1

    return hitung


def merge_sort(daftar, kunci):
    hitung = Pencacah()
    if len(daftar) > 1:
        urutkan_bagian(daftar, 0, len(daftar) - 1, kunci, hitung)
    return hitung


def urutkan_bagian(daftar, kiri, kanan, kunci, hitung):
    if kiri >= kanan:
        return
    tengah = (kiri + kanan) // 2
    urutkan_bagian(daftar, kiri, tengah, kunci, hitung)
    urutkan_bagian(daftar, tengah + 1, kanan, kunci, hitung)
    gabung(daftar, kiri, tengah, kanan, kunci, hitung)


def gabung(daftar, kiri, tengah, kanan, kunci, hitung):
    bagian_kiri = []
    for i in range(kiri, tengah + 1):
        bagian_kiri.append(daftar[i])

    bagian_kanan = []
    for i in range(tengah + 1, kanan + 1):
        bagian_kanan.append(daftar[i])

    i = 0
    j = 0
    k = kiri

    while i < len(bagian_kiri) and j < len(bagian_kanan):
        hitung.perbandingan = hitung.perbandingan + 1
        if nilai_kunci(bagian_kiri[i], kunci) <= nilai_kunci(bagian_kanan[j], kunci):
            daftar[k] = bagian_kiri[i]
            i = i + 1
        else:
            daftar[k] = bagian_kanan[j]
            j = j + 1
        k = k + 1
        hitung.pemindahan = hitung.pemindahan + 1

    while i < len(bagian_kiri):
        daftar[k] = bagian_kiri[i]
        i = i + 1
        k = k + 1
        hitung.pemindahan = hitung.pemindahan + 1

    while j < len(bagian_kanan):
        daftar[k] = bagian_kanan[j]
        j = j + 1
        k = k + 1
        hitung.pemindahan = hitung.pemindahan + 1


def linear_search(daftar, target):
    perbandingan = 0
    for i in range(len(daftar)):
        perbandingan = perbandingan + 1
        if daftar[i][0] == target:
            return i, perbandingan
    return -1, perbandingan


def binary_search(daftar, target):
    perbandingan = 0
    lo = 0
    hi = len(daftar) - 1

    while lo <= hi:
        mid = (lo + hi) // 2
        oid_tengah = daftar[mid][0]
        perbandingan = perbandingan + 1

        if oid_tengah == target:
            return mid, perbandingan
        elif oid_tengah < target:
            lo = mid + 1
        else:
            hi = mid - 1

    return -1, perbandingan
