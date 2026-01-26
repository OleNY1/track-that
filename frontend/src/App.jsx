import { useEffect, useState } from "react";
import {
  fetchApplications,
  searchApplications,
  createApplication,
  deleteApplication,
  updateApplication,
} from "./api";

const STATUS_OPTIONS = ["Applied", "Interview", "Offer", "Rejected", "Withdrawn"];

export default function App() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);

  // form state
  const [form, setForm] = useState({
    company: "",
    role: "",
    status: "Applied",
    date_applied: "", // "YYYY-MM-DD"
    application_link: "",
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce the search input (wait 350ms after typing stops)
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 350);
    return () => clearTimeout(t);
  }, [search]);

  async function loadApps() {
    setLoading(true);
    setError("");

    try {
      const data =
        debouncedSearch.length > 0
          ? await searchApplications(debouncedSearch)
          : await fetchApplications();

      setApps(data);
    } catch (e) {
      setError(e.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  // Load data on first render + whenever the debounced search changes
  useEffect(() => {
    loadApps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    const payload = {
      company: form.company.trim(),
      role: form.role.trim(),
      status: form.status.trim(),
      date_applied: form.date_applied || null,
      application_link: form.application_link.trim() || null,
    };

    try {
      await createApplication(payload);

      setForm({
        company: "",
        role: "",
        status: "Applied",
        date_applied: "",
        application_link: "",
      });

      await loadApps();
    } catch (e) {
      setError(e.message || "Failed to create application");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this application?")) return;

    setError("");
    try {
      await deleteApplication(id);
      await loadApps();
    } catch (e) {
      setError(e.message || "Failed to delete");
    }
  }

  async function handleStatusChange(id, newStatus) {
    setError("");
    try {
      await updateApplication(id, { status: newStatus });
      await loadApps();
    } catch (e) {
      setError(e.message || "Failed to update status");
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: "system-ui, Arial" }}>
      <h1 style={{ marginBottom: 16 }}>Track That</h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 8 }}>Add application</h2>

        <div style={{ display: "grid", gap: 8, maxWidth: 520 }}>
          <input
            name="company"
            placeholder="Company (required)"
            value={form.company}
            onChange={handleChange}
            required
          />
          <input
            name="role"
            placeholder="Role (required)"
            value={form.role}
            onChange={handleChange}
            required
          />
          <input
            name="status"
            placeholder="Status (e.g. Applied)"
            value={form.status}
            onChange={handleChange}
          />
          <input
            name="date_applied"
            type="date"
            value={form.date_applied}
            onChange={handleChange}
          />
          <input
            name="application_link"
            placeholder="Application link (optional)"
            value={form.application_link}
            onChange={handleChange}
          />

          <button type="submit" disabled={submitting}>
            {submitting ? "Adding..." : "Add"}
          </button>

          {error && <p style={{ color: "crimson" }}>{error}</p>}
        </div>
      </form>

      <div style={{ margin: "16px 0" }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search company or role..."
          style={{ width: 320, padding: 8 }}
        />
        {search && (
          <button type="button" onClick={() => setSearch("")} style={{ marginLeft: 8 }}>
            Clear
          </button>
        )}
      </div>

      {loading ? (
        <p>Loading…</p>
      ) : (
        <table cellPadding="8" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th align="left">Company</th>
              <th align="left">Role</th>
              <th align="left">Status</th>
              <th align="left">Date applied</th>
              <th align="left">Link</th>
              <th align="left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {apps.map((a) => (
              <tr key={a.id} style={{ borderTop: "1px solid #ddd" }}>
                <td>{a.company}</td>
                <td>{a.role}</td>
                <td>
                  <select
                    value={a.status || "Applied"}
                    onChange={(e) => handleStatusChange(a.id, e.target.value)}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td>{a.date_applied ?? ""}</td>
                <td>
                  {a.application_link ? (
                    <a href={a.application_link} target="_blank" rel="noreferrer">
                      open
                    </a>
                  ) : (
                    ""
                  )}
                </td>
                <td>
                  <button onClick={() => handleDelete(a.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
