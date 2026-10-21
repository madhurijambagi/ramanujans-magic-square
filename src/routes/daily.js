const express = require("express");
const db = require("../db");
const { requireAuth } = require("../middleware/auth");
const {
  orderInfo,
  generateMagicSquare,
  seededScramble,
  magicConstant,
  todayDateString,
  DISPLAY_ORDERS,
} = require("../magicSquare");

const router = express.Router();

// GET /api/daily/:order -> today's fixed puzzle for that order.
// Same for every user, so it's a fair race against the same scramble.
// Requires auth so we can report whether *this* user already solved it today.
router.get("/:order", requireAuth, (req, res) => {
  const order = parseInt(req.params.order, 10);
  const info = orderInfo(order);
  if (!info.possible) {
    return res.status(400).json({
      error: info.reason || `Order must be one of: ${DISPLAY_ORDERS.join(", ")}`,
      possible: false,
    });
  }

  const date = todayDateString();

  const already = db
    .prepare(
      "SELECT time_taken, moves_made, hints_used FROM attempts WHERE user_id=? AND square_order=? AND is_daily=1 AND challenge_date=?"
    )
    .get(req.session.userId, order, date);

  const { flat: solved, path } = generateMagicSquare(order, { withPath: true });
  const scrambled = seededScramble(solved, `${date}:${order}`);

  res.json({
    date,
    order,
    target: magicConstant(order),
    solved,
    path,
    scrambled,
    already_attempted: !!already,
    result: already || null,
  });
});

module.exports = router;
