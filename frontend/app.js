var ICONS = { "Clothing": "👕", "Electronics": "🎧", "Accessories": "👜" };
var products = [];
var activeCategory = "All";
var cartCount = 0;

var grid = document.getElementById("grid");
var filters = document.getElementById("filters");
var statusBox = document.getElementById("status");
var cartBadge = document.getElementById("cart-count");

function formatPrice(n) {
  return "Rs " + n.toLocaleString("en-PK");
}

function makeEl(tag, className, text) {
  var e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
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
        cartCount += 1;
        cartBadge.textContent = cartCount;
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
  } catch (err) {
    statusBox.textContent = "Products load nahi ho sake. Backend check karo.";
  }
}

loadProducts();
