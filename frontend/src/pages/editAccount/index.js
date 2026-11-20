import { Alert, Button, Card, Form, Input, message, PageHeader, Space } from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const MIN_PASSWORD_LENGTH = 8;

/**
 * Edit your own account: name, and password.
 *
 * Changing the password needs the current password; the backend checks it
 * (/update_account), this page only collects it. Accounts that sign in with
 * Google only have no password (has_password from /get_user_by_id), so the
 * password fields are replaced by a note.
 */
export default function EditAccount() {
  const userId = JSON.parse(localStorage.getItem("userInfo") || "null")?.id;
  const [form] = Form.useForm();
  const [account, setAccount] = useState({});
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!userId) return;
    const load = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/get_user_by_id?id=${userId}`, {
          credentials: "include",
        });
        if (!response.ok) throw new Error("Could not load your account");
        setAccount(await response.json());
      } catch (error) {
        message.error(error.message);
      }
    };
    load();
  }, [userId]);

  // Until the account loads, assume it has a password so the fields don't flicker.
  const hasPassword = account.has_password !== false;

  const save = async () => {
    let values;
    try {
      values = await form.validateFields();
    } catch {
      return; // the form shows what to fix
    }

    const payload = { id: userId };
    if (values.name?.trim()) payload.name = values.name.trim();
    if (values.password) {
      payload.password = values.password;
      payload.current_password = values.current_password;
    }
    if (!payload.name && !payload.password) {
      message.info("Nothing to update");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/update_account`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        message.error(data.message || "Could not update your account");
        return;
      }
      message.success(payload.password ? "Password changed" : "Account updated");
      navigate("/dashboard");
    } catch {
      message.error("Could not update your account");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Form form={form} layout="vertical" wrapperCol={{ lg: 12 }} style={{ marginLeft: 20 }}>
      <Space direction="vertical" style={{ width: "100%" }}>
        <PageHeader title="Edit Account" />
        <Card title="Basic Settings">
          {/* EID and email can't be changed here */}
          <Form.Item label="EID">
            <Input value={account.sis_user_id || ""} disabled aria-label="EID" />
          </Form.Item>
          <Form.Item label="NAME" name="name">
            <Input placeholder={account.name || "Enter name"} aria-label="Name" />
          </Form.Item>
          <Form.Item label="EMAIL ADDRESS">
            <Input value={account.email_address || ""} disabled aria-label="Email address" />
          </Form.Item>
        </Card>

        <Card title="Change Password">
          {hasPassword ? (
            <>
              <Form.Item
                label="NEW PASSWORD"
                name="password"
                rules={[{ min: MIN_PASSWORD_LENGTH, message: `Use at least ${MIN_PASSWORD_LENGTH} characters` }]}
              >
                <Input.Password placeholder="Leave empty to keep your password" autoComplete="new-password" aria-label="New password" />
              </Form.Item>
              <Form.Item
                label="CONFIRM NEW PASSWORD"
                name="confirm_password"
                dependencies={["password"]}
                rules={[
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      const password = getFieldValue("password");
                      if (!password || value === password) return Promise.resolve();
                      return Promise.reject(new Error("The new passwords don't match"));
                    },
                  }),
                ]}
              >
                <Input.Password autoComplete="new-password" aria-label="Confirm new password" />
              </Form.Item>
              <Form.Item
                label="CURRENT PASSWORD"
                name="current_password"
                dependencies={["password"]}
                extra="Needed to change your password."
                rules={[
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!getFieldValue("password") || value) return Promise.resolve();
                      return Promise.reject(new Error("Enter your current password"));
                    },
                  }),
                ]}
              >
                <Input.Password autoComplete="current-password" aria-label="Current password" />
              </Form.Item>
            </>
          ) : (
            <Alert
              type="info"
              showIcon
              message="You sign in with Google, so there is no password to change."
            />
          )}
        </Card>

        <Card>
          <Space>
            <Button type="primary" onClick={save} loading={saving}>
              Update Account
            </Button>
            <Button onClick={() => navigate("/dashboard")}>Cancel</Button>
          </Space>
        </Card>
      </Space>
    </Form>
  );
}
