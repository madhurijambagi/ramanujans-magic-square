const express = require("express");
const db = require("../db");
const { requireAdmin } = require("../middleware/auth");

const router = express.Router();

router.use(requireAdmin);

router.get("/users", (req, res) => {
  const rows = db
    .prepare(
      `SELECT u.id, u.username, u.is_admin, u.created_at,
              COUNT(a.id) AS attempt_count
       FROM users u
       LEFT JOIN attempts a ON a.user_id = u.id
       GROUP BY u.id
       ORDER BY u.created_at ASC`
    )
    .all();
  res.json(rows.map((r) => ({ ...r, is_admin: !!r.is_admin })));
});

router.get("/attempts", (req, res) => {
  const rows = db
    .prepare(
      `SELECT a.id, a.square_order, a.moves_made, a.time_taken, a.date_attempted,
              u.username, u.id AS user_id
       FROM attempts a
       JOIN users u ON u.id = a.user_id
       ORDER BY a.date_attempted DESC
       LIMIT 200`
    )
    .all();
  res.json(rows);
});

// Account deletion is deliberately self-service only; administrators cannot delete members.

// Administrators can grant/revoke admin privilege for other users, so a
// team can add more administrators without relying on server env vars or
// direct database access. An admin can't demote themselves if they're the
// only admin left (that would lock everyone out of the admin panel).
router.patch("/users/:id/role", (req, res) => {
  const id = parseInt(req.params.id, 10);
  const { is_admin } = req.body || {};
  if (typeof is_admin !== "boolean") {
    return res.status(400).json({ error: "is_admin (boolean) is required." });
  }
  const target = db.prepare("SELECT id, is_admin FROM users WHERE id=?").get(id);
  if (!target) return res.status(404).json({ error: "User not found." });

  if (!is_admin && target.is_admin) {
    const { count } = db.prepare("SELECT COUNT(*) AS count FROM users WHERE is_admin=1").get();
    if (count <= 1) {
      return res.status(400).json({ error: "Can't remove the last remaining administrator." });
    }
  }

  db.prepare("UPDATE users SET is_admin=? WHERE id=?").run(is_admin ? 1 : 0, id);
  res.json({ ok: true, id, is_admin });
});

router.delete("/attempts/:id", (req, res) => {
  const id = parseInt(req.params.id, 10);
  const result = db.prepare("DELETE FROM attempts WHERE id = ?").run(id);
  if (result.changes === 0) {
    return res.status(404).json({ error: "Attempt not found." });
  }
  res.json({ ok: true });
});

module.exports = router;
