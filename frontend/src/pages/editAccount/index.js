import { DeleteOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Checkbox,
  Col,
  Form,
  Input,
  PageHeader,
  Popover,
  Radio,
  Row,
  Select,
  Space,
  Typography,
  Modal
} from "antd";
import { useEffect, useState, useCallback } from "react";
import { useContext } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";

export default () => {
    const userId = JSON.parse(localStorage.getItem("userInfo"))?.id;
    const isStudent = JSON.parse(localStorage.getItem("userInfo"))?.isStudent;
    const [formData, setFormData] = useState({});
    const [placeholders, setPlaceholders] = useState({});

    useEffect(() => {
        if (userId) {
            fetchData(userId);
        }
    }, [userId]);

    const fetchData = async (id) => {
        try {
            const response = isStudent?await fetch(`${process.env.REACT_APP_API_URL}/get_student_byid?id=${id}`): await fetch(`${process.env.REACT_APP_API_URL}/get_instructor_byid?id=${id}`);
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            const data = await response.json();
            setPlaceholders(data);
        } catch (error) {
            console.error("Error fetching student data:", error);
        }
    };

    const onFinish = () => {
        const dataToSend = {
            id: userId,
            ...Object.fromEntries(
            Object.entries(formData).filter(([_, value]) => value !== undefined))
        };
        fetch(process.env.REACT_APP_API_URL + "/update_account", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(dataToSend)
        })
        .then((response) => response.json())
        .then((data) => console.log(data))
        .catch((err) => console.log(err))
    }

    const navigate = useNavigate();
    const navigateHome = () => {
        navigate("/dashboard");
    };

    return (
        <Form
            layout='vertical'
            wrapperCol={{
                lg: 12,
            }}
            style={{
                marginLeft: "20px",
            }}
            initialValues={formData}
            onValuesChange={(changedValues, allValues) => {
                setFormData(allValues);
            }}
        >
            <Space direction='vertical' style={{ width: "100%" }}>
                <PageHeader title='Edit Account' />
                <Card
                    title='Basic Settings'
                    bodyStyle={{
                        width: "100%",
                    }}
                >
                    <Form.Item label='EID' name="sis_user_id">
                        <Input placeholder={placeholders.sis_user_id || "Enter EID"} />
                    </Form.Item>
                    <Form.Item label='NAME' name='name'>
                        <Input placeholder={placeholders.name || "Enter Name"} />
                    </Form.Item>
                    <Form.Item label='EMAIL ADDRESS' name='email_address'>
                        <Input placeholder={placeholders.email_address || "Enter Email Address"} />
                    </Form.Item>
                    <Form.Item label='PASSWORD' name="password">
                        <Input placeholder={placeholders.password || "Enter Password"} />
                    </Form.Item>
                </Card>

                <Card>
                    <Space>
                        <Button
                            type='primary'
                            onClick={() => {
                                onFinish();
                                navigateHome();
                            }}
                        >
                            Update Account
                        </Button>
                    </Space>
                </Card>
            </Space>
        </Form>
    );
};

// import { DeleteOutlined } from "@ant-design/icons";
// import {
//   Button,
//   Card,
//   Checkbox,
//   Col,
//   Form,
//   Input,
//   PageHeader,
//   Popover,
//   Radio,
//   Row,
//   Select,
//   Space,
//   Typography,
//   Modal
// } from "antd";
// import { useEffect, useState, useCallback } from "react";
// import { useContext } from "react";
// import { useNavigate, useParams } from "react-router-dom";
// import { GlobalContext } from "../../App";

// export default () => {
//     const userId= JSON.parse(localStorage.getItem("userInfo"))?.id;

//     const [formData, setFormData] = useState({})

//     const onFinish = () => {
//         const dataToSend = {
//             id: userId,
//             ...Object.fromEntries(
//             Object.entries(formData).filter(([_, value]) => value !== undefined))
//         };
//         fetch(process.env.REACT_APP_API_URL + "/update_account", {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json"
//             },
//             body: JSON.stringify(dataToSend)
//         })
//         .then((response) => response.json())
//         .then((data) => console.log(data))
//         .catch((err) => console.log(err))
//     }

//     const navigate = useNavigate();
//     const navigateHome = () =>{
//         navigate("/dashboard")
//     }
  
//   return (
//     <Form
//       layout='vertical'
//       wrapperCol={{
//         lg: 12,
//       }}
//       style={{
//         marginLeft: "20px",
//       }}
//       onValuesChange={(changedValues, allValues) => {
//         setFormData(allValues)
//       }}
//     >
//       <Space direction='vertical' style={{ width: "100%" }}>
//         <PageHeader title='Edit Account' />
//         <Card
//           title='Basic Settings'
//           // bordered={false}
//           bodyStyle={{
//             width: "100%",
//           }}
//         >
//           <Form.Item label='EID' name = "sis_user_id">
//             {/* need to add plaeholder text for all of these fields --> same page for both student and insstructor */}
//             <Input placeholder="hello"/>
//           </Form.Item>
//           <Form.Item label='NAME' name='name'>
//             <Input />
//           </Form.Item>
//           <Form.Item label='EMAIL ADDRESS' name='email_address'>
//             <Input />
//           </Form.Item>
//           <Form.Item label='PASSWORD' name = "password">
//             <Input />
//           </Form.Item>
//         </Card>
        
//         <Card>
//           <Space>
//             <Button 
//             type='primary' 
//             onClick = {() => {
//                 onFinish();
//                 navigateHome();
//             }}
//             >Update Account</Button>
//           </Space>
//         </Card>
       
//       </Space>
//     </Form>
//   );
  
    
// };
