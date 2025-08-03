import { useCallback, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { GlobalContext } from "../../App";
import { GoogleLogin } from '@react-oauth/google';
import GoogleSignUp from "./googleSignUp";
import { googleLogin } from "../../services/user";

/**
 * home modal
 * @returns
 */
export default function Home() {
  const [googleModalOpen, setGoogleModalOpen] = useState(false);
  const [googleValues, setGoogleValues] = useState({});
  const { userInfo, updateUserInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  const toggleGoogleModal = useCallback(() => {
    setGoogleModalOpen(googleModalOpen => !googleModalOpen);
  }, []);

  useEffect(() => {
    if (userInfo?.name) {
      navigate("/dashboard");
      return;
    }
  }, [userInfo, navigate]);

  const handleOAuth = async (credentialResponse) => {
    let res;
    try {
      res = await googleLogin(credentialResponse);
    }
    catch (error) {
      if (!error.response) {
        alert(`User authentication failed.`);
        return;
      };
      if (error.response.status === 400) {
        const errorType = error.response.data;
        alert(`User authentication failed. ${errorType}`);
        return;
      };
    }

    const role = res.data?.role;

  if (res.data?.name && role) {
    // Existing user (admin, student, or instructor)
    const userInfo = {
      name: res.data.name,
      id: res.data.id,
      role: role,
      isAdmin: role === "admin",
      isStudent: role === "student",
    };
    localStorage.setItem("userInfo", JSON.stringify(userInfo));
    updateUserInfo(userInfo);

    // Redirect based on role
    if (role === "admin") {
      navigate("/admin/dashboard");
    } else if (role === "student") {
      navigate("/dashboard");
    } else if (role === "instructor") {
      navigate("/dashboard");
    }
    return;
  }

  // For non-admins, store credential and show sign-up modal
  setGoogleValues({
    ...googleValues,
    credential: credentialResponse.credential,
    email: res.data?.email || "",
  });
  toggleGoogleModal();
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        backgroundColor: "#f2f5f5",
        height: "100vh",
        marginLeft: "-20px",
      }}
    >
      <div
        style={{
          width: "1200px",
        }}
      >
        <div
          style={{
            lineHeight: "80px",
            fontSize: "30px",
            fontWeight: "bold",
            borderBottom: "1px solid #c0c0c0",
            marginLeft: "30px",
            marginRight: "30px",
          }}
        >
          Grading
        </div>
        <div>
          <div
            style={{
              height: "300px",
              textAlign: "center",
              marginTop: "150px",
            }}
          >
            <div
              style={{
                fontSize: "40px",
              }}
            >
              Get Automated Feedback about Your Assignments!
            </div>
            <div
              style={{
                marginTop: "100px",
                display: "flex",
                justifyContent: "center",
                textAlign: "center"
              }}
            >
              <GoogleLogin
                onSuccess={credentialResponse => {
                  handleOAuth(credentialResponse);
                }}
                onError={() => {
                  console.log('Login Failed');
                }}
                // style={{
                //   flex: 1,
                //   display: "flex",
                // }}
              />
            </div>
          </div>
        </div>
      </div>
      <GoogleSignUp open={googleModalOpen} onCancel={toggleGoogleModal} googleValues={googleValues}/>
    </div>
  );
}
