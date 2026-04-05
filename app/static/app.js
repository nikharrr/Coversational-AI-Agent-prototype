const state = {
  users: [],
  selectedUserId: "",
  currentQuery: "",
};

const healthBadge = document.getElementById("health-badge");
const healthText = document.getElementById("health-text");
const userSelect = document.getElementById("user-select");
const searchForm = document.getElementById("search-form");
const searchQueryInput = document.getElementById("search-query");
const searchResults = document.getElementById("search-results");
const searchFeedback = document.getElementById("search-feedback");
const ingestButton = document.getElementById("ingest-button");
const chatForm = document.getElementById("chat-form");
const chatMessageInput = document.getElementById("chat-message");
const chatLog = document.getElementById("chat-log");

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
    box.innerHTML = `<strong>${product.name}</strong><span>${product.category} • Rs. ${product.price}</span>`;
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
    userSelect.innerHTML = "";
    data.users.forEach((user, index) => {
      const option = document.createElement("option");
      option.value = user.id;
      option.textContent = `${user.name} (${user.location})`;
      if (index === 0) {
        state.selectedUserId = user.id;
      }
      userSelect.appendChild(option);
    });
    userSelect.value = state.selectedUserId;
  } catch (error) {
    userSelect.innerHTML = "<option>Unable to load users</option>";
  }
}

userSelect.addEventListener("change", (event) => {
  state.selectedUserId = event.target.value;
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
  "Ask for an outfit, a snack, a gadget, or a follow-up like why a recommendation fits."
);

Promise.all([loadHealth(), loadUsers()]);
