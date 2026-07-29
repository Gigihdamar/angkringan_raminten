// ============================================================
// Angkringan Raminten - main.js
// Menangani: toggle sidebar admin (mobile), serta helper umum.
// Logika auto-refresh spesifik halaman (status pelanggan &
// dashboard/orders admin) ada langsung di masing-masing template
// agar mudah dibaca sesuai konteks halamannya.
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".admin-sidebar");
  const sidebarBackdrop = document.getElementById("sidebarBackdrop");
  function setSidebar(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("open", open);
    if (sidebarBackdrop) sidebarBackdrop.classList.toggle("show", open);
  }
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => setSidebar(!sidebar.classList.contains("open")));
  }
  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", () => setSidebar(false));
  }

  // ---- Navbar: solid once page is scrolled (or always, on non-hero pages) ----
  const navbar = document.getElementById("mainNavbar");
  if (navbar) {
    const hasHero = document.body.classList.contains("has-hero");
    if (!hasHero) {
      // Halaman tanpa hero selalu tampil solid (sesuai CSS), jadi class
      // "solid" harus selalu aktif juga -- tanpa ini, ikon kanan navbar
      // ikut style transparan (putih) dan jadi tidak terlihat di atas
      // background navbar yang sebenarnya sudah solid/terang.
      navbar.classList.add("solid");
    } else {
      const onScroll = () => navbar.classList.toggle("solid", window.scrollY > 40);
      onScroll();
      window.addEventListener("scroll", onScroll, { passive: true });
    }
  }

  // ---- Search box generik: dipakai untuk pencarian pelanggan (menu +
  // halaman/info) maupun admin (pesanan + menu + halaman panel) ----
  function initGlobalSearch(opts) {
    const toggle = document.getElementById(opts.toggleId);
    const box = document.getElementById(opts.boxId);
    const wrap = document.getElementById(opts.wrapId);
    const input = document.getElementById(opts.inputId);
    const dropdown = document.getElementById(opts.dropdownId);
    if (!input || !dropdown) return;

    function closeSearch() {
      if (box) box.classList.remove("open");
      dropdown.classList.remove("show");
    }

    if (toggle && box) {
      toggle.addEventListener("click", () => {
        const willOpen = !box.classList.contains("open");
        box.classList.toggle("open", willOpen);
        if (willOpen) { input.focus(); } else { dropdown.classList.remove("show"); }
      });
    }

    let searchDebounce = null;
    let activeSearchToken = 0;
    let lastResults = {};

    function itemRow(item, thumbHtml) {
      return `<a class="search-result-item" href="${item.url}">
          ${thumbHtml}
          <span>
            <span class="sri-title d-block">${item.title}</span>
            <span class="sri-sub">${item.desc}</span>
          </span>
        </a>`;
    }

    function renderResults(data, query) {
      const groups = opts.groups; // [{key, label}, ...] in display order
      const hasAny = groups.some((g) => (data[g.key] || []).length);
      if (!hasAny) {
        dropdown.innerHTML = `<div class="search-empty-state">Tidak ada hasil untuk &ldquo;${query}&rdquo;.</div>`;
        return;
      }
      let html = "";
      groups.forEach((g) => {
        const items = data[g.key] || [];
        if (!items.length) return;
        html += `<div class="search-group-label">${g.label}</div>`;
        items.forEach((item) => {
          const thumb = item.image && item.image !== "default-menu.jpg"
            ? `<img class="sri-thumb" src="/static/images/${item.image}" alt="${item.title}">`
            : `<span class="sri-icon"><i class="bi ${item.icon || 'bi-egg-fried'}"></i></span>`;
          html += itemRow(item, thumb);
        });
      });
      dropdown.innerHTML = html;
    }

    async function runSearch(query) {
      const token = ++activeSearchToken;
      dropdown.classList.add("show");
      dropdown.innerHTML = `<div class="search-loading-state">Mencari...</div>`;
      try {
        const res = await fetch(opts.apiUrl + "?q=" + encodeURIComponent(query));
        const data = await res.json();
        if (token !== activeSearchToken) return; // hasil basi
        lastResults = data;
        renderResults(data, query);
      } catch (err) {
        if (token !== activeSearchToken) return;
        dropdown.innerHTML = `<div class="search-empty-state">Gagal memuat hasil pencarian.</div>`;
      }
    }

    input.addEventListener("input", () => {
      const q = input.value.trim();
      clearTimeout(searchDebounce);
      if (!q) {
        dropdown.classList.remove("show");
        dropdown.innerHTML = "";
        lastResults = {};
        return;
      }
      searchDebounce = setTimeout(() => runSearch(q), 250);
    });

    input.addEventListener("focus", () => {
      if (input.value.trim() && dropdown.innerHTML) dropdown.classList.add("show");
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const q = input.value.trim();
        if (!q) return;
        let topResult = null;
        for (const g of opts.groups) {
          if (lastResults[g.key] && lastResults[g.key].length) { topResult = lastResults[g.key][0]; break; }
        }
        if (topResult) window.location.href = topResult.url;
        else if (opts.fallbackUrl) window.location.href = opts.fallbackUrl + encodeURIComponent(q);
      } else if (e.key === "Escape") {
        closeSearch();
      }
    });

    document.addEventListener("click", (e) => {
      const container = wrap || box;
      if (container && !container.contains(e.target) && e.target !== toggle) {
        dropdown.classList.remove("show");
      }
    });
  }

  initGlobalSearch({
    toggleId: "searchToggle", boxId: "searchBox", wrapId: "searchWrap",
    inputId: "menuSearchInput", dropdownId: "searchResultsDropdown",
    apiUrl: "/api/search", fallbackUrl: "/menu?q=",
    groups: [{ key: "menu", label: "Menu" }, { key: "pages", label: "Halaman & Info" }],
  });

  // Kotak cari versi mobile (di dalam drawer, selalu terbuka, tanpa tombol toggle)
  initGlobalSearch({
    toggleId: null, boxId: null, wrapId: "mobileSearchWrap",
    inputId: "menuSearchInputMobile", dropdownId: "searchResultsDropdownMobile",
    apiUrl: "/api/search", fallbackUrl: "/menu?q=",
    groups: [{ key: "menu", label: "Menu" }, { key: "pages", label: "Halaman & Info" }],
  });

  initGlobalSearch({
    toggleId: "adminSearchToggle", boxId: "adminSearchBox", wrapId: "adminSearchWrap",
    inputId: "adminSearchInput", dropdownId: "adminSearchDropdown",
    apiUrl: "/admin/api/search", fallbackUrl: null,
    groups: [
      { key: "orders", label: "Pesanan" },
      { key: "menu", label: "Menu" },
      { key: "pages", label: "Halaman Panel" },
    ],
  });

  // ---- Cart drawer ----
  const cartToggle = document.getElementById("cartToggle");
  const cartFab = document.getElementById("cartFab");
  const cartDrawer = document.getElementById("cartDrawer");
  const cartBackdrop = document.getElementById("cartBackdrop");
  const cartClose = document.getElementById("cartClose");
  function openDrawer() {
    cartDrawer.classList.add("open");
    cartBackdrop.classList.add("open");
    document.body.style.overflow = "hidden";
  }
  function closeDrawer() {
    cartDrawer.classList.remove("open");
    cartBackdrop.classList.remove("open");
    document.body.style.overflow = "";
  }
  if (cartDrawer) {
    if (cartToggle) cartToggle.addEventListener("click", openDrawer);
    if (cartFab) cartFab.addEventListener("click", openDrawer);
    cartClose.addEventListener("click", closeDrawer);
    cartBackdrop.addEventListener("click", closeDrawer);
  }

  // ---- Quantity steppers (cart page & cart drawer) — delegated so it still
  // works after the cart drawer content is refreshed via AJAX ----
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".qty-minus, .qty-plus");
    if (!btn) return;
    const stepper = btn.closest(".qty-stepper");
    const input = stepper && stepper.querySelector(".qty-input");
    if (!input) return;
    if (btn.classList.contains("qty-minus")) {
      input.value = Math.max(0, parseInt(input.value || "0", 10) - 1);
    } else {
      input.value = parseInt(input.value || "0", 10) + 1;
    }
    stepper.submit();
  });

  // ---- Button ripple effect ----
  document.querySelectorAll(".btn-pesan, .btn-staff-login, .btn-ripple").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      const rect = this.getBoundingClientRect();
      const ripple = document.createElement("span");
      ripple.className = "btn-ripple-fx";
      ripple.style.left = (e.clientX - rect.left) + "px";
      ripple.style.top = (e.clientY - rect.top) + "px";
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  // ---- Fade-in-up on scroll into view ----
  const revealEls = document.querySelectorAll(".reveal-on-scroll");
  if (revealEls.length && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("fade-in-up");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    revealEls.forEach((el) => io.observe(el));
  }

  // ---- Tambah ke Keranjang lewat AJAX (tanpa reload / scroll ke atas) ----
  document.addEventListener("submit", async (e) => {
    const form = e.target.closest(".cart-add-form");
    if (!form) return;
    e.preventDefault();

    const btn = form.querySelector("button[type=submit]");
    const originalHtml = btn ? btn.innerHTML : null;
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Menambahkan...';
    }

    try {
      const res = await fetch(form.action, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: new FormData(form),
      });
      const data = await res.json();

      if (data.success) {
        showToast(data.message, "success");
        document.querySelectorAll("#cartBadge, #cartBadgeMobile").forEach((badge) => {
          badge.textContent = data.cart_count;
          badge.classList.toggle("d-none", data.cart_count <= 0);
        });
        refreshCartDrawer();
      } else {
        showToast(data.message || "Gagal menambahkan ke keranjang.", "danger");
      }
    } catch (err) {
      showToast("Gagal menambahkan ke keranjang. Coba lagi.", "danger");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }
    }
  });
});

// ---- Refresh isi cart drawer tanpa reload halaman ----
async function refreshCartDrawer() {
  const inner = document.getElementById("cartDrawerInner");
  if (!inner) return;
  try {
    const res = await fetch("/cart/fragment", { headers: { "X-Requested-With": "XMLHttpRequest" } });
    if (!res.ok) return;
    inner.innerHTML = await res.text();
  } catch (err) {
    console.error("Gagal menyegarkan keranjang:", err);
  }
}

// ---- Toast notifikasi ringan (dipakai saat tambah ke keranjang) ----
function showToast(message, type) {
  let container = document.getElementById("toastStack");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastStack";
    container.className = "toast-stack";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = "app-toast app-toast--" + (type || "success");
  toast.innerHTML = `<i class="bi ${type === 'danger' ? 'bi-exclamation-circle' : 'bi-check-circle'}"></i> <span>${message}</span>`;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 250);
  }, 2600);
}

function formatRupiah(number) {
  return "Rp" + Number(number).toLocaleString("id-ID");
}
