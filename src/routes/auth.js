const express = require("express");
const crypto = require("crypto");
const bcrypt = require("bcryptjs");
const db = require("../db");
const { sendMail } = require("../mailer");

const router = express.Router();

const USERNAME_RE = /^[a-zA-Z0-9_]{3,20}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LEN = 8;
const RESET_TOKEN_TTL_MS = 1000 * 60 * 30; // 30 minutes
const VERIFY_TOKEN_TTL_MS = 1000 * 60 * 60 * 24; // 24 hours

function makeToken() {
  return crypto.randomBytes(32).toString("hex");
}

router.post("/register", async (req, res) => {
  const { username, password, email } = req.body || {};

  if (typeof username !== "string" || !USERNAME_RE.test(username)) {
    return res.status(400).json({
      error:
        "Username must be 3-20 characters and contain only letters, numbers, and underscores.",
    });
  }
  if (typeof password !== "string" || password.length < MIN_PASSWORD_LEN) {
    return res.status(400).json({
      error: `Password must be at least ${MIN_PASSWORD_LEN} characters long.`,
    });
  }
  let cleanEmail = null;
  if (email !== undefined && email !== null && String(email).trim() !== "") {
    cleanEmail = String(email).trim().toLowerCase();
    if (!EMAIL_RE.test(cleanEmail)) {
      return res.status(400).json({ error: "That doesn't look like a valid email address." });
    }
    const emailTaken = db.prepare("SELECT id FROM users WHERE email = ?").get(cleanEmail);
    if (emailTaken) {
      return res.status(409).json({ error: "That email is already associated with an account." });
    }
  }

  const existing = db
    .prepare("SELECT id FROM users WHERE username = ?")
    .get(username);
  if (existing) {
    return res.status(409).json({ error: "That username is already taken." });
  }

  // Production administration is explicitly configured, rather than granted
  // to whichever visitor happens to register first.
  const isBootstrapAdmin = !!process.env.ADMIN_USERNAME && username === process.env.ADMIN_USERNAME;

  const passwordHash = await bcrypt.hash(password, 10);

  let verifyToken = null;
  let verifyExpires = null;
  if (cleanEmail) {
    verifyToken = makeToken();
    verifyExpires = Date.now() + VERIFY_TOKEN_TTL_MS;
  }

  const result = db
    .prepare(
      `INSERT INTO users (username, password_hash, is_admin, email, verify_token, verify_token_expires)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
    .run(username, passwordHash, isBootstrapAdmin ? 1 : 0, cleanEmail, verifyToken, verifyExpires);

  req.session.userId = result.lastInsertRowid;

  if (cleanEmail) {
    const verifyUrl = `${req.protocol}://${req.get("host")}/api/auth/verify-email?token=${verifyToken}`;
    sendMail({
      to: cleanEmail,
      subject: "Verify your Ramanujan's Magic Square email",
      text: `Welcome to Ramanujan's Magic Square! Verify your email by visiting:\n${verifyUrl}\n\nThis link expires in 24 hours. If you didn't create this account, you can ignore this message.`,
    }).catch((err) => console.error("[mailer] verification email failed:", err.message));
  }

  return res.status(201).json({
    id: result.lastInsertRowid,
    username,
    is_admin: isBootstrapAdmin,
    email: cleanEmail,
    email_verified: false,
  });
});

router.post("/login", async (req, res) => {
  const { username, password } = req.body || {};

  if (typeof username !== "string" || typeof password !== "string") {
    return res.status(400).json({ error: "Username and password are required." });
  }

  const user = db
    .prepare("SELECT * FROM users WHERE username = ?")
    .get(username);

  if (!user) {
    return res.status(401).json({ error: "Invalid username or password." });
  }

  const valid = await bcrypt.compare(password, user.password_hash);
  if (!valid) {
    return res.status(401).json({ error: "Invalid username or password." });
  }

  req.session.userId = user.id;

  return res.json({
    id: user.id,
    username: user.username,
    is_admin: !!user.is_admin,
  });
});

router.post("/logout", (req, res) => {
  req.session.destroy(() => {
    res.clearCookie("connect.sid");
    res.json({ ok: true });
  });
});

router.post("/change-password", async (req, res) => {
  if (!req.session.userId) return res.status(401).json({ error: "Not authenticated." });
  const { current_password, new_password } = req.body || {};
  if (typeof new_password !== "string" || new_password.length < MIN_PASSWORD_LEN) return res.status(400).json({ error: `New password must be at least ${MIN_PASSWORD_LEN} characters long.` });
  const user = db.prepare("SELECT password_hash FROM users WHERE id=?").get(req.session.userId);
  if (!user || !(await bcrypt.compare(current_password || "", user.password_hash))) return res.status(401).json({ error: "Current password is incorrect." });
  db.prepare("UPDATE users SET password_hash=? WHERE id=?").run(await bcrypt.hash(new_password, 10), req.session.userId);
  res.json({ ok: true });
});

// --- Forgot / reset password (works for logged-out users) ---------------

router.post("/forgot-password", async (req, res) => {
  const { email } = req.body || {};
  // Always respond the same way whether or not the email exists, so this
  // endpoint can't be used to enumerate registered addresses.
  const generic = { ok: true, message: "If that email is associated with an account, a reset link has been sent." };
  if (typeof email !== "string" || !EMAIL_RE.test(email.trim())) {
    return res.json(generic);
  }
  const user = db.prepare("SELECT id, email FROM users WHERE email = ?").get(email.trim().toLowerCase());
  if (!user) return res.json(generic);

  const token = makeToken();
  const expires = Date.now() + RESET_TOKEN_TTL_MS;
  db.prepare("UPDATE users SET reset_token=?, reset_token_expires=? WHERE id=?").run(token, expires, user.id);

  const resetUrl = `${req.protocol}://${req.get("host")}/reset-password.html?token=${token}`;
  sendMail({
    to: user.email,
    subject: "Reset your Ramanujan's Magic Square password",
    text: `We received a request to reset your Ramanujan's Magic Square password. Visit this link within 30 minutes to choose a new one:\n${resetUrl}\n\nIf you didn't request this, you can safely ignore this email — your password will stay the same.`,
  }).catch((err) => console.error("[mailer] reset email failed:", err.message));

  res.json(generic);
});

router.post("/reset-password", async (req, res) => {
  const { token, new_password } = req.body || {};
  if (typeof token !== "string" || !token) {
    return res.status(400).json({ error: "Missing reset token." });
  }
  if (typeof new_password !== "string" || new_password.length < MIN_PASSWORD_LEN) {
    return res.status(400).json({ error: `New password must be at least ${MIN_PASSWORD_LEN} characters long.` });
  }
  const user = db.prepare("SELECT id, reset_token_expires FROM users WHERE reset_token = ?").get(token);
  if (!user || !user.reset_token_expires || user.reset_token_expires < Date.now()) {
    return res.status(400).json({ error: "This reset link is invalid or has expired. Request a new one." });
  }
  const passwordHash = await bcrypt.hash(new_password, 10);
  db.prepare("UPDATE users SET password_hash=?, reset_token=NULL, reset_token_expires=NULL WHERE id=?").run(passwordHash, user.id);
  res.json({ ok: true });
});

// --- Email verification ---------------------------------------------------

router.get("/verify-email", (req, res) => {
  const { token } = req.query || {};
  if (typeof token !== "string" || !token) {
    return res.status(400).send("Missing verification token.");
  }
  const user = db.prepare("SELECT id, verify_token_expires FROM users WHERE verify_token = ?").get(token);
  if (!user || !user.verify_token_expires || user.verify_token_expires < Date.now()) {
    return res.status(400).send("This verification link is invalid or has expired. Request a new one from your profile page.");
  }
  db.prepare("UPDATE users SET email_verified=1, verify_token=NULL, verify_token_expires=NULL WHERE id=?").run(user.id);
  res.redirect("/profile.html?verified=1");
});

router.post("/resend-verification", async (req, res) => {
  if (!req.session.userId) return res.status(401).json({ error: "Not authenticated." });
  const user = db.prepare("SELECT id, email, email_verified FROM users WHERE id=?").get(req.session.userId);
  if (!user || !user.email) return res.status(400).json({ error: "Add an email address to your profile first." });
  if (user.email_verified) return res.json({ ok: true, already_verified: true });

  const token = makeToken();
  const expires = Date.now() + VERIFY_TOKEN_TTL_MS;
  db.prepare("UPDATE users SET verify_token=?, verify_token_expires=? WHERE id=?").run(token, expires, user.id);
  const verifyUrl = `${req.protocol}://${req.get("host")}/api/auth/verify-email?token=${token}`;
  sendMail({
    to: user.email,
    subject: "Verify your Ramanujan's Magic Square email",
    text: `Verify your email by visiting:\n${verifyUrl}\n\nThis link expires in 24 hours.`,
  }).catch((err) => console.error("[mailer] verification email failed:", err.message));
  res.json({ ok: true });
});

// --- Add/change email while logged in --------------------------------------

router.post("/email", async (req, res) => {
  if (!req.session.userId) return res.status(401).json({ error: "Not authenticated." });
  const { email } = req.body || {};
  if (typeof email !== "string" || !EMAIL_RE.test(email.trim())) {
    return res.status(400).json({ error: "That doesn't look like a valid email address." });
  }
  const cleanEmail = email.trim().toLowerCase();
  const taken = db.prepare("SELECT id FROM users WHERE email = ? AND id != ?").get(cleanEmail, req.session.userId);
  if (taken) return res.status(409).json({ error: "That email is already associated with an account." });

  const token = makeToken();
  const expires = Date.now() + VERIFY_TOKEN_TTL_MS;
  db.prepare("UPDATE users SET email=?, email_verified=0, verify_token=?, verify_token_expires=? WHERE id=?").run(cleanEmail, token, expires, req.session.userId);
  const verifyUrl = `${req.protocol}://${req.get("host")}/api/auth/verify-email?token=${token}`;
  sendMail({
    to: cleanEmail,
    subject: "Verify your Ramanujan's Magic Square email",
    text: `Verify your email by visiting:\n${verifyUrl}\n\nThis link expires in 24 hours.`,
  }).catch((err) => console.error("[mailer] verification email failed:", err.message));
  res.json({ ok: true, email: cleanEmail });
});

// --- Account data / deletion ----------------------------------------------

router.get("/export", (req, res) => {
  if (!req.session.userId) return res.status(401).json({ error: "Not authenticated." });
  const user = db.prepare("SELECT id,username,email,email_verified,created_at FROM users WHERE id=?").get(req.session.userId);
  const attempts = db.prepare("SELECT square_order,moves_made,time_taken,hints_used,is_daily,challenge_date,date_attempted FROM attempts WHERE user_id=? ORDER BY date_attempted").all(req.session.userId);
  res.json({ user, attempts });
});

router.delete("/account", async (req, res) => {
  if (!req.session.userId) return res.status(401).json({ error: "Not authenticated." });
  const { password } = req.body || {};
  const user = db.prepare("SELECT password_hash FROM users WHERE id=?").get(req.session.userId);
  if (!user || !(await bcrypt.compare(password || "", user.password_hash))) return res.status(401).json({ error: "Password is incorrect." });
  db.prepare("DELETE FROM users WHERE id=?").run(req.session.userId);
  req.session.destroy(() => res.json({ ok: true }));
});

router.get("/me", (req, res) => {
  if (!req.session || !req.session.userId) {
    return res.status(401).json({ error: "Not authenticated." });
  }
  const user = db
    .prepare("SELECT id, username, is_admin, created_at, daily_streak, last_daily_date, email, email_verified FROM users WHERE id = ?")
    .get(req.session.userId);
  if (!user) {
    return res.status(401).json({ error: "Not authenticated." });
  }
  res.json({ ...user, is_admin: !!user.is_admin, email_verified: !!user.email_verified });
});

module.exports = router;
