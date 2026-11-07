# Actual property-topic runs — final audit

Fresh real generation on 7 November 2026 through Streamlit AppTest and the local model. English and Indonesian shown below are saved generated output. Synthetic briefing figures are not real market data. Audit answers were selected programmatically, with the first deliberately wrong. These are functional checks, not employee attempts or an accuracy benchmark.

## Evergreen rental yield

Created (UTC): 2026-11-07T09:32:07+00:00

Model: gemma-4-12b — Gemma 4 12B QAT via llama.cpp CUDA b12182, POST /v1/chat/completions.

Input:

```text
{
  "topic": "Calculating hypothetical property rental yield using an explicitly stated annual-rent divided by purchase-price formula",
  "reference_notes": "",
  "count": 2
}
```

Generated output and key:

```text
1. In a hypothetical scenario, a property is purchased for Rp 1,000,000,000 and generates an annual rent of Rp 50,000,000. Using the formula (Annual Rent / Purchase Price) * 100, what is the rental yield?
Dalam skenario hipotetis, sebuah properti dibeli seharga Rp 1.000.000.000 dan menghasilkan sewa tahunan sebesar Rp 50.000.000. Menggunakan rumus (Sewa Tahunan / Harga Beli) * 100, berapakah hasil sewa (rental yield) tersebut?
A. 10%
   10%
B. 50%
   50%
C. 1%
   1%
D. 5%
   5%
Answer: D. 5%
Explanation: The calculation is (50,000,000 / 1,000,000,000) * 100, which equals 5%.
Penjelasan: Perhitungannya adalah (50.000.000 / 1.000.000.000) * 100, yang menghasilkan 5%.

2. In a hypothetical scenario, a property has a purchase price of Rp 2,500,000,000. If the annual rent is Rp 150,000,000, what is the rental yield based on the formula (Annual Rent / Purchase Price) * 100?
Dalam skenario hipotetis, sebuah properti memiliki harga beli Rp 2.500.000.000. Jika sewa tahunannya adalah Rp 150.000.000, berapakah hasil sewa (rental yield) berdasarkan rumus (Sewa Tahunan / Harga Beli) * 100?
A. 4%
   4%
B. 15%
   15%
C. 8%
   8%
D. 6%
   6%
Answer: D. 6%
Explanation: The calculation is (150,000,000 / 2,500,000,000) * 100, which equals 6%.
Penjelasan: Perhitungannya adalah (150.000.000 / 2.500.000.000) * 100, yang menghasilkan 6%.
```

Audit attempt: 1/2; 14.89 seconds.

## Dated synthetic Jakarta briefing

Created (UTC): 2026-11-07T09:32:37+00:00

Model: gemma-4-12b — Gemma 4 12B QAT via llama.cpp CUDA b12182, POST /v1/chat/completions.

Input:

```text
{
  "topic": "Reading a fictional Jakarta property briefing dated 7 November 2026: calculate changes, distinguish asking from sale prices, and respect the dataset scope caref",
  "reference_notes": "RINGKASAN PELATIHAN FIKTIF ? bukan berita atau data pasar Jakarta yang sebenarnya. Seluruh angka berikut dibuat untuk latihan membaca laporan, bukan untuk mengambil keputusan investasi. Periode contoh adalah September dan Oktober 2026, dengan cakupan Wilayah A saja.\n\nMedian harga penawaran di Wilayah A adalah Rp2.0 miliar pada September dan Rp2.1 miliar pada Oktober. Iklan properti baru turun dari 100 menjadi 80. Jumlah pertanyaan calon pembeli naik dari 200 menjadi 240. Data mencatat harga yang diiklankan, bukan harga transaksi penjualan yang sudah selesai. Tidak ada kesimpulan sebab-akibat yang ditetapkan dalam ringkasan ini.\n\nTim menggunakan definisi tingkat konversi kunjungan sebagai jumlah kunjungan yang terlaksana dibagi jumlah pertanyaan calon pembeli yang memenuhi kriteria. Dalam kampanye pelatihan terpisah, ada 80 pertanyaan yang memenuhi kriteria dan 20 kunjungan terlaksana. Angka kampanye ini tidak boleh dicampur dengan jumlah pertanyaan pasar Wilayah A karena kelompok pengamatannya berbeda.\n\nPembaca diminta memperhatikan penyebut ketika menghitung persentase perubahan. Kenaikan selalu dibandingkan dengan nilai pada awal periode. Penurunan jumlah iklan tidak dengan sendirinya membuktikan bahwa pasokan rumah di seluruh kota ikut turun, karena laporan ini hanya memantau iklan baru dalam satu wilayah. Tidak tersedia jumlah seluruh rumah, stok aktif kumulatif, atau proyek pembangunan baru.\n\nLaporan juga tidak mencatat pendapatan rumah tangga, keputusan bank, tingkat bunga, aturan pajak, atau kebijakan pemerintah. Karena variabel tersebut tidak ada, pembaca tidak boleh menambahkan klaim mengenai perubahan regulasi atau kemampuan pembeli mendapatkan pinjaman. Pertanyaan latihan harus dapat dijawab dari angka dan definisi yang tertulis, tanpa menebak kondisi ekonomi nyata.\n\nUntuk latihan mencocokkan kebutuhan, seorang pembeli hipotetis mensyaratkan minimal 3 kamar tidur, harga maksimal Rp2.5 miliar, dan balkon. Unit P memiliki 3 kamar tidur, harga Rp2.4 miliar, dan balkon. Unit Q memiliki 2 kamar tidur, harga Rp2.2 miliar, dan balkon. Unit R memiliki 4 kamar tidur dan balkon, tetapi berharga Rp2.8 miliar. Unit S memiliki 3 kamar tidur dengan harga Rp2.3 miliar, tetapi tanpa balkon.\n\nSetiap syarat harus diperiksa secara bersamaan, bukan dipilih berdasarkan kesan umum terhadap properti. Satu kelebihan tidak menggantikan syarat wajib yang tidak terpenuhi. Label unit hanya digunakan untuk membedakan pilihan dalam skenario, bukan menunjukkan peringkat kualitas atau rekomendasi pembelian.\n\nCatatan kualitas data: median merupakan nilai tengah dalam kumpulan data yang diurutkan. Perubahan median harga penawaran tidak membuktikan bahwa setiap rumah mengalami kenaikan harga dengan besaran yang sama.                                                                                                                                                                                                                                                                  ",
  "count": 5
}
```

Generated output and key:

```text
1. Based on the briefing, what is the percentage increase in the median asking price in Region A from September to October?
Berdasarkan ringkasan, berapa persentase kenaikan median harga penawaran di Wilayah A dari September ke Oktober?
A. 15%
   15%
B. 10%
   10%
C. 20%
   20%
D. 5%
   5%
Answer: D. 5%
Explanation: The price increased from Rp2.0 billion to Rp2.1 billion, which is a 5% increase from the initial value.
Penjelasan: Harga naik dari Rp2,0 miliar menjadi Rp2,1 miliar, yang merupakan kenaikan 5% dari nilai awal.

2. In the separate training campaign, what is the conversion rate of visits based on the provided definition?
Dalam kampanye pelatihan terpisah, berapa tingkat konversi kunjungan berdasarkan definisi yang diberikan?
A. 80%
   80%
B. 25%
   25%
C. 40%
   40%
D. 20%
   20%
Answer: B. 25%
Explanation: The conversion rate is 20 visits divided by 80 qualified inquiries, which equals 25%.
Penjelasan: Tingkat konversi adalah 20 kunjungan dibagi 80 pertanyaan yang memenuhi kriteria, yang sama dengan 25%.

3. Which unit matches all the requirements of a hypothetical buyer seeking at least 3 bedrooms, a maximum price of Rp2.5 billion, and a balcony?
Unit mana yang memenuhi semua persyaratan pembeli hipotetis yang menginginkan minimal 3 kamar tidur, harga maksimal Rp2,5 miliar, dan balkon?
A. Unit Q
   Unit Q
B. Unit S
   Unit S
C. Unit P
   Unit P
D. Unit R
   Unit R
Answer: C. Unit P
Explanation: Unit P meets all three criteria: 3 bedrooms, Rp2.4 billion, and a balcony.
Penjelasan: Unit P memenuhi ketiga kriteria: 3 kamar tidur, Rp2,4 miliar, dan balkon.

4. According to the briefing, what is the specific decrease in the number of new property listings in Region A?
Menurut ringkasan, berapa penurunan spesifik jumlah iklan properti baru di Wilayah A?
A. 100
   100
B. 20
   20
C. 10
   10
D. 80
   80
Answer: B. 20
Explanation: The number of new listings dropped from 100 to 80, resulting in a decrease of 20.
Penjelasan: Jumlah iklan baru turun dari 100 menjadi 80, menghasilkan penurunan sebesar 20.

5. Which of the following statements is NOT supported by the data in the briefing?
Manakah dari pernyataan berikut yang TIDAK didukung oleh data dalam ringkasan?
A. The median price in October was higher than September.
   Median harga di bulan Oktober lebih tinggi dari September.
B. The decrease in listings proves a city-wide supply drop.
   Penurunan iklan membuktikan penurunan pasokan di seluruh kota.
C. The number of inquiries increased in Region A.
   Jumlah pertanyaan meningkat di Wilayah A.
D. The conversion rate for the training campaign was 25%.
   Tingkat konversi untuk kampanye pelatihan adalah 25%.
Answer: B. The decrease in listings proves a city-wide supply drop.
Explanation: The briefing explicitly states that a decrease in listings in one region does not prove a city-wide supply drop.
Penjelasan: Ringkasan secara eksplisit menyatakan bahwa penurunan iklan di satu wilayah tidak membuktikan penurunan pasokan di seluruh kota.
```

Audit attempt: 4/5; 30.34 seconds.
