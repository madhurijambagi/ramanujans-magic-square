const express = require("express");
const { requireAuth } = require("../middleware/auth");
const { listForUser } = require("../achievements");

const router = express.Router();

router.get("/mine", requireAuth, (req, res) => {
  res.json(listForUser(req.session.userId));
});

module.exports = router;
