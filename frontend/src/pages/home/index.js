import { Button } from "antd";
import { useCallback, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { GlobalContext } from "../../App";
import LogInModal from "./logInModal";
import SignUpModal from "./signUpModal";

import { GoogleLogin } from '@react-oauth/google';
import { useGoogleOneTapLogin } from '@react-oauth/google';
import GoogleSignUp from "./googleSignUp";
import { userLogin } from "../../services/user";

/**
 * home modal
 * @returns
 */
export default function Home() {
  const [isModalOpen, setModalOpen] = useState(false);
  const [logInModalOpen, setlogInModalOpen] = useState(false);
  const [googleModalOpen, setGoogleModalOpen] = useState(false);
  const [googleValues, setGoogleValues] = useState({});
  const { userInfo, updateUserInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  // control login window modal
  const toggleLogInModal = useCallback(() => {
    setlogInModalOpen(logInModalOpen => !logInModalOpen);
  }, []);

  const toggleGoogleModal = useCallback(() => {
    setGoogleModalOpen(googleModalOpen => !googleModalOpen);
  }, []);

  // open signup window
  const openModal = () => {
    setModalOpen(true);
  };

  // close signup window
  const closeModal = () => {
    setModalOpen(false);
  };

  useEffect(() => {
    if (userInfo?.name) {
      navigate("/dashboard");
      return;
    }
  }, [userInfo, navigate]);

  const handleOAuth = async (credentialResponse) => {
    let res;
    try {
      res = await userLogin(credentialResponse);
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

    if (res.data.name) {
      console.log("valid login")
      const userInfo = {
        name: res.data?.name,
        id: res.data?.id,
        isStudent: res.data?.student,
      };
      localStorage.setItem("userInfo", JSON.stringify(userInfo));
      updateUserInfo(userInfo);
      return
    }

    setGoogleValues ({
      ...googleValues,
      credential: credentialResponse.credential
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
                marginBottom: "15px",
                paddingLeft: "475px",
                paddingRight: "475px",
                display: "flex",
                justifyContent: "center",
                gap: "20px",
              }}
            >
              <Button
                onClick={openModal}
                type='primary'
                size='large'
                style={{
                  flex: 1,
                  display: "flex",
                  justifyContent: "center"
                }}
              >
                Sign Up
              </Button>
              <Button
                onClick={toggleLogInModal}
                size='large'
                style={{
                  flex: 1,
                  display: "flex",
                  justifyContent: "center"
                }}
              >
                Log In
              </Button>
            </div>
            <div
              style={{
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
      <SignUpModal open={isModalOpen} onCancel={closeModal} />
      <LogInModal open={logInModalOpen} onCancel={toggleLogInModal} />
      <GoogleSignUp open={googleModalOpen} onCancel={toggleGoogleModal} googleValues={googleValues}/>
    </div>
  );
}