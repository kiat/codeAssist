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
    message.error("operation failed");
    return Promise.reject(err); // TODO: put real error reason
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
    params: method === "get" ? params : "",
    data: method === "get" ? "" : params,
    ...options,
  });

export default service;
