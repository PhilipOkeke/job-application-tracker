const form = document.querySelector("#application-form");
const list = document.querySelector("#application-list");
const message = document.querySelector("#form-message");
const search = document.querySelector("#search");
const statusFilter = document.querySelector("#status-filter");

const statusLabels = { saved: "Saved", applied: "Applied", interview: "Interview", offer: "Offer", rejected: "Rejected" };

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
}

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error((await response.json()).detail || "Request failed");
  return response.status === 204 ? null : response.json();
}

async function loadAnalytics() {
  const data = await request("/api/analytics");
  document.querySelector("#metric-total").textContent = data.total;
  document.querySelector("#metric-active").textContent = data.active;
  document.querySelector("#metric-rate").textContent = `${data.response_rate}%`;
}

async function loadApplications() {
  const params = new URLSearchParams();
  if (search.value.trim()) params.set("search", search.value.trim());
  if (statusFilter.value) params.set("status", statusFilter.value);
  const items = await request(`/api/applications?${params}`);
  list.innerHTML = items.length ? items.map((item) => `
    <article class="application-card">
      <div>
        <span class="status status-${item.status}">${statusLabels[item.status]}</span>
        <h3>${escapeHtml(item.role)}</h3>
        <p class="company">${escapeHtml(item.company)}${item.location ? ` · ${escapeHtml(item.location)}` : ""}</p>
        ${item.next_action ? `<p class="next-action"><strong>Next:</strong> ${escapeHtml(item.next_action)}</p>` : ""}
      </div>
      <button class="delete" data-delete="${item.id}" aria-label="Delete ${escapeHtml(item.role)} at ${escapeHtml(item.company)}">Delete</button>
    </article>`).join("") : '<div class="empty"><h3>No applications yet</h3><p>Add your first opportunity or change the filters.</p></div>';
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";
  const values = Object.fromEntries(new FormData(form));
  if (!values.applied_on) values.applied_on = null;
  try {
    await request("/api/applications", { method: "POST", body: JSON.stringify(values) });
    form.reset(); message.textContent = "Application saved.";
    await Promise.all([loadApplications(), loadAnalytics()]);
  } catch (error) { message.textContent = error.message; }
});

list.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-delete]");
  if (!button) return;
  await request(`/api/applications/${button.dataset.delete}`, { method: "DELETE" });
  await Promise.all([loadApplications(), loadAnalytics()]);
});

let searchTimer;
search.addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadApplications, 250); });
statusFilter.addEventListener("change", loadApplications);
Promise.all([loadApplications(), loadAnalytics()]).catch((error) => { list.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`; });
