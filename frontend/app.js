var ICONS = { "Clothing": "👕", "Electronics": "🎧", "Accessories": "👜" };
var products = [];
var activeCategory = "All";

var grid = document.getElementById("grid");
var filters = document.getElementById("filters");
var statusBox = document.getElementById("status");
var cartBadge = document.getElementById("cart-count");

var USER_ID = localStorage.getItem("shopstack_user");
if (!USER_ID) {
  USER_ID = "u" + Math.random().toString(36).slice(2, 10);
  localStorage.setItem("shopstack_user", USER_ID);
}

function formatPrice(n) {
  return "Rs " + n.toLocaleString("en-PK");
}

function makeEl(tag, className, text) {
  var e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
}

var messageTimer = null;
function showMessage(text) {
  statusBox.textContent = text;
  clearTimeout(messageTimer);
  messageTimer = setTimeout(function () {
    statusBox.textContent = "";
  }, 3000);
}

function cartTotal(cart) {
  return cart.items.reduce(function (sum, i) {
    return sum + i.quantity;
  }, 0);
}

async function refreshCart() {
  try {
    var res = await fetch("/api/orders/cart/" + USER_ID);
    if (res.ok) {
      cartBadge.textContent = cartTotal(await res.json());
    }
  } catch (err) {
    /* cart ka count na mile to UI chalti rahe */
  }
}

async function addToCart(productId) {
  try {
    var res = await fetch("/api/orders/cart/" + USER_ID + "/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, quantity: 1 })
    });
    var data = await res.json();
    if (!res.ok) {
      showMessage(data.detail || "Cart mein nahi dala ja saka");
      return;
    }
    cartBadge.textContent = cartTotal(data);
    showMessage("Cart mein add ho gaya ✅");
  } catch (err) {
    showMessage("Server tak pahunch nahi saka");
  }
}

function renderFilters() {
  filters.innerHTML = "";
  var cats = ["All"];
  products.forEach(function (p) {
    if (cats.indexOf(p.category) === -1) cats.push(p.category);
  });
  cats.forEach(function (c) {
    var chip = makeEl("button", "chip" + (c === activeCategory ? " active" : ""), c);
    chip.onclick = function () {
      activeCategory = c;
      renderFilters();
      renderGrid();
    };
    filters.appendChild(chip);
  });
}

function renderGrid() {
  grid.innerHTML = "";
  products
    .filter(function (p) {
      return activeCategory === "All" || p.category === activeCategory;
    })
    .forEach(function (p) {
      var card = makeEl("div", "card");
      card.appendChild(makeEl("div", "icon", ICONS[p.category] || "📦"));
      card.appendChild(makeEl("div", "cat", p.category));
      card.appendChild(makeEl("div", "name", p.name));
      card.appendChild(makeEl("div", "price", formatPrice(p.price)));
      var low = p.stock < 20;
      card.appendChild(
        makeEl("div", "stock" + (low ? " low" : ""),
          low ? "Sirf " + p.stock + " bache hain" : "In stock")
      );
      var btn = makeEl("button", "", "Add to cart");
      btn.onclick = function () {
        addToCart(p.id);
      };
      card.appendChild(btn);
      grid.appendChild(card);
    });
}

async function loadProducts() {
  try {
    var res = await fetch("/api/products");
    if (!res.ok) throw new Error("HTTP " + res.status);
    products = await res.json();
    statusBox.textContent = "";
    renderFilters();
    renderGrid();
    refreshCart();
  } catch (err) {
    statusBox.textContent = "Products load nahi ho sake. Backend check karo.";
  }
}

loadProducts();
