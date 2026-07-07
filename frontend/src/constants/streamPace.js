/** 思考区：偏慢，便于肉眼跟随；积压大时自动加速追最新 */
export const THINKING_PACE = {
  msPerChar: 28,
  maxPerFrame: 2,
  followLatest: true,
  catchUpThreshold: 80,
  catchUpMaxPerFrame: 28,
  catchUpMinMsPerChar: 6,
};

/** 答案正文：略快，长文可自然追平积压 */
export const ANSWER_PACE = {
  msPerChar: 10,
  maxPerFrame: 8,
};
