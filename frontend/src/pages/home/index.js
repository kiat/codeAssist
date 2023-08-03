import { Button } from "antd";
import { useCallback, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { GlobalContext } from "../../App";
import LogInModal from "./logInModal";
import SignUpModal from "./signUpModal";

/**
 * home modal
 * @returns
 */
export default function Home() {
  const [isModalOpen, setModalOpen] = useState(false);
  const [logInModalOpen, setlogInModalOpen] = useState(false);
  const { userInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  // control login window modal
  const toggleLogInModal = useCallback(() => {
    setlogInModalOpen(logInModalOpen => !logInModalOpen);
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
              }}
            >
              <Button
                onClick={openModal}
                type='primary'
                size='large'
                style={{
                  marginRight: "20px",
                  width: "150px",
                }}
              >
                Sign Up
              </Button>
              <Button
                onClick={toggleLogInModal}
                size='large'
                style={{
                  width: "150px",
                }}
              >
                Log In
              </Button>
            </div>
          </div>
        </div>
      </div>
      <SignUpModal open={isModalOpen} onCancel={closeModal} />
      <LogInModal open={logInModalOpen} onCancel={toggleLogInModal} />
    </div>
  );
}
