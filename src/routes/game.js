const express = require("express");
const crypto = require("crypto");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");
const {
  isAllowedOrder,
  orderInfo,
  generateMagicSquare,
  scrambleSquare,
  magicConstant,
  validateGrid,
  todayDateString,
  DISPLAY_ORDERS,
} = require("../magicSquare");

const router = express.Router();

function orderError(order) {
  const info = orderInfo(order);
  if (info.possible) return null;
  return info.reason || `Order must be one of: ${DISPLAY_ORDERS.join(", ")}`;
}

// GET /api/game/new/:order  -> a freshly generated + scrambled puzzle
router.get("/new/:order", requireAuth, (req, res) => {
  const order = parseInt(req.params.order, 10);
  const err = orderError(order);
  if (err) return res.status(400).json({ error: err, possible: false });

  const { flat: solved, path } = generateMagicSquare(order, { withPath: true });
  const scrambled = scrambleSquare(solved);

  res.json({
    order,
    target: magicConstant(order),
    solved,
    path,
    scrambled,
  });
});

router.post("/start", requireAuth, (req, res) => {
  const { order, is_daily } = req.body || {};
  const err = orderError(order);
  if (err) return res.status(400).json({ error: err, possible: false });
  const daily = !!is_daily;
  const date = daily ? todayDateString() : null;
  if (
    daily &&
    db
      .prepare(
        "SELECT 1 FROM attempts WHERE user_id=? AND square_order=? AND is_daily=1 AND challenge_date=?"
      )
      .get(req.session.userId, order, date)
  ) {
    return res.status(409).json({ error: "You already completed this daily challenge for this order today." });
  }
  const flat = generateMagicSquare(order);
  const id = crypto.randomUUID();
  db.prepare(
    "INSERT INTO game_sessions (id,user_id,square_order,solved_grid,is_daily,challenge_date,started_at) VALUES (?,?,?,?,?,?,?)"
  ).run(id, req.session.userId, order, JSON.stringify(flat), daily ? 1 : 0, date, Date.now());
  res.status(201).json({ game_id: id });
});

// POST /api/game/validate  -> live validation of a candidate grid
router.post("/validate", (req, res) => {
  const { grid, order } = req.body || {};
  if (!Array.isArray(grid) || !isAllowedOrder(order) || grid.length !== order * order) {
    return res.status(400).json({ error: "Invalid grid or order supplied." });
  }
  const result = validateGrid(grid, order);
  res.json(result);
});

module.exports = router;
