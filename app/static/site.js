const state = {
  users: [],
  selectedUserId: "",
  currentQuery: "",
  profileMenuOpen: false,
};

const healthBadge = document.getElementById("health-badge");
const healthText = document.getElementById("health-text");
const searchForm = document.getElementById("search-form");
const searchQueryInput = document.getElementById("search-query");
const searchResults = document.getElementById("search-results");
const searchFeedback = document.getElementById("search-feedback");
const ingestButton = document.getElementById("ingest-button");
const chatForm = document.getElementById("chat-form");
const chatMessageInput = document.getElementById("chat-message");
const chatLog = document.getElementById("chat-log");
const profileButton = document.getElementById("profile-button");
const profileMenu = document.getElementById("profile-menu");
const profileUserList = document.getElementById("profile-user-list");
const profileAvatar = document.getElementById("profile-avatar");
const profileName = document.getElementById("profile-name");
const profileLocation = document.getElementById("profile-location");

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  return response.json();
}

function initialsFor(name) {
  return name
    .split(" ")
    .map((part) => part[0] || "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function selectedUser() {
  return state.users.find((user) => user.id === state.selectedUserId) || null;
}

function setHealth(ok, message) {
  healthBadge.textContent = ok ? "Backend ready" : "Backend issue";
  healthBadge.className = `badge ${ok ? "badge-ok" : "badge-error"}`;
  healthText.textContent = message;
}

function createPill(text) {
  const pill = document.createElement("span");
  pill.className = "pill";
  pill.textContent = text;
  return pill;
}

function syncUserUI() {
  const user = selectedUser();
  if (!user) {
    return;
  }

  const initials = initialsFor(user.name);
  profileAvatar.textContent = initials;
  profileName.textContent = user.name;
  profileLocation.textContent = user.location;
}

function setProfileMenu(open) {
  state.profileMenuOpen = open;
  profileMenu.classList.toggle("hidden", !open);
  profileButton.setAttribute("aria-expanded", String(open));
}

function renderUserList() {
  profileUserList.innerHTML = "";

  state.users.forEach((user) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `user-card${user.id === state.selectedUserId ? " active" : ""}`;
    button.innerHTML = `
      <span class="user-avatar">${initialsFor(user.name)}</span>
      <span class="user-meta">
        <strong>${user.name}</strong>
        <span>${user.location} | ${user.preferences.slice(0, 2).join(", ")}</span>
      </span>
    `;
    button.addEventListener("click", () => {
      state.selectedUserId = user.id;
      syncUserUI();
      renderUserList();
      setProfileMenu(false);
      addChatEntry("Assistant", `Switched to ${user.name}. I can tailor suggestions to ${user.location} and their preferences.`);
    });
    profileUserList.appendChild(button);
  });
}

function renderProductCard(item) {
  const template = document.getElementById("product-card-template");
  const fragment = template.content.cloneNode(true);
  const card = fragment.querySelector(".product-card");
  const product = item.product;

  fragment.querySelector(".category").textContent = product.category;
  fragment.querySelector(".product-name").textContent = product.name;
  fragment.querySelector(".price").textContent = `Rs. ${product.price}`;
  fragment.querySelector(".description").textContent = product.description;
  fragment.querySelector(".score").textContent = item.similarity_score !== null
    ? `Similarity score: ${item.similarity_score}`
    : "";

  const tags = fragment.querySelector(".tags");
  product.tags.forEach((tag) => tags.appendChild(createPill(tag)));

  const attributes = fragment.querySelector(".attributes");
  Object.entries(product.attributes).forEach(([key, value]) => {
    attributes.appendChild(createPill(`${key}: ${value}`));
  });

  const explanationNode = fragment.querySelector(".explanation");
  const explainButton = fragment.querySelector(".explain-button");
  explainButton.addEventListener("click", async () => {
    explanationNode.classList.remove("hidden");
    explanationNode.textContent = "Generating explanation...";

    try {
      const data = await request("/explain", {
        method: "POST",
        body: JSON.stringify({
          product_id: product.id,
          query: state.currentQuery || searchQueryInput.value || "shopping recommendation",
        }),
      });
      explanationNode.textContent = data.explanation;
    } catch (error) {
      explanationNode.textContent = `Could not generate explanation: ${error.message}`;
    }
  });

  return card;
}

function addChatEntry(role, text, recommendations = []) {
  const template = document.getElementById("chat-entry-template");
  const fragment = template.content.cloneNode(true);

  fragment.querySelector(".chat-role").textContent = role;
  fragment.querySelector(".chat-text").textContent = text;

  const recommendationWrap = fragment.querySelector(".chat-recommendations");
  recommendations.forEach((product) => {
    const box = document.createElement("div");
    box.className = "mini-product";
    box.innerHTML = `<strong>${product.name}</strong><span>${product.category} | Rs. ${product.price}</span>`;
    recommendationWrap.appendChild(box);
  });

  chatLog.appendChild(fragment);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function loadHealth() {
  try {
    const data = await request("/health");
    setHealth(data.status === "ok", "FastAPI backend is reachable.");
  } catch (error) {
    setHealth(false, error.message);
  }
}

async function loadUsers() {
  try {
    const data = await request("/users");
    state.users = data.users;
    state.selectedUserId = data.users[0]?.id || "";
    syncUserUI();
    renderUserList();
  } catch (error) {
    profileName.textContent = "Unavailable";
    profileLocation.textContent = "Could not load users";
  }
}

profileButton.addEventListener("click", () => {
  setProfileMenu(!state.profileMenuOpen);
});

document.addEventListener("click", (event) => {
  if (!profileMenu.contains(event.target) && !profileButton.contains(event.target)) {
    setProfileMenu(false);
  }
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  searchResults.innerHTML = "";
  searchFeedback.textContent = "Searching products...";
  state.currentQuery = searchQueryInput.value.trim();

  try {
    const data = await request("/search", {
      method: "POST",
      body: JSON.stringify({ query: state.currentQuery }),
    });

    searchFeedback.textContent = `Showing ${data.results.length} result(s) for "${data.query}".`;
    if (!data.results.length) {
      searchFeedback.textContent = "No products matched that search yet.";
      return;
    }

    data.results.forEach((item) => {
      searchResults.appendChild(renderProductCard(item));
    });
  } catch (error) {
    searchFeedback.textContent = `Search failed: ${error.message}`;
  }
});

ingestButton.addEventListener("click", async () => {
  ingestButton.disabled = true;
  ingestButton.textContent = "Re-ingesting...";
  try {
    const data = await request("/ingest-products", { method: "POST", body: "{}" });
    searchFeedback.textContent = `Indexed ${data.ingested_count} products into ${data.collection_name}.`;
  } catch (error) {
    searchFeedback.textContent = `Ingestion failed: ${error.message}`;
  } finally {
    ingestButton.disabled = false;
    ingestButton.textContent = "Re-ingest products";
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatMessageInput.value.trim();
  if (!message) {
    return;
  }

  addChatEntry("You", message);
  chatMessageInput.value = "";

  try {
    const data = await request("/chat", {
      method: "POST",
      body: JSON.stringify({
        user_id: state.selectedUserId || "U001",
        message,
      }),
    });
    addChatEntry("Assistant", data.response, data.recommendations || []);
  } catch (error) {
    addChatEntry("Assistant", `Chat failed: ${error.message}`);
  }
});

addChatEntry(
  "Assistant",
  "Welcome back. Tell me what you're shopping for and I’ll pull recommendations with context."
);

Promise.all([loadHealth(), loadUsers()]);
