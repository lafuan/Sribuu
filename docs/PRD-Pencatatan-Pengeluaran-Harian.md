# Business Requirements Document (PRD Mini)
# Aplikasi Web: Pencatatan Pengeluaran Harian

---

## Daftar Isi
1. [Pertanyaan Klarifikasi & Asumsi](#1-pertanyaan-klarifikasi--asumsi)
2. [User Stories](#2-user-stories)
3. [Acceptance Criteria per User Story](#3-acceptance-criteria-per-user-story)
4. [Prioritas & Roadmap Rilis](#4-prioritas--roadmap-rilis)
5. [Daftar Fitur/Kemampuan Aplikasi](#5-daftar-fiturkemampuan-aplikasi)
6. [Batasan & Non-Functional Requirements](#6-batasan--non-functional-requirements)

---

## 1. Pertanyaan Klarifikasi & Asumsi

Berikut adalah daftar pertanyaan klarifikasi yang idealnya ditanyakan kepada stakeholder/user sebelum pengembangan dimulai. Karena user tidak tersedia, kami menetapkan **jawaban asumsi yang masuk akal** (reasonable defaults) untuk setiap pertanyaan.

### 1.1 — Autentikasi & Multi-User

| # | Pertanyaan Klarifikasi | Asumsi (Jawaban Default) |
|---|---|---|
| Q1 | Apakah aplikasi perlu login/register? | **Ya.** Meskipun target awal personal use, setiap user harus memiliki akun terpisah agar data pribadi tidak tercampur dan siap untuk skenario multi-user di masa depan. |
| Q2 | Apakah perlu login dengan Google/SSO atau cukup email+password? | **Email + password saja** untuk MVP. Login sosial (Google) dapat ditambahkan di rilis berikutnya. |
| Q3 | Apakah ada kebutuhan "family sharing" (satu household, banyak user lihat data bersama)? | **Tidak untuk MVP.** Fitur sharing dapat dipertimbangkan jika ada permintaan di masa depan. |
| Q4 | Apakah perlu role-based access (admin vs user biasa)? | **Tidak.** Semua user memiliki hak yang sama atas data mereka sendiri. Tidak ada hierarki. |

### 1.2 — Data Transaksi & Kategori

| # | Pertanyaan Klarifikasi | Asumsi (Jawaban Default) |
|---|---|---|
| Q5 | Field apa saja yang wajib saat input transaksi? | **Jumlah (amount), kategori, tanggal.** Catatan/deskripsi bersifat opsional. |
| Q6 | Apakah user bisa membuat kategori sendiri (custom) atau hanya dari daftar tetap? | **Keduanya.** Sistem menyediakan daftar kategori default (Makanan, Transportasi, Belanja, dll.), dan user dapat menambah, mengedit, atau menghapus kategori kustom miliknya. Kategori default tidak bisa dihapus, hanya bisa dinonaktifkan/disembunyikan. |
| Q7 | Apakah satu transaksi bisa memiliki lebih dari satu kategori (split)? | **Tidak untuk MVP.** Satu transaksi = satu kategori. Fitur split dapat ditambahkan nanti. |
| Q8 | Apakah perlu mencatat metode pembayaran (cash, debit, kredit, e-wallet)? | **Ya, opsional.** Field metode pembayaran tersedia tapi tidak wajib diisi. Ini membantu untuk analisis kebiasaan belanja. |
| Q9 | Apakah perlu upload bukti/foto struk? | **Tidak untuk MVP.** Dapat dipertimbangkan di rilis berikutnya jika ada permintaan. |
| Q10 | Apakah transaksi bisa diedit atau dihapus setelah dibuat? | **Ya.** User dapat mengedit semua field transaksi dan menghapus transaksi yang salah input. |
| Q11 | Apakah perlu soft-delete (recycle bin) atau langsung hard-delete? | **Hard-delete dengan konfirmasi.** Tidak perlu recycle bin untuk MVP. |

### 1.3 — Tampilan & Ringkasan

| # | Pertanyaan Klarifikasi | Asumsi (Jawaban Default) |
|---|---|---|
| Q12 | Ringkasan/statistik apa yang paling dibutuhkan user? | **Total pengeluaran per bulan, pengeluaran per kategori (pie chart), dan tren harian/mingguan (bar chart).** Ini adalah tiga visualisasi paling umum untuk personal finance tracking. |
| Q13 | Apakah perlu membandingkan dengan budget/anggaran? | **Tidak untuk MVP.** Fitur budgeting (set budget per kategori, alert jika melebihi) bisa ditambahkan di rilis berikutnya. |
| Q14 | Apakah perlu filter dan pencarian di riwayat transaksi? | **Ya.** Filter berdasarkan rentang tanggal, kategori, dan metode pembayaran. Pencarian teks pada kolom catatan/deskripsi. |
| Q15 | Apakah user bisa export data (CSV, PDF)? | **Export CSV untuk MVP.** PDF report bisa di rilis berikutnya. |

### 1.4 — Perilaku & UX

| # | Pertanyaan Klarifikasi | Asumsi (Jawaban Default) |
|---|---|---|
| Q16 | Apakah aplikasi perlu mobile-friendly (responsif)? | **Ya.** Aplikasi web responsif yang nyaman digunakan di HP, karena user kemungkinan besar input pengeluaran saat di perjalanan (setelah belanja, makan, dll.). |
| Q17 | Apakah perlu input cepat (quick-add) tanpa banyak form? | **Ya.** Ada mode "input cepat" di halaman utama/dashboard: cukup isi jumlah, pilih kategori, dan simpan (tanggal otomatis hari ini). Field lain opsional. |
| Q18 | Apakah perlu dark mode? | **Tidak untuk MVP.** Bisa dipertimbangkan nanti. |
| Q19 | Apakah perlu notifikasi/pengingat untuk input pengeluaran? | **Tidak untuk MVP.** Bisa dipertimbangkan nanti. |
| Q20 | Bahasa antarmuka: Indonesia saja atau bilingual (ID/EN)? | **Bahasa Indonesia saja** untuk MVP. |

### 1.5 — Teknis & Operasional

| # | Pertanyaan Klarifikasi | Asumsi (Jawaban Default) |
|---|---|---|
| Q21 | Berapa ekspektasi jumlah transaksi per user per bulan? | **~60–200 transaksi/bulan** (rata-rata 2–7 transaksi/hari). Ini pemakaian wajar individu. |
| Q22 | Berapa lama data historis perlu disimpan? | **Selamanya/tanpa batas waktu.** User dapat menghapus data sendiri jika ingin. Sistem tidak menghapus otomatis. |
| Q23 | Apakah ada kebutuhan backup data oleh user sendiri? | **Ya, via fitur export CSV.** Tidak perlu backup otomatis tersendiri untuk MVP. |

---

## 2. User Stories

Format: **"Sebagai [jenis pengguna], saya ingin [fitur/aksi] sehingga [manfaat/tujuan]."**

### US-01: Registrasi Akun
> Sebagai **pengguna baru**, saya ingin **mendaftar akun dengan email dan password** sehingga **saya dapat memiliki akses pribadi ke aplikasi dan data saya tersimpan aman.**

### US-02: Login & Logout
> Sebagai **pengguna terdaftar**, saya ingin **login dengan email dan password saya** sehingga **saya dapat mengakses data pengeluaran pribadi saya kapan saja.**

### US-03: Input Cepat Transaksi (Quick Add)
> Sebagai **pengguna**, saya ingin **mencatat pengeluaran dengan cepat hanya dengan memasukkan jumlah dan memilih kategori** sehingga **saya tidak repot mengisi banyak form saat sedang di perjalanan atau terburu-buru.**

### US-04: Input Transaksi Lengkap
> Sebagai **pengguna**, saya ingin **mencatat transaksi dengan detail lengkap: jumlah, kategori, tanggal, catatan, dan metode pembayaran** sehingga **saya dapat mendokumentasikan pengeluaran secara lebih rinci saat diperlukan.**

### US-05: Melihat Riwayat Transaksi
> Sebagai **pengguna**, saya ingin **melihat daftar seluruh transaksi saya yang terurut dari terbaru** sehingga **saya dapat meninjau kembali pengeluaran saya.**

### US-06: Filter & Cari Riwayat
> Sebagai **pengguna**, saya ingin **memfilter riwayat transaksi berdasarkan rentang tanggal, kategori, dan metode pembayaran, serta mencari berdasarkan kata kunci di catatan** sehingga **saya dapat dengan mudah menemukan transaksi spesifik.**

### US-07: Edit Transaksi
> Sebagai **pengguna**, saya ingin **mengedit transaksi yang sudah tercatat (jumlah, kategori, tanggal, catatan, metode pembayaran)** sehingga **saya dapat memperbaiki kesalahan input tanpa harus menghapus dan membuat ulang.**

### US-08: Hapus Transaksi
> Sebagai **pengguna**, saya ingin **menghapus transaksi yang tidak diperlukan** sehingga **data pengeluaran saya tetap rapi dan akurat.**

### US-09: Ringkasan Pengeluaran Bulanan
> Sebagai **pengguna**, saya ingin **melihat total pengeluaran saya untuk bulan berjalan dan bulan-bulan sebelumnya** sehingga **saya dapat memantau pola pengeluaran dari waktu ke waktu.**

### US-10: Statistik per Kategori (Pie Chart)
> Sebagai **pengguna**, saya ingin **melihat persentase pengeluaran per kategori dalam bentuk diagram pie** sehingga **saya dapat mengidentifikasi pos pengeluaran terbesar saya.**

### US-11: Tren Pengeluaran Harian/Mingguan (Bar Chart)
> Sebagai **pengguna**, saya ingin **melihat grafik batang pengeluaran harian dalam satu minggu atau satu bulan** sehingga **saya dapat melihat hari-hari dengan pengeluaran tertinggi.**

### US-12: Kelola Kategori Kustom
> Sebagai **pengguna**, saya ingin **menambah, mengedit, dan menghapus kategori pengeluaran buatan saya sendiri** sehingga **kategori yang tersedia sesuai dengan kebutuhan dan gaya hidup saya.**

### US-13: Lihat Kategori Default
> Sebagai **pengguna**, saya ingin **melihat daftar kategori default yang sudah disediakan sistem** sehingga **saya bisa langsung menggunakannya tanpa harus membuat dari nol.**

### US-14: Export Data ke CSV
> Sebagai **pengguna**, saya ingin **mengunduh data transaksi saya dalam format CSV** sehingga **saya bisa membuka dan menganalisis data di spreadsheet (Excel/Google Sheets) atau menyimpannya sebagai backup pribadi.**

### US-15: Dashboard Ringkasan
> Sebagai **pengguna**, saya ingin **melihat halaman dashboard yang menampilkan ringkasan pengeluaran hari ini, bulan ini, dan kategori terbesar** sehingga **saya bisa langsung mendapat gambaran kondisi keuangan saya begitu membuka aplikasi.**

### US-16: Ganti Password
> Sebagai **pengguna**, saya ingin **mengganti password akun saya** sehingga **saya dapat menjaga keamanan akun saya.**

---

## 3. Acceptance Criteria per User Story

### US-01: Registrasi Akun
- [ ] User dapat mengakses halaman registrasi (`/register`)
- [ ] Form registrasi meminta: nama, email, password, konfirmasi password
- [ ] Validasi: email harus format valid dan belum terdaftar
- [ ] Validasi: password minimal 6 karakter
- [ ] Validasi: password dan konfirmasi password harus sama
- [ ] Setelah registrasi berhasil, user otomatis login dan diarahkan ke dashboard
- [ ] Jika validasi gagal, pesan error jelas ditampilkan di dekat field terkait

### US-02: Login & Logout
- [ ] User dapat mengakses halaman login (`/login`)
- [ ] Form login meminta: email, password
- [ ] Kredensial salah menampilkan pesan error generik ("Email atau password salah")
- [ ] Login berhasil mengarahkan user ke dashboard
- [ ] User dapat logout via tombol/logout, session dihapus, kembali ke halaman login
- [ ] User yang sudah login dan mengakses `/login` atau `/register` langsung dialihkan ke dashboard
- [ ] User yang belum login tidak bisa mengakses halaman dalam aplikasi (redirect ke login)

### US-03: Input Cepat Transaksi (Quick Add)
- [ ] Di halaman dashboard, tersedia form input cepat yang minimal
- [ ] Field yang tampil: jumlah (wajib), dropdown kategori (wajib)
- [ ] Tanggal otomatis terisi hari ini (bisa diubah jika perlu)
- [ ] Tombol "Simpan" langsung menyimpan transaksi
- [ ] Setelah simpan, form reset dan siap input berikutnya
- [ ] Notifikasi sukses singkat muncul (toast/alert)

### US-04: Input Transaksi Lengkap
- [ ] Tersedia halaman/form "Tambah Transaksi" (`/transactions/new`)
- [ ] Field: jumlah (wajib, numerik), kategori (wajib, dropdown/searchable), tanggal (wajib, date picker, default hari ini), catatan (opsional, text), metode pembayaran (opsional, dropdown: Tunai, Debit, Kredit, E-Wallet, Transfer Bank)
- [ ] Validasi: jumlah harus > 0, tidak boleh negatif
- [ ] Setelah simpan, user diarahkan ke riwayat transaksi dengan notifikasi sukses

### US-05: Melihat Riwayat Transaksi
- [ ] Halaman riwayat transaksi menampilkan daftar seluruh transaksi user
- [ ] Default terurut dari transaksi terbaru (tanggal descending)
- [ ] Setiap item menampilkan: tanggal, kategori, jumlah, catatan (jika ada), ikon metode pembayaran
- [ ] Pagination: misal 25 transaksi per halaman
- [ ] Total pengeluaran untuk hasil yang ditampilkan muncul di bagian atas/bawah

### US-06: Filter & Cari Riwayat
- [ ] Filter rentang tanggal: "Dari" dan "Sampai" dengan date picker
- [ ] Filter kategori: dropdown multi-select atau single-select
- [ ] Filter metode pembayaran: dropdown
- [ ] Pencarian teks: mencari pada kolom catatan/deskripsi
- [ ] Filter dan pencarian dapat dikombinasikan
- [ ] Hasil filter langsung diperbarui (via tombol "Terapkan" atau otomatis)
- [ ] Tombol "Reset" untuk menghapus semua filter
- [ ] Saat tidak ada hasil, tampilkan pesan "Tidak ada transaksi ditemukan"

### US-07: Edit Transaksi
- [ ] Di setiap item riwayat transaksi, tersedia tombol/ikon "Edit"
- [ ] Klik edit membuka form dengan data existing sudah terisi
- [ ] Semua field bisa diubah (jumlah, kategori, tanggal, catatan, metode pembayaran)
- [ ] Validasi yang sama dengan input transaksi baru berlaku
- [ ] Setelah simpan, kembali ke riwayat dengan notifikasi sukses
- [ ] Data yang diubah langsung tercermin di riwayat dan statistik

### US-08: Hapus Transaksi
- [ ] Di setiap item riwayat transaksi, tersedia tombol/ikon "Hapus"
- [ ] Klik hapus menampilkan dialog konfirmasi: "Apakah Anda yakin ingin menghapus transaksi ini?"
- [ ] Konfirmasi "Ya, Hapus" → transaksi terhapus permanen, notifikasi sukses
- [ ] Konfirmasi "Batal" → dialog tertutup, tidak ada perubahan
- [ ] Data yang dihapus tidak muncul lagi di riwayat dan statistik

### US-09: Ringkasan Pengeluaran Bulanan
- [ ] Halaman statistik menampilkan total pengeluaran bulan berjalan
- [ ] User dapat memilih bulan dan tahun untuk melihat total bulan lain
- [ ] Perbandingan dengan bulan sebelumnya (opsional: persentase naik/turun)
- [ ] Jika belum ada transaksi di bulan yang dipilih, tampilkan "Belum ada transaksi"

### US-10: Statistik per Kategori (Pie Chart)
- [ ] Diagram pie menampilkan distribusi pengeluaran per kategori
- [ ] Rentang waktu sesuai filter (default: bulan berjalan)
- [ ] Setiap irisan pie menampilkan nama kategori, persentase, dan nominal
- [ ] Warna setiap kategori konsisten
- [ ] Jika hanya ada satu kategori, diagram tetap dirender dengan benar (bukan error)

### US-11: Tren Pengeluaran Harian/Mingguan (Bar Chart)
- [ ] Grafik batang menampilkan total pengeluaran per hari dalam rentang waktu terpilih
- [ ] Default: 7 hari terakhir (mingguan)
- [ ] User bisa switch ke tampilan 30 hari (bulanan)
- [ ] Sumbu X: tanggal/hari, sumbu Y: jumlah (Rupiah)
- [ ] Tooltip menampilkan detail saat hover/tap pada batang

### US-12: Kelola Kategori Kustom
- [ ] Halaman Pengaturan > Kategori menampilkan daftar semua kategori (default + kustom)
- [ ] Kategori kustom bisa ditambah (nama, ikon/emoji opsional, warna opsional)
- [ ] Kategori kustom bisa diedit (nama, ikon, warna)
- [ ] Kategori kustom bisa dihapus — dengan konfirmasi
- [ ] Kategori default tidak bisa dihapus, hanya bisa "disembunyikan"
- [ ] Kategori yang sedang digunakan oleh transaksi tidak bisa dihapus (tampilkan error: "Kategori sedang digunakan oleh X transaksi")
- [ ] Nama kategori tidak boleh duplikat dalam scope user yang sama

### US-13: Lihat Kategori Default
- [ ] Saat pertama kali login, user sudah melihat daftar kategori default
- [ ] Kategori default yang disarankan: Makanan & Minuman, Transportasi, Belanja, Tagihan & Utilitas, Hiburan, Kesehatan, Pendidikan, Pakaian, Rumah Tangga, Lain-lain

### US-14: Export Data ke CSV
- [ ] Tombol "Export CSV" tersedia di halaman riwayat transaksi
- [ ] Klik export mengunduh file CSV dengan data sesuai filter yang sedang aktif
- [ ] Nama file: `pengeluaran_[YYYY-MM-DD].csv`
- [ ] Kolom CSV: Tanggal, Kategori, Jumlah, Metode Pembayaran, Catatan
- [ ] Format encoding: UTF-8 (mendukung karakter Indonesia)
- [ ] Jika tidak ada transaksi sesuai filter, tombol export disable dengan tooltip "Tidak ada data untuk diexport"

### US-15: Dashboard Ringkasan
- [ ] Dashboard adalah halaman pertama setelah login (`/`)
- [ ] Menampilkan ringkasan: "Hari Ini" (total pengeluaran hari ini), "Bulan Ini" (total bulan berjalan)
- [ ] Menampilkan 3 kategori pengeluaran terbesar bulan ini
- [ ] Menampilkan 5 transaksi terakhir (dengan link "Lihat Semua")
- [ ] Form input cepat (US-03) terintegrasi di dashboard
- [ ] Data di dashboard hanya milik user yang sedang login

### US-16: Ganti Password
- [ ] Tersedia di halaman Pengaturan
- [ ] Form meminta: password lama, password baru, konfirmasi password baru
- [ ] Validasi password lama benar sebelum memperbolehkan perubahan
- [ ] Password baru minimal 6 karakter
- [ ] Setelah berhasil, notifikasi sukses, user tetap login (session tidak terputus)

---

## 4. Prioritas & Roadmap Rilis

### 🚀 MVP — Rilis 1 (Minimal Viable Product)

Target: **Aplikasi dasar yang sudah bisa digunakan untuk mencatat pengeluaran harian.**

| User Story | Fitur | Prioritas |
|---|---|---|
| US-01 | Registrasi Akun | 🔴 Must Have |
| US-02 | Login & Logout | 🔴 Must Have |
| US-03 | Input Cepat Transaksi (Quick Add) | 🔴 Must Have |
| US-04 | Input Transaksi Lengkap | 🔴 Must Have |
| US-05 | Melihat Riwayat Transaksi | 🔴 Must Have |
| US-06 | Filter & Cari Riwayat | 🔴 Must Have |
| US-07 | Edit Transaksi | 🔴 Must Have |
| US-08 | Hapus Transaksi | 🔴 Must Have |
| US-09 | Ringkasan Pengeluaran Bulanan | 🔴 Must Have |
| US-13 | Lihat Kategori Default | 🔴 Must Have |
| US-15 | Dashboard Ringkasan | 🔴 Must Have |

**MVP mencakup:** Siklus penuh catat → lihat → edit → hapus, ringkasan dasar, dashboard, dan 10 kategori default.

### 🔜 Rilis 2 — Enhanced Features

Target: **Personalisasi kategori, statistik visual, dan export data.**

| User Story | Fitur | Prioritas |
|---|---|---|
| US-12 | Kelola Kategori Kustom | 🟡 Should Have |
| US-10 | Statistik per Kategori (Pie Chart) | 🟡 Should Have |
| US-11 | Tren Pengeluaran Harian/Mingguan (Bar Chart) | 🟡 Should Have |
| US-14 | Export Data ke CSV | 🟡 Should Have |
| US-16 | Ganti Password | 🟡 Should Have |

### 📋 Rilis 3 — Nice to Have (Backlog)

| Fitur Potensial | Keterangan |
|---|---|
| Login dengan Google / SSO | Mempermudah registrasi dan login |
| Budgeting & Alert | Set anggaran per kategori, notifikasi jika melebihi |
| Upload Foto Struk | Lampirkan bukti transaksi |
| Export PDF Report | Laporan ringkasan bulanan format PDF |
| Dark Mode | Tema gelap untuk kenyamanan malam hari |
| Multi-currency | Selain Rupiah, bisa pilih mata uang lain |
| Recurring Transactions | Transaksi berulang otomatis (misal: tagihan bulanan) |
| Family/Household Sharing | Satu akun bisa sharing data dengan anggota keluarga |
| PWA / Mobile App Wrapper | Bisa diinstal di homescreen HP, akses offline dasar |
| Notifikasi Pengingat | Push notification untuk ingatkan input pengeluaran harian |

---

## 5. Daftar Fitur/Kemampuan Aplikasi

### A. Modul Autentikasi & Akun
| ID | Fitur | Deskripsi Singkat |
|---|---|---|
| F-AUTH-01 | Registrasi | User membuat akun dengan email & password |
| F-AUTH-02 | Login | User masuk ke akun dengan email & password |
| F-AUTH-03 | Logout | User keluar dari sesi aktif |
| F-AUTH-04 | Ganti Password | User mengganti password akun (Rilis 2) |

### B. Modul Transaksi
| ID | Fitur | Deskripsi Singkat |
|---|---|---|
| F-TRX-01 | Input Cepat (Quick Add) | Form minimal: jumlah + kategori, tanggal default hari ini |
| F-TRX-02 | Input Lengkap | Form lengkap: jumlah, kategori, tanggal, catatan, metode pembayaran |
| F-TRX-03 | Riwayat Transaksi | Daftar seluruh transaksi, terurut terbaru, dengan pagination |
| F-TRX-04 | Edit Transaksi | Ubah semua field transaksi yang sudah ada |
| F-TRX-05 | Hapus Transaksi | Hapus transaksi dengan konfirmasi |
| F-TRX-06 | Filter & Pencarian | Filter by rentang tanggal, kategori, metode bayar; pencarian teks |

### C. Modul Kategori
| ID | Fitur | Deskripsi Singkat |
|---|---|---|
| F-CAT-01 | Kategori Default | 10 kategori siap pakai saat user pertama daftar |
| F-CAT-02 | Tambah Kategori | User membuat kategori kustom (Rilis 2) |
| F-CAT-03 | Edit Kategori | User mengubah nama/ikon/warna kategori kustom (Rilis 2) |
| F-CAT-04 | Hapus Kategori | User menghapus kategori kustom yang tidak digunakan (Rilis 2) |
| F-CAT-05 | Sembunyikan Kategori | User menyembunyikan kategori default yang tidak relevan (Rilis 2) |

### D. Modul Statistik & Dashboard
| ID | Fitur | Deskripsi Singkat |
|---|---|---|
| F-DASH-01 | Dashboard | Halaman utama: ringkasan hari ini, bulan ini, 5 transaksi terakhir |
| F-STAT-01 | Ringkasan Bulanan | Total pengeluaran per bulan dengan navigasi bulan/tahun |
| F-STAT-02 | Diagram Pie Kategori | Distribusi pengeluaran per kategori dalam pie chart (Rilis 2) |
| F-STAT-03 | Grafik Tren Harian | Bar chart pengeluaran 7 atau 30 hari terakhir (Rilis 2) |

### E. Modul Export
| ID | Fitur | Deskripsi Singkat |
|---|---|---|
| F-EXPORT-01 | Export CSV | Unduh data transaksi (sesuai filter aktif) dalam format CSV (Rilis 2) |

---

## 6. Batasan & Non-Functional Requirements

### 6.1 — Target Environment
- **Server:** VPS 2 Core CPU, RAM 4GB
- **Target user:** Individu / personal use
- **Minimal user:** 1 user (single-user), siap multi-user

### 6.2 — Ekspektasi Performa
- Halaman dashboard dan riwayat transaksi harus dimuat dalam < 2 detik untuk 1000 transaksi
- Operasi CRUD (simpan, edit, hapus) harus memberikan respon < 500ms
- Aplikasi harus tetap responsif dengan 10 concurrent user dan 200 transaksi/user/bulan

### 6.3 — Kompatibilitas
- **Browser modern:** Chrome, Firefox, Safari, Edge (2 versi terakhir)
- **Mobile:** Responsif, nyaman digunakan di layar HP (min. 320px lebar)
- **Offline:** Tidak ada kebutuhan offline untuk MVP

### 6.4 — Keamanan
- Password disimpan dalam bentuk hash (tidak plain text)
- Semua komunikasi via HTTPS
- Session management dengan expiry (auto-logout setelah periode inactivity — opsional)
- Data antar user terisolasi sepenuhnya (user A tidak bisa melihat data user B)

### 6.5 — Bahasa & Mata Uang
- **Bahasa UI:** Bahasa Indonesia
- **Mata Uang Default:** Rupiah (Rp), format: Rp 10.000
- **Zona Waktu Default:** WIB (Asia/Jakarta / UTC+7)

---

## Lampiran: Daftar Kategori Default

| No | Nama Kategori | Ikon/Emoji (Saran) |
|---|---|---|
| 1 | Makanan & Minuman | 🍔 |
| 2 | Transportasi | 🚗 |
| 3 | Belanja | 🛒 |
| 4 | Tagihan & Utilitas | 💡 |
| 5 | Hiburan | 🎮 |
| 6 | Kesehatan | 💊 |
| 7 | Pendidikan | 📚 |
| 8 | Pakaian | 👕 |
| 9 | Rumah Tangga | 🏠 |
| 10 | Lain-lain | 📦 |

---

*Dokumen ini disusun sebagai panduan kebutuhan bisnis/user. Diskusi teknis terkait arsitektur, database schema, dan technology stack akan ditangani oleh Architect Agent dalam dokumen terpisah.*
