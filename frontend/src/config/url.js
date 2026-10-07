/*
 * Set REACT_APP_API_URL in frontend/.env to change the backend URL
 * (e.g. /api behind nginx). Falls back to the local backend.
 */

/*
 * Apifox local mocx
 */

//export const URL_PREFIX = "http://127.0.0.1:4523/m1/1927806-0-default";

/*
 * Localhost
 */

export const URL_PREFIX = process.env.REACT_APP_API_URL || "http://localhost:5001";

/*
 * AWS
 */

// export const URL_PREFIX = "http://3.212.97.84:5001";
