import { mock, setup } from "mockjs";

export default function IMock(url, func, type = "get") {
  setup({
    timeout: "100-600",
  });

  mock(url, type, options => {
    const body = options.body;
    if (typeof body === "string") {
      const params = JSON.parse(body);
      return func(params);
    }
    return func(body);
  });
}
