const api = {
  async request(method, url, body) {
    const res = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
      credentials: "same-origin",
    });
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      /* no body */
    }
    if (!res.ok) {
      throw new Error((data && data.error) || `Request failed (${res.status})`);
    }
    return data;
  },
  get(url) { return this.request("GET", url); },
  post(url, body) { return this.request("POST", url, body); },
  del(url) { return this.request("DELETE", url); },
  delete(url, body) { return this.request("DELETE", url, body); },
};

async function requireSession(redirectIfMissing = true) {
  try {
    return await api.get("/api/auth/me");
  } catch (e) {
    if (redirectIfMissing) window.location.href = "/";
    return null;
  }
}

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatDate(iso) {
  const d = new Date(iso.replace(" ", "T") + "Z");
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function initNav(activePath) {
  const links = document.querySelectorAll(".nav-links a[data-path]");
  links.forEach((a) => {
    if (a.getAttribute("data-path") === activePath) a.classList.add("active");
  });
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await api.post("/api/auth/logout");
      window.location.href = "/";
    });
  }
}
