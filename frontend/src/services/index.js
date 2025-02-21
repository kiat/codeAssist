import { message } from "antd";
import axios from "axios";
import { URL_PREFIX } from "../config/url";

const instance = axios.create({
  baseURL: URL_PREFIX,
});

instance.interceptors.response.use(
  res => {
    return res;
  },
  err => {
    let errorMessage = 'Operation failed';

    if (err.response) {
      // Server responded with a status other than 200 range
      if (err.response.status) {
        errorMessage = err.response.data.message;
      } else {
        errorMessage = 'An unexpected error occurred. Please try again.';
      }
    } else if (err.request) {
      // Request was made but no response was received
      errorMessage = 'No response from the server. Please check your network connection.';
    } else {
      // Something happened in setting up the request that triggered an error
      errorMessage = 'Request error. Please try again.';
    }
    message.error(errorMessage);
    return Promise.reject(err);
  }
);

/**
 * service is the only way for axios to communicate with the backend (for now)
 * @param {*} url the url extension to the URL_PREFIX
 * @param {*} params the params
 * @param {*} method the method
 * @param {*} options the additional options for axios
 * @returns 
 */
const service = (url, params, method = "get", options) =>
  instance({
    method: method,
    url,
    params: method === "get" ? params : undefined,
    data: method !== "get" ? params : undefined,
    ...options,
  });

export default service;
