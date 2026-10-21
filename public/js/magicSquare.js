const MagicSquare = {
  // Every order offered in the UI (2 is included so its impossibility can
  // be explained rather than hidden), and the magic constant formula
  // M(n) = n(n²+1)/2, which holds for any n regardless of whether a magic
  // arrangement actually exists for that n.
  DISPLAY_ORDERS: [2, 3, 4, 5, 6, 7, 8, 9, 10],
  ALLOWED_ORDERS: [3, 4, 5, 6, 7, 8, 9, 10],
  MIN_ORDER: 2,
  MAX_ORDER: 10,

  magicConstant(n) {
    return (n * (n * n + 1)) / 2;
  },

  isPossible(n) {
    return n !== 2 && n >= 3 && n <= 10;
  },

  // Local, odd-only generator used purely for the decorative landing-page
  // animation (order 5) so it doesn't need a network round trip. The real
  // game screens always fetch their puzzle (including even orders) from
  // the server, which is also where solutions are validated.
  generateWithPath(n) {
    if (n % 2 === 0) throw new Error("This local helper only supports odd orders (used for the order-5 landing animation).");
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
    return { flat: grid.flat(), path };
  },
};
