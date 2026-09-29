const form = document.querySelector("#analyze-form");
const input = document.querySelector("#repo-input");
const button = document.querySelector("#analyze-button");
const results = document.querySelector("#results");
const loading = document.querySelector("#loading");
const report = document.querySelector("#report");
const errorBox = document.querySelector("#error-message");
const number = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const dateFormat = new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" });

document.querySelector("#year").textContent = new Date().getFullYear();
document.querySelectorAll(".example").forEach((example) => {
  example.addEventListener("click", () => {
    input.value = example.dataset.repo;
    form.requestSubmit();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  results.hidden = false;
  loading.hidden = false;
  report.hidden = true;
  button.disabled = true;
  try {
    const response = await fetch(`/api/analyze?repo=${encodeURIComponent(input.value)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not analyze that repository.");
    render(data);
    loading.hidden = true;
    report.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    results.hidden = true;
    errorBox.textContent = error.message || "Something went wrong. Please try again.";
    errorBox.hidden = false;
  } finally {
    loading.hidden = true;
    button.disabled = false;
  }
});

function dateOnly(value) {
  if (!value) return "Unknown";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? "Unknown" : dateFormat.format(parsed);
}

function safeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}

function render(data) {
  const repo = data.repository;
  document.querySelector("#repo-name").textContent = repo.name;
  document.querySelector("#repo-description").textContent = repo.description;
  const repoLink = document.querySelector("#repo-link");
  repoLink.href = repo.url;
  const avatar = document.querySelector("#owner-avatar");
  avatar.src = repo.owner_avatar;
  avatar.hidden = !repo.owner_avatar;
  document.querySelector("#stars").textContent = number.format(repo.stars);
  document.querySelector("#forks").textContent = number.format(repo.forks);
  document.querySelector("#issues").textContent = number.format(repo.open_issues);
  document.querySelector("#last-push").textContent = dateOnly(repo.pushed_at);

  document.querySelector("#topics").innerHTML = (repo.topics || []).slice(0, 8).map((topic) => `<span class="topic">${safeText(topic)}</span>`).join("");
  const languages = document.querySelector("#language-bars");
  languages.innerHTML = data.languages.map((language) => `<div class="language-row"><span class="language-name">${safeText(language.name)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(language.percent, 1)}%"></div></div><span class="language-percent">${language.percent}%</span></div>`).join("");
  document.querySelector("#language-empty").hidden = data.languages.length > 0;

  const status = repo.archived ? '<span class="status-pill archived">Archived</span>' : '<span class="status-pill">Active</span>';
  const details = [
    ["Status", status, true], ["Default branch", safeText(repo.default_branch)], ["License", safeText(repo.license)],
    ["Created", dateOnly(repo.created_at)], ["Updated", dateOnly(repo.updated_at)], ["Watchers", number.format(repo.watchers)],
  ];
  document.querySelector("#details").innerHTML = details.map(([label, value, html]) => `<div class="detail-row"><span class="detail-label">${label}</span><span class="detail-value">${html ? value : safeText(value)}</span></div>`).join("");

  document.querySelector("#contributors").innerHTML = data.contributors.map((person) => `<div class="contributor"><img src="${safeText(person.avatar_url)}" alt="" loading="lazy"><div class="contributor-info"><a class="contributor-name" href="${safeText(person.html_url)}" target="_blank" rel="noreferrer">${safeText(person.login)}</a><div class="contributor-count">${number.format(person.contributions)} contributions</div></div></div>`).join("");
  document.querySelector("#contributors-empty").hidden = data.contributors.length > 0;
  document.querySelector("#contributor-count").textContent = `TOP ${data.contributors.length}`;

  document.querySelector("#commits").innerHTML = data.commits.slice(0, 5).map((commit) => `<div class="commit"><span class="commit-dot"></span><div class="commit-copy"><a class="commit-message" href="${safeText(commit.url)}" target="_blank" rel="noreferrer" title="${safeText(commit.message)}">${safeText(commit.message)}</a><div class="commit-meta">${safeText(commit.author)} · ${dateOnly(commit.date)}</div></div><a class="commit-sha" href="${safeText(commit.url)}" target="_blank" rel="noreferrer">${safeText(commit.sha)}</a></div>`).join("");
  document.querySelector("#commits-empty").hidden = data.commits.length > 0;
  document.querySelector("#commit-sample").textContent = `${data.commit_sample_size} FETCHED`;

  document.querySelector("#files").innerHTML = data.files.map((file) => `<a class="file-item" href="${safeText(file.url)}" target="_blank" rel="noreferrer"><span class="file-icon">${file.type === "dir" ? "▰" : "▤"}</span><span class="file-name">${safeText(file.name)}</span>${file.type === "file" ? `<span class="file-size">${formatBytes(file.size)}</span>` : ""}</a>`).join("");
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}
