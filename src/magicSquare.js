/**
 * Magic square engine.
 * - Odd n (n>=3): Siamese method (De la Loubère).
 * - Doubly-even n (n%4===0): standard complement-swap method.
 * - Singly-even n (n%4===2): Strachey / LUX method, built on an odd Siamese core.
 * - n===2: mathematically impossible (no arrangement of 4 distinct numbers
 *   can satisfy both row/column and both diagonal sums simultaneously).
 * - n===1: trivial/degenerate, excluded from the playable range.
 */

const MIN_ORDER = 2;
const MAX_ORDER = 10;
// Orders that can actually be turned into a valid magic square.
const ALLOWED_ORDERS = [3, 4, 5, 6, 7, 8, 9, 10];
// Every order offered in the UI, including the impossible one (2), so the
// impossibility itself can be explained rather than hidden.
const DISPLAY_ORDERS = [2, 3, 4, 5, 6, 7, 8, 9, 10];

function isAllowedOrder(order) {
  return ALLOWED_ORDERS.includes(order);
}

function magicConstant(n) {
  return (n * (n * n + 1)) / 2;
}

function orderInfo(n) {
  if (!Number.isInteger(n) || n < MIN_ORDER || n > MAX_ORDER) {
    return { order: n, possible: false, method: null, reason: `Order must be between ${MIN_ORDER} and ${MAX_ORDER}.` };
  }
  if (n === 2) {
    return {
      order: n,
      possible: false,
      method: null,
      reason:
        "A 2\u00d72 magic square is not mathematically possible. With only 4 distinct numbers, " +
        "there is no arrangement where both rows, both columns, AND both diagonals all share the same sum " +
        "(this has been proven for order 2 \u2014 it's the one square size that cannot be magic).",
    };
  }
  const method = n % 2 === 1 ? "siamese" : n % 4 === 0 ? "doubly-even" : "singly-even";
  return { order: n, possible: true, method, target: magicConstant(n) };
}

function arraysEqual(a, b) {
  return a.length === b.length && a.every((v, i) => v === b[i]);
}

/* ---------------- odd orders: Siamese method ---------------- */
function generateSiameseGrid(n) {
  const grid = Array.from({ length: n }, () => Array(n).fill(0));
  const path = [];
  let row = 0;
  let col = Math.floor(n / 2);
  for (let num = 1; num <= n * n; num++) {
    grid[row][col] = num;
    path.push({ row, col, value: num });
    const nextRow = (row - 1 + n) % n;
    const nextCol = (col + 1) % n;
    if (grid[nextRow][nextCol] !== 0) {
      row = (row + 1) % n;
    } else {
      row = nextRow;
      col = nextCol;
    }
  }
  return { grid, path };
}

/* ---------------- doubly-even orders (n % 4 === 0) ---------------- */
function generateDoublyEvenGrid(n) {
  const grid = Array.from({ length: n }, () => Array(n).fill(0));
  const path = [];
  const total = n * n;
  let num = 1;
  const sequential = [];
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      sequential.push({ r, c, value: num });
      num++;
    }
  }
  for (const { r, c, value } of sequential) {
    const br = r % 4;
    const bc = c % 4;
    const marked = br === bc || br + bc === 3;
    const finalValue = marked ? total + 1 - value : value;
    grid[r][c] = finalValue;
    path.push({ row: r, col: c, value: finalValue });
  }
  return { grid, path };
}

/* ---------------- singly-even orders (n % 4 === 2): LUX / Strachey method ---------------- */
function generateSinglyEvenGrid(n) {
  const m = n / 2; // odd
  const { grid: base } = generateSiameseGrid(m);
  const msq = m * m;

  const grid = Array.from({ length: n }, () => Array(n).fill(0));

  // Quadrant placement: TL=top-left(+0), TR=top-right(+2msq), BL=bottom-left(+3msq), BR=bottom-right(+msq)
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < m; c++) {
      grid[r][c] = base[r][c]; // TL
      grid[r + m][c] = base[r][c] + 3 * msq; // BL
      grid[r][c + m] = base[r][c] + 2 * msq; // TR
      grid[r + m][c + m] = base[r][c] + msq; // BR
    }
  }

  const k = (m - 1) / 2;

  // Swap the leftmost k columns between A (top) and C (bottom), except in
  // the middle row, where the swap is shifted one column to the right and
  // extended by one extra column (this is the "LUX" step that fixes the
  // sums broken by the naive quadrant assignment above).
  const midRow = Math.floor(m / 2);
  for (let r = 0; r < m; r++) {
    let colsToSwap;
    if (r === midRow) {
      colsToSwap = [];
      for (let c = 1; c <= k; c++) colsToSwap.push(c);
    } else {
      colsToSwap = [];
      for (let c = 0; c < k; c++) colsToSwap.push(c);
    }
    for (const c of colsToSwap) {
      const tmp = grid[r][c];
      grid[r][c] = grid[r + m][c];
      grid[r + m][c] = tmp;
    }
  }

  // Swap the rightmost (k-1) columns between B (top) and D (bottom).
  for (let r = 0; r < m; r++) {
    for (let c = m - k + 1; c < m; c++) {
      const tmp = grid[r][c + m];
      grid[r][c + m] = grid[r + m][c + m];
      grid[r + m][c + m] = tmp;
    }
  }

  const path = [];
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) path.push({ row: r, col: c, value: grid[r][c] });
  return { grid, path };
}

function generateMagicSquare(n, { withPath = false } = {}) {
  const info = orderInfo(n);
  if (!info.possible) throw new Error(info.reason);
  let result;
  if (info.method === "siamese") result = generateSiameseGrid(n);
  else if (info.method === "doubly-even") result = generateDoublyEvenGrid(n);
  else result = generateSinglyEvenGrid(n);
  const flat = result.grid.flat();
  return withPath ? { flat, path: result.path } : flat;
}

function validateGrid(candidateFlat, n, target = magicConstant(n)) {
  const grid = [];
  for (let r = 0; r < n; r++) grid.push(candidateFlat.slice(r * n, r * n + n));
  const rows = grid.map((r) => r.reduce((a, b) => a + b, 0) === target);
  const cols = [];
  for (let c = 0; c < n; c++) {
    let sum = 0;
    for (let r = 0; r < n; r++) sum += grid[r][c];
    cols.push(sum === target);
  }
  let diagMain = 0, diagAnti = 0;
  for (let i = 0; i < n; i++) { diagMain += grid[i][i]; diagAnti += grid[i][n - 1 - i]; }
  const diagonals = [diagMain === target, diagAnti === target];
  const solved = rows.every(Boolean) && cols.every(Boolean) && diagonals.every(Boolean);
  return { rows, cols, diagonals, solved, target };
}

/**
 * Fisher-Yates shuffle of a flat magic square into a scrambled puzzle state.
 * Guaranteed to differ from the solved arrangement (for n > 1).
 */
function scrambleSquare(flatSquare) {
  const arr = [...flatSquare];
  let scrambled;
  do {
    scrambled = [...arr];
    for (let i = scrambled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [scrambled[i], scrambled[j]] = [scrambled[j], scrambled[i]];
    }
  } while (arraysEqual(scrambled, arr) && arr.length > 1);
  return scrambled;
}

/**
 * Small deterministic PRNG (mulberry32) so the daily challenge produces the
 * exact same scramble for every user who requests it on a given date.
 */
function mulberry32(seed) {
  let t = seed >>> 0;
  return function () {
    t |= 0;
    t = (t + 0x6d2b79f5) | 0;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function hashSeed(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/**
 * Deterministically scrambles a flat magic square given a string seed
 * (e.g. "2026-07-29:5"), using Fisher-Yates driven by a seeded PRNG.
 */
function seededScramble(flatSquare, seedString) {
  const rand = mulberry32(hashSeed(seedString));
  const arr = [...flatSquare];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  if (arraysEqual(arr, flatSquare) && arr.length > 1) {
    return seededScramble(flatSquare, seedString + ":r");
  }
  return arr;
}

function todayDateString() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD (UTC)
}

/**
 * Ramanujan-style "date magic square" — a 4x4 square built from four
 * numbers (traditionally day, month, century, and year-within-century of a
 * date) so that every row, every column, and BOTH diagonals sum to the same
 * total (a + b + c + d). This is the general version of the party trick
 * Ramanujan is famous for demonstrating with his own birthdate. The first
 * row is always exactly [a, b, c, d] so the audience sees their chosen
 * numbers appear unmodified.
 *
 * The offset matrix below was derived and numerically verified (every row,
 * column and diagonal of the offsets sums to exactly 0, and each of a/b/c/d
 * receives four distinct offsets) so the identity holds for ANY four
 * integers. Because the four input numbers are arbitrary, this construction
 * cannot *guarantee* all 16 resulting cells are distinct for every possible
 * date (e.g. a day and a month that happen to be numerically close can
 * collide) — the returned object flags this so the UI can be honest about it.
 */
/**
 * Ramanujan-style "date magic square" — the classical 4x4 construction:
 * split a date into DD (day), MM (month), CC (century), YY (two-digit
 * year), place them unmodified as the first row, then fill the rest with
 * this fixed offset pattern:
 *
 *   DD      MM      CC      YY
 *   YY+1    CC-1    MM-3    DD+3
 *   MM-2    DD+2    YY+2    CC-2
 *   CC+1    YY-1    DD+1    MM-1
 *
 * Every row, column, and both diagonals sum to DD+MM+CC+YY. This is the
 * historical trick Ramanujan is known for demonstrating with his own
 * birthdate.
 *
 * Some of the offsets are negative (-1, -2, -3), so for small MM (Jan/Feb/
 * Mar), small CC, or small YY (e.g. YY=01) a cell can land on zero or
 * negative — not a natural number. To guarantee every cell is a natural
 * number (>= 1) while preserving the magic property exactly, we add one
 * uniform constant to all 16 cells whenever the raw construction would dip
 * below 1. Adding the same constant K to every cell increases every row/
 * column/diagonal sum by the same 4K, so the square is still magic — its
 * target just becomes (DD+MM+CC+YY) + 4K instead of DD+MM+CC+YY. When the
 * date is "large enough" already, K is 0 and the first row is exactly
 * [DD, MM, CC, YY] as in the classic trick.
 */
function generateRamanujanSquare(a, b, c, d) {
  [a, b, c, d].forEach((v) => {
    if (!Number.isFinite(v) || !Number.isInteger(v)) {
      throw new Error("All four inputs must be whole numbers.");
    }
  });
  let grid = [
    [a, b, c, d],
    [d + 1, c - 1, b - 3, a + 3],
    [b - 2, a + 2, d + 2, c - 2],
    [c + 1, d - 1, a + 1, b - 1],
  ];

  const minVal = Math.min(...grid.flat());
  const shift = minVal < 1 ? 1 - minVal : 0;
  if (shift > 0) {
    grid = grid.map((row) => row.map((v) => v + shift));
  }

  const target = a + b + c + d + 4 * shift;
  const flat = grid.flat();
  const distinct = new Set(flat).size === 16;
  const allNatural = flat.every((v) => Number.isInteger(v) && v >= 1);
  const check = validateGrid(flat, 4, target);
  return { grid, flat, target, distinct, valid: check.solved, allNatural, shift };
}

module.exports = {
  ALLOWED_ORDERS,
  DISPLAY_ORDERS,
  MIN_ORDER,
  MAX_ORDER,
  isAllowedOrder,
  orderInfo,
  magicConstant,
  generateMagicSquare,
  validateGrid,
  arraysEqual,
  scrambleSquare,
  seededScramble,
  todayDateString,
  generateRamanujanSquare,
};
