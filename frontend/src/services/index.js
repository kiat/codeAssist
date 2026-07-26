import { message } from "antd";
import axios from "axios";
import { URL_PREFIX } from "../config/url";

const instance = axios.create({
  baseURL: URL_PREFIX,
  withCredentials: true,
});

instance.interceptors.response.use(
  res => {
    return res;
  },
  err => {
    let errorMessage = "Operation failed";
    const responseMessage = err.response?.data?.message || "";
    const isAuthMismatch =
      err.response?.status === 403 &&
      (
        responseMessage.includes("Not authenticated") ||
        responseMessage.includes("You can only access your own data")
      );

    if (err.response?.status === 401 || isAuthMismatch) {
      localStorage.removeItem("userInfo");
      localStorage.removeItem("courseInfo");
      localStorage.removeItem("courseRole");
      window.location.assign("/");
      return Promise.reject(err);
    }

    if (err.response) {
      if (err.response.status) {
        errorMessage = err.response.data.message;
      } else {
        errorMessage = "An unexpected error occurred. Please try again.";
      }
    } else if (err.request) {
      errorMessage = "No response from the server. Please check your network connection.";
    } else {
      errorMessage = "Request error. Please try again.";
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
    params: (method === "get" || method === "delete") ? params : undefined,
    data: (method === "get" || method === "delete") ? undefined : params,
    ...options,
  });

export default service;
