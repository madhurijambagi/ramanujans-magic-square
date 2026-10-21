const express = require("express");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");
const { validateGrid } = require("../magicSquare");
const { evaluateAchievements } = require("../achievements");

const router = express.Router();

router.post("/", requireAuth, (req, res) => {
  const { game_id, grid } = req.body || {};
  if (typeof game_id !== "string" || !Array.isArray(grid)) return res.status(400).json({ error: "A game session and completed grid are required." });
  const game = db.prepare("SELECT * FROM game_sessions WHERE id=? AND user_id=?").get(game_id, req.session.userId);
  if (!game || game.completed_at) return res.status(400).json({ error: "This game session is not available." });
  const solved = JSON.parse(game.solved_grid);
  if (grid.length !== solved.length || !validateGrid(grid, game.square_order).solved || grid.some((value, i) => value !== solved[i])) {
    return res.status(400).json({ error: "The submitted grid is not the solved puzzle." });
  }
  const elapsed = Math.max(1, Math.floor((Date.now() - game.started_at) / 1000));
  if (game.is_daily && db.prepare("SELECT 1 FROM attempts WHERE user_id=? AND square_order=? AND is_daily=1 AND challenge_date=?").get(req.session.userId, game.square_order, game.challenge_date)) {
    return res.status(409).json({ error: "You already completed this daily challenge for this order today." });
  }

  const result = db
    .prepare(
      `INSERT INTO attempts (user_id, square_order, moves_made, time_taken, hints_used, is_daily, challenge_date)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
    .run(
      req.session.userId,
      game.square_order, game.moves_made, elapsed, game.hints_used, game.is_daily, game.challenge_date
    );
  db.prepare("UPDATE game_sessions SET completed_at=? WHERE id=?").run(Date.now(), game.id);
  if (game.is_daily) {
    const user = db.prepare("SELECT daily_streak,last_daily_date FROM users WHERE id=?").get(req.session.userId);
    const previous = user.last_daily_date;
    if (previous !== game.challenge_date) {
      const gap = previous ? Math.round((Date.parse(game.challenge_date + "T00:00:00Z") - Date.parse(previous + "T00:00:00Z")) / 86400000) : 1;
      const retained = gap > 1 ? Math.max(0, user.daily_streak - (gap - 1)) : user.daily_streak;
      db.prepare("UPDATE users SET daily_streak=?, last_daily_date=? WHERE id=?").run(retained + 1, game.challenge_date, req.session.userId);
    }
  }

  const newlyEarned = evaluateAchievements(req.session.userId);

  res.status(201).json({ id: result.lastInsertRowid, newly_earned: newlyEarned });
});

router.post("/progress", requireAuth, (req, res) => {
  const { game_id, action } = req.body || {};
  if (typeof game_id !== "string" || !["move", "hint"].includes(action)) return res.status(400).json({ error: "Invalid progress update." });
  const column = action === "move" ? "moves_made" : "hints_used";
  const result = db.prepare(`UPDATE game_sessions SET ${column}=${column}+1 WHERE id=? AND user_id=? AND completed_at IS NULL`).run(game_id, req.session.userId);
  if (!result.changes) return res.status(400).json({ error: "Game session is not active." });
  res.json({ ok: true });
});

router.get("/history", requireAuth, (req, res) => {
  const rows = db
    .prepare(
      `SELECT id, square_order, moves_made, time_taken, hints_used, is_daily, date_attempted
       FROM attempts WHERE user_id = ? ORDER BY date_attempted DESC`
    )
    .all(req.session.userId);
  res.json(rows);
});

router.get("/best", requireAuth, (req, res) => {
  const rows = db
    .prepare(
      `SELECT square_order, MIN(time_taken) AS best_time
       FROM attempts WHERE user_id = ? GROUP BY square_order`
    )
    .all(req.session.userId);

  const best = {};
  for (const r of rows) best[r.square_order] = r.best_time;
  res.json(best);
});

module.exports = router;
