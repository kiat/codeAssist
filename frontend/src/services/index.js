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
    return Promise.reject(err);
  }
);

const service = (url, params, method = "get", options) =>
  instance({
    method: method,
    url,
    params: method === "get" ? params : "",
    data: method === "get" ? "" : params,
    ...options,
  });

export default service;
