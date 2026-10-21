const express = require("express");
const db = require("../db");
const { isAllowedOrder, todayDateString } = require("../magicSquare"); // isAllowedOrder now covers orders 3-10

const router = express.Router();

// GET /api/leaderboard/daily/:order -> today's fastest solves of the Daily Challenge
router.get("/daily/:order", (req, res) => {
  const order = parseInt(req.params.order, 10);
  if (!isAllowedOrder(order)) {
    return res.status(400).json({ error: "Invalid square order." });
  }

  const rows = db
    .prepare(
      `SELECT u.username, a.time_taken, a.moves_made, a.hints_used, a.date_attempted
       FROM attempts a
       JOIN users u ON u.id = a.user_id
       WHERE a.square_order = ? AND a.is_daily = 1 AND a.challenge_date = ?
       ORDER BY a.time_taken ASC, a.moves_made ASC
       LIMIT 20`
    )
    .all(order, todayDateString());

  res.json(rows);
});

router.get("/:order", (req, res) => {
  const order = parseInt(req.params.order, 10);
  if (!isAllowedOrder(order)) {
    return res.status(400).json({ error: "Invalid square order." });
  }

  const rows = db
    .prepare(
      `SELECT u.username, a.time_taken, a.moves_made, a.date_attempted
       FROM attempts a
       JOIN users u ON u.id = a.user_id
       WHERE a.square_order = ?
       ORDER BY a.time_taken ASC, a.moves_made ASC
       LIMIT 20`
    )
    .all(order);

  res.json(rows);
});

module.exports = router;
