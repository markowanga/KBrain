# KBrain Storage Module

Asynchroniczny system storage dla backendu KBrain z obsługą pamięci RAM i dysków lokalnych.

## Funkcjonalności

- **Abstrakcyjny interfejs**: `BaseStorage` - spójny API dla różnych implementacji
- **In-Memory Storage**: `MemoryStorage` - szybki, volatile storage w RAM
- **File-Based Storage**: `FileStorage` - trwały storage na dysku (JSON)
- **Asynchroniczne metody**: Wszystkie operacje są async/await
- **Thread-safe**: Używa async locks do bezpieczeństwa wątków

## Implementacje

### MemoryStorage
```python
from storage import MemoryStorage

storage = MemoryStorage()
await storage.set("key", "value")
value = await storage.get("key")
```

**Zalety:**
- Bardzo szybki
- Brak I/O
- Idealny do testów

**Wady:**
- Volatile - dane ginną po restarcie
- Ograniczone przez RAM

### FileStorage
```python
from storage import FileStorage

storage = FileStorage(storage_dir="data")
await storage.set("key", "value")
value = await storage.get("key")
```

**Zalety:**
- Persistent - dane przetrwają restart
- Backup/restore możliwe
- Cache w pamięci dla wydajności

**Wady:**
- Wolniejszy niż MemoryStorage
- Wymaga miejsca na dysku
- Tylko JSON-serializable dane

## API Metody

Wszystkie implementacje storage wspierają następujące metody:

### Podstawowe operacje
- `async get(key: str) -> Optional[Any]` - Pobierz wartość
- `async set(key: str, value: Any) -> bool` - Zapisz wartość
- `async delete(key: str) -> bool` - Usuń wartość
- `async exists(key: str) -> bool` - Sprawdź czy klucz istnieje

### Batch operacje
- `async get_all() -> Dict[str, Any]` - Pobierz wszystkie pary klucz-wartość
- `async set_many(items: Dict[str, Any]) -> bool` - Zapisz wiele wartości
- `async delete_many(keys: List[str]) -> int` - Usuń wiele kluczy

### Utility
- `async list_keys(prefix: Optional[str]) -> List[str]` - Lista kluczy (z filtrem)
- `async count() -> int` - Liczba elementów
- `async clear() -> bool` - Wyczyść wszystko

### FileStorage specyficzne
- `async backup(backup_path: Optional[str]) -> bool` - Backup danych
- `async restore(backup_path: str) -> bool` - Przywróć z backupu

## Konfiguracja

Storage można skonfigurować przez zmienne środowiskowe:

```bash
# Wybór typu storage
export STORAGE_TYPE=file  # lub "memory"

# Katalog dla FileStorage
export STORAGE_DIR=data
```

## Przykład użycia w aplikacji

```python
import os
from storage import BaseStorage, MemoryStorage, FileStorage

# Inicjalizacja storage
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file")
storage: BaseStorage

if STORAGE_TYPE == "memory":
    storage = MemoryStorage()
else:
    storage = FileStorage(storage_dir="data")

# Użycie
await storage.set("user:123", {"name": "Jan", "age": 30})
user = await storage.get("user:123")

# Batch operacje
await storage.set_many({
    "user:124": {"name": "Anna", "age": 25},
    "user:125": {"name": "Piotr", "age": 35}
})

# Listowanie z prefixem
user_keys = await storage.list_keys(prefix="user:")
print(f"Found {len(user_keys)} users")
```

## API Endpoints

Backend udostępnia następujące REST API endpoints:

- `GET /api/storage/stats` - Statystyki storage
- `GET /api/storage/item/{key}` - Pobierz element
- `POST /api/storage/item` - Zapisz element
- `DELETE /api/storage/item/{key}` - Usuń element
- `GET /api/storage/exists/{key}` - Sprawdź istnienie
- `GET /api/storage/keys?prefix=xyz` - Lista kluczy
- `GET /api/storage/all` - Wszystkie elementy
- `POST /api/storage/many` - Zapisz wiele
- `DELETE /api/storage/many` - Usuń wiele
- `DELETE /api/storage/clear` - Wyczyść wszystko

## Testowanie

```bash
# Uruchom backend
cd kbrain_backend
python main.py

# W innym terminalu - testuj API
curl http://localhost:8000/api/storage/stats

# Zapisz element
curl -X POST http://localhost:8000/api/storage/item \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "hello"}'

# Pobierz element
curl http://localhost:8000/api/storage/item/test
```

## Architektura

```
storage/
├── __init__.py          # Eksporty modułu
├── base.py              # BaseStorage - abstrakcyjny interfejs
├── memory.py            # MemoryStorage - implementacja RAM
├── file.py              # FileStorage - implementacja dysk
└── README.md            # Ta dokumentacja
```

## Thread Safety

Wszystkie implementacje używają `asyncio.Lock()` dla zapewnienia thread-safety:

```python
async with self._lock:
    # Bezpieczne operacje
    self._storage[key] = value
```

## Wydajność

### MemoryStorage
- Operacje: ~O(1)
- Latency: <1ms
- Throughput: bardzo wysoki

### FileStorage
- Operacje: O(1) z cache, O(n) na reload
- Latency: 1-10ms (zależnie od rozmiaru)
- Throughput: średni (I/O bound)

## Rozszerzalność

Łatwo dodać nowe backendy implementując `BaseStorage`:

```python
from storage.base import BaseStorage

class RedisStorage(BaseStorage):
    async def get(self, key: str):
        # implementacja
        pass

    # ... pozostałe metody
```
