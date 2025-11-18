# 📊 PyO3 Overhead & Marshalling Benchmarks

## **1. PyO3 Overhead Benchmarks (małe dane, minimalna logika)**

| Benchmark | Python (ops/s) | Rust (ops/s) | Wniosek |
|----------|----------------|--------------|---------|
| **empty()** | 11,83M | 14,40M | Rust ~20% szybszy – minimalny narzut PyO3 |
| **small_args(5×int)** | 8,28M | 7,38M | Python nieco szybszy – koszt konwersji liczb → Rust |
| **small_ret()** | 8,78M | 9,75M | Rust szybciej zwraca małe wartości |
| **make_empty_class()** | 8,70M | 12,58M | Tworzenie obiektu `#[pyclass]` dużo tańsze niż klasy Python |
| **read_one_field(obj)** | 6,55M | 6,36M | Prawie identyczne czasy – dostęp do pola jest porównywalny |
| **pass_obj(obj)** | 8,88M | 9,75M | Rust nieco szybszy – przekazywanie PyAny jest tanie |
| **read_list(list)** | 7,81M | 0,18M | ⚠️ Rust wolny, bo konwersja listy → Vec w każdej iteracji |

### 🎯 Interpretacja – Overhead

- **Granica Python ↔ Rust jest bardzo tania**, gdy dane są małe.  
  Overhead PyO3 wynosi zwykle **10–30%**.
- **Tworzenie obiektów po stronie Rusta jest zauważalnie tańsze** niż po stronie Pythona.
- Operacje na małych typach skalarnych (int, return int) są **bardzo szybkie po obu stronach**.
- Jedyny wyraźny outlier:  
  **read_list_rust** – bo wymusza konwersję `list → Vec`, czyli tak naprawdę jest to benchmark marshallingu, nie overheadu.

---

## **2. Marshalling Benchmarks (duże argumenty / duży wynik)**

| Benchmark | Python (ops/s) | Rust (ops/s) | Wniosek |
|----------|----------------|--------------|---------|
| **marshall_large_args(list,str,bytes)** | 7,34M | 830 | Python szybki (brak kopiowania), Rust ekstremalnie wolny (pełna konwersja danych) |
| **marshall_large_return(len)** | 1314 | 1240 | Podobne czasy – koszt generacji dużych danych dominuje, a marshalling Rust→Python jest relatywnie tani |

### 🎯 Interpretacja – Marshalling

- **Przekazywanie dużych struktur Python → Rust jest bardzo kosztowne**, jeśli Rust oczekuje:  
  - `Vec<i64>`  
  - `Vec<u8>`  
  - `String`  
  
  Każde wywołanie powoduje **pełną kopię** danych → dlatego Rust osiąga tylko ~830 ops/s.

- Po stronie Pythona:  
  - duże argumenty są przekazywane przez **referencję**,  
  - brak kopiowania → dlatego Python osiąga ~7M ops/s.

- **Duże zwroty Rust → Python są względnie tanie**, bo PyO3 może:  
  - zbudować Python listę/string/bytes bez wielokrotnej interpretacji,  
  - i oba środowiska wykonują podobną pracę (alokacja + wypełnienie).

---

## **3. Najważniejsze wnioski dla projektu**

### ✔ Overhead PyO3 jest niski
Dla małych danych Rust ↔ Python działa z wysoką przepustowością (~8–14M ops/s).  
Można wykonywać wiele małych wywołań – overhead jest pomijalny.

### ✔ Rust wymiata w tworzeniu obiektów
`#[pyclass]` jest dużo tańsze niż Python-native objects.  
To jest świetna wiadomość dla drivera – opłaca się tworzyć obiekty po stronie Rust.

### ✔ Odczyty pól i przekazywanie obiektów są tanie
Operacje na PyAny są szybkie – dobre dla serialization/deserialization logic.

### ⚠️ Największe zagrożenie: konwersja dużych kolekcji Python → Rust
`list -> Vec` to **najbardziej kosztowna rzecz w PyO3**, nawet kilka tysięcy razy wolniejsza od małego callu.

### ✔ Zwracanie dużych danych z Rusta jest OK
Rust→Python marshalling jest dużo tańszy niż Python→Rust.

---

## 📌 TL;DR

- **PyO3 overhead jest bardzo niski** — Rust i Python działają podobnie szybko.  
- **Rust opłaca się dla obiektów i małych operacji.**  
- **Unikaj konwersji dużych list z Pythona do Rust**, jeśli nie jest absolutnie konieczne.  
- **Duże dane najlepiej generować po stronie Rust** i tylko zwracać do Pythona.

