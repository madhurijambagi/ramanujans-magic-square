const db = require("./db");
const { ALLOWED_ORDERS } = require("./magicSquare");

/**
 * Achievement catalog. Each entry's `check(userId)` runs against the
 * attempts table and returns true if the user has newly qualified.
 * Keep checks cheap — they run once per saved attempt.
 */
const ACHIEVEMENTS = [
  {
    key: "first_solve",
    name: "First Square",
    description: "Solve your first magic square.",
    check: (userId) => {
      const { count } = db
        .prepare("SELECT COUNT(*) AS count FROM attempts WHERE user_id = ?")
        .get(userId);
      return count >= 1;
    },
  },
  {
    key: "all_orders",
    name: "Full Spectrum",
    description: `Solve at least one square of every order: ${ALLOWED_ORDERS.join(", ")}.`,
    check: (userId) => {
      const rows = db
        .prepare(
          "SELECT DISTINCT square_order FROM attempts WHERE user_id = ?"
        )
        .all(userId)
        .map((r) => r.square_order);
      return ALLOWED_ORDERS.every((o) => rows.includes(o));
    },
  },
  {
    key: "ten_solves",
    name: "Ten and Counting",
    description: "Log ten total solve attempts.",
    check: (userId) => {
      const { count } = db
        .prepare("SELECT COUNT(*) AS count FROM attempts WHERE user_id = ?")
        .get(userId);
      return count >= 10;
    },
  },
  {
    key: "speed_demon",
    name: "Speed Demon",
    description: "Solve 3x3 under 20s, 5x5 under 1m, 7x7 under 10m, or 9x9 under 5m.",
    check: (userId) => {
      const row = db
        .prepare(
          `SELECT 1 FROM attempts WHERE user_id = ? AND ((square_order=3 AND time_taken < 20) OR (square_order=5 AND time_taken < 60) OR (square_order=7 AND time_taken < 600) OR (square_order=9 AND time_taken < 300)) LIMIT 1`
        )
        .get(userId);
      return !!row;
    },
  },
  {
    key: "no_hints_needed",
    name: "No Hints Needed",
    description: "Solve a 7x7 or larger square without using a single hint.",
    check: (userId) => {
      const { count } = db
        .prepare(
          `SELECT COUNT(*) AS count FROM attempts
           WHERE user_id = ? AND square_order >= 7 AND hints_used = 0`
        )
        .get(userId);
      return count >= 1;
    },
  },
  {
    key: "daily_solver",
    name: "Daily Devotee",
    description: "Complete a Daily Challenge square.",
    check: (userId) => {
      const { count } = db
        .prepare(
          "SELECT COUNT(*) AS count FROM attempts WHERE user_id = ? AND is_daily = 1"
        )
        .get(userId);
      return count >= 1;
    },
  },
];

/**
 * Evaluates every achievement for a user and records any newly-earned ones.
 * Returns the list of achievement keys newly unlocked by this call.
 */
function evaluateAchievements(userId) {
  const already = new Set(
    db
      .prepare("SELECT achievement_key FROM user_achievements WHERE user_id = ?")
      .all(userId)
      .map((r) => r.achievement_key)
  );

  const newlyEarned = [];
  const insert = db.prepare(
    "INSERT INTO user_achievements (user_id, achievement_key) VALUES (?, ?)"
  );

  for (const a of ACHIEVEMENTS) {
    if (already.has(a.key)) continue;
    if (a.check(userId)) {
      insert.run(userId, a.key);
      newlyEarned.push(a.key);
    }
  }
  return newlyEarned;
}

function listForUser(userId) {
  const earned = new Map(
    db
      .prepare(
        "SELECT achievement_key, earned_at FROM user_achievements WHERE user_id = ?"
      )
      .all(userId)
      .map((r) => [r.achievement_key, r.earned_at])
  );
  return ACHIEVEMENTS.map((a) => ({
    key: a.key,
    name: a.name,
    description: a.description,
    earned: earned.has(a.key),
    earned_at: earned.get(a.key) || null,
  }));
}

module.exports = { ACHIEVEMENTS, evaluateAchievements, listForUser };
