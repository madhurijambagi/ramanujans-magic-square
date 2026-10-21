const db = require("../db");

function requireAuth(req, res, next) {
  if (!req.session || !req.session.userId) {
    return res.status(401).json({ error: "Not authenticated. Please log in." });
  }
  next();
}

function requireAdmin(req, res, next) {
  if (!req.session || !req.session.userId) {
    return res.status(401).json({ error: "Not authenticated. Please log in." });
  }
  const user = db
    .prepare("SELECT is_admin FROM users WHERE id = ?")
    .get(req.session.userId);
  if (!user || !user.is_admin) {
    return res.status(403).json({ error: "Administrator privilege required." });
  }
  next();
}

module.exports = { requireAuth, requireAdmin };
