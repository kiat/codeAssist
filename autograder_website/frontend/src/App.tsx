import axios from 'axios'
import { useState }  from 'react';
import { Button, Input, Layout, Menu, Space, Typography } from 'antd';

const { Header, Content, Footer } = Layout;

// CHANGE THIS baseURL TO A QUALIFIED DOMAIN NAME
const baseURL = "http://localhost:5000"

const App: React.FC = () => {
  const [message, setMessage] = useState("Waiting for message")
  const [textbox, setTextbox] = useState("")

  const { Title } = Typography
  let menuItems: string[] = ['Upload Assignment']

  const header = {
    "userid":localStorage.getItem("userid"),
    "token":localStorage.getItem("token"),
    "Content-Type": "multipart/form-data",
    "Access-Control-Allow-Origin": "*"
  }

  return (
    <Layout className="layout" style={{ height:'100vh'}}>
      <Header style={{ display: 'full', alignItems: 'center' }}>
        <Menu
          theme="dark"
          mode="horizontal"
          defaultSelectedKeys={['0']}
          items={menuItems.map((_, index) => {
            const key = index;
            return {
              key,
              label: _,
            };
          })}
        />
      </Header>
      <Content style={{ padding: '50px 50px', textAlign: 'center'}}>
          <Title>
            Upload assignment below
          </Title>
          <Space.Compact style={{ width: '100%' }}>
            <Input
              onChange={(e) => setTextbox(e.target.value)}
            />
            <Button 
              type="primary" 
              onClick={
                () => axios.post(baseURL + "/message", { message: textbox })
              }
            >
{/* axios.get(baseURL).then((response) => { setMessage(response.data); }) */}
{/* axios.post(baseURL + "/message", { message: textbox }) */}

            Submit Message
            </Button>
          </Space.Compact>
          <Button
            type="primary"
            onClick={
              () => axios.get(baseURL + "/getlatestmessage").then((response) => setMessage(response.data.message))
            }
          >
            Get Latest Message
          </Button>
          <p>{message}</p>
          <p>{textbox}</p>
      </Content>
      <Footer style={{ textAlign: 'center' }}>Created by Allen Wu</Footer>
    </Layout>
  );
};

export default App;