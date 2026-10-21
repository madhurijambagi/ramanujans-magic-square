const path = require("path");
const express = require("express");
const session = require("express-session");

require("./src/db"); // ensures schema is initialized on boot

const authRoutes = require("./src/routes/auth");
const gameRoutes = require("./src/routes/game");
const attemptsRoutes = require("./src/routes/attempts");
const leaderboardRoutes = require("./src/routes/leaderboard");
const adminRoutes = require("./src/routes/admin");
const dailyRoutes = require("./src/routes/daily");
const achievementsRoutes = require("./src/routes/achievements");
const ramanujanRoutes = require("./src/routes/ramanujan");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.use(
  session({
    name: "connect.sid",
    secret: process.env.SESSION_SECRET || "magic-square-dev-secret-change-me",
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      maxAge: 1000 * 60 * 60 * 24, // 24 hours
      sameSite: "lax",
    },
  })
);

app.use("/api/auth", authRoutes);
app.use("/api/game", gameRoutes);
app.use("/api/attempts", attemptsRoutes);
app.use("/api/leaderboard", leaderboardRoutes);
app.use("/api/admin", adminRoutes);
app.use("/api/daily", dailyRoutes);
app.use("/api/achievements", achievementsRoutes);
app.use("/api/ramanujan", ramanujanRoutes);

app.use(express.static(path.join(__dirname, "public")));

// Fallback 404 for unknown API routes
app.use("/api", (req, res) => {
  res.status(404).json({ error: "Not found." });
});

app.listen(PORT, () => {
  console.log(`Ramanujan's Magic Square running at http://localhost:${PORT}`);
});
