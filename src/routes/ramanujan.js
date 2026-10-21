const express = require("express");
const { generateRamanujanSquare } = require("../magicSquare");

const router = express.Router();

// GET /api/ramanujan/:a/:b/:c/:d -> a 4x4 date-style magic square built
// from four whole numbers, using the generalized version of the
// construction Ramanujan famously demonstrated with his own birthdate.
router.get("/:a/:b/:c/:d", (req, res) => {
  const [a, b, c, d] = [req.params.a, req.params.b, req.params.c, req.params.d].map((v) => parseInt(v, 10));
  if ([a, b, c, d].some((v) => !Number.isFinite(v))) {
    return res.status(400).json({ error: "Four whole numbers are required." });
  }
  try {
    const result = generateRamanujanSquare(a, b, c, d);
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

module.exports = router;
