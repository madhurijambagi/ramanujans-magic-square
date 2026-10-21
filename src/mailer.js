/**
 * Minimal mail helper.
 *
 * If SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS (and optionally
 * SMTP_FROM) are set in the environment, real emails are sent via
 * nodemailer. Otherwise — e.g. in local development, or on a fresh
 * deployment before SMTP is configured — the message is written to the
 * server console instead, so password resets and verification links can
 * still be copy-pasted by whoever operates the server. Nothing here ever
 * throws for a missing SMTP config; email is a convenience layer, not a
 * hard dependency of account security (the token-based flows work the
 * same either way).
 */

let transporter = null;
let attemptedSetup = false;

function getTransporter() {
  if (attemptedSetup) return transporter;
  attemptedSetup = true;
  const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS } = process.env;
  if (!SMTP_HOST || !SMTP_PORT || !SMTP_USER || !SMTP_PASS) return null;
  try {
    // Required lazily so the app still boots if nodemailer isn't installed
    // (e.g. dependency not yet added on an older deployment).
    const nodemailer = require("nodemailer");
    transporter = nodemailer.createTransport({
      host: SMTP_HOST,
      port: parseInt(SMTP_PORT, 10),
      secure: parseInt(SMTP_PORT, 10) === 465,
      auth: { user: SMTP_USER, pass: SMTP_PASS },
    });
  } catch (e) {
    console.warn("[mailer] SMTP configured but nodemailer is unavailable; falling back to console logging.");
    transporter = null;
  }
  return transporter;
}

async function sendMail({ to, subject, text }) {
  const t = getTransporter();
  if (!t) {
    console.log(`\n[mailer] (no SMTP configured — logging instead of sending)\nTo: ${to}\nSubject: ${subject}\n${text}\n`);
    return { delivered: false };
  }
  const from = process.env.SMTP_FROM || process.env.SMTP_USER;
  await t.sendMail({ from, to, subject, text });
  return { delivered: true };
}

module.exports = { sendMail };
