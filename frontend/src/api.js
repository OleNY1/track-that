const API_BASE = "http://127.0.0.1:8000";

export async function fetchApplications() {
  const res = await fetch(`${API_BASE}/applications`);
  if (!res.ok) throw new Error("Failed to fetch applications");
  return res.json();
}

export async function searchApplications(q) {
  const res = await fetch(
    `${API_BASE}/applications/search?q=${encodeURIComponent(q)}`
  );
  if (!res.ok) throw new Error("Failed to search applications");
  return res.json();
}

export async function createApplication(payload) {
  const res = await fetch(`${API_BASE}/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to create application: ${res.status} ${text}`);
  }

  return res.json();
}

export async function updateApplication(id, patch) {
  const res = await fetch(`${API_BASE}/applications/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to update application: ${res.status} ${text}`);
  }

  return res.json();
}

export async function deleteApplication(id) {
  const res = await fetch(`${API_BASE}/applications/${id}`, { method: "DELETE" });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to delete application: ${res.status} ${text}`);
  }

  // DELETE returns 204 No Content, so don't call res.json()
  return true;
}
