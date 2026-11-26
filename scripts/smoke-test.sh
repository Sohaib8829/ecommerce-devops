#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8080}"

pass() { echo "✅ $1"; }
fail() { echo "❌ FAIL: $1"; exit 1; }

# Website ke uthne ka intezar (zyada se zyada 60 second)
for i in $(seq 1 30); do
  if curl -fsS "$BASE/" > /dev/null 2>&1; then break; fi
  sleep 2
done

# 1. Frontend page
curl -fsS "$BASE/" | grep -q "ShopStack" || fail "frontend page loaded"
pass "frontend page theek hai"

# 2. Products ki list (kam az kam 6)
count=$(curl -fsS "$BASE/api/products" | grep -o '"id"' | wc -l)
[ "$count" -ge 6 ] || fail "products are short: $count"
pass "products list: $count products"

# 3. Orders service ready hai (Redis + database)
curl -fsS "$BASE/api/orders/ready" | grep -q "ready" || fail "orders service not ready"
pass "orders service ready"

# 4. Cart ka poora safar
USER="ci$RANDOM"
curl -fsS -X POST "$BASE/api/orders/cart/$USER/items" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":2}' > /dev/null || fail "cart didn't work"
curl -fsS "$BASE/api/orders/cart/$USER" | grep -q '"quantity":2' || fail "cart quantity wrong"
pass "cart working"

# 5. Na-maujood product par 404
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/orders/cart/$USER/items" \
  -H "Content-Type: application/json" -d '{"product_id":9999}')
[ "$code" = "404" ] || fail "9999 required 404 found: $code"
pass "404 on wrong product"

# 6. reserve bahar se band hai
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/products/1/reserve" \
  -H "Content-Type: application/json" -d '{"quantity":1}')
[ "$code" = "403" ] || fail "needed 403 on reserver, found: $code"
pass "reserver not available from outside"

echo "All smoke tests are passed"