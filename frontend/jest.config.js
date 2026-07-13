// frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',

  transform: {
    '^.+\\.[jt]sx?$': 'babel-jest',
  },

  // transpile axios (and any other ESM-only deps) through Babel
  transformIgnorePatterns: [
    '/node_modules/(?!(axios|@codemirror|@lezer|@marijn)/)',
  ],

  // stub CSS imports
  moduleNameMapper: {
    '\\.(css|sass|scss)$': 'identity-obj-proxy',
  },

  setupFilesAfterEnv: ['@testing-library/jest-dom'],
};
