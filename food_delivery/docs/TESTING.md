# Test Qo'llanmasi

## Ishga tushirish

```bash
# Barcha testlar
pytest tests/ -v

# Coverage bilan
pytest tests/ -v --cov=app --cov-report=html

# Bitta fayl
pytest tests/test_auth.py -v

# Bitta test
pytest tests/test_cart.py::test_add_item -v
```

## Test yozish qoidalari

1. Har test bitta narsani tekshiradi
2. Test nomi `test_[nima_qiladi]_[qanday_holat]` formatida
3. Arrange → Act → Assert tartibida
4. Mock faqat tashqi servislar uchun (bot, SMS)

## Fixtures (conftest.py)

```python
@pytest.fixture
async def db_session():
    # test DB session

@pytest.fixture
async def redis_client():
    # fakeredis

@pytest.fixture
async def test_user(db_session):
    # yaratilgan user

@pytest.fixture
def auth_headers(test_user):
    # JWT token bilan headers

@pytest.fixture
async def test_products(db_session):
    # 5 ta test mahsulot
```

## Muhim test cases

### Auth
- Valid initData → user yaratiladi, JWT qaytariladi
- Invalid initData → 401
- Expired token → 401
- Admin user → is_admin=True

### Cart
- Mahsulot qo'shish → Redis da saqlanadi
- Miqdor 0 ga teng → item o'chadi
- Mavjud item qo'shish → quantity ortadi

### Checkout
- To'liq flow → order yaratiladi, cart tozalanadi
- Noto'g'ri narx yuborilsa → DB narxi ishlatiladi
- Bo'sh savat → 400
- Duplicate idempotency key → 409
- Min order amount past → 400
