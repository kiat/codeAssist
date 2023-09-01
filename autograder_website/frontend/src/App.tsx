import axios from 'axios'
import { useState }  from 'react';
import { Button, Input, Layout, Menu, message, Space, Typography, Upload } from 'antd';
import type { UploadFile } from 'antd/es/upload/interface';
import type { UploadProps } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const { Header, Content, Footer } = Layout;

// CHANGE THIS baseURL TO A QUALIFIED DOMAIN NAME
const baseURL = "http://localhost:5000"

const App: React.FC = () => {
  // const [text, setText] = useState("Waiting for message")
  // const [textbox, setTextbox] = useState("")
   const [fileList, setFileList] = useState<UploadFile[]>([]);
   const [loading, setLoading] = useState(false);

  const handleChange: UploadProps['onChange'] = (info) => {
    let newFileList = [...info.fileList];
    // Only to show one recently uploaded file, and old ones will be replaced by the new
    newFileList = newFileList.slice(-1);
    setFileList(newFileList);

    if (info.file.status !== 'uploading') {
      console.log(info.file, info.fileList);
      setLoading(true)
    }
    if (info.file.status === 'done') {
      message.success(`${info.file.name} file uploaded successfully`);
      setLoading(false)
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} file upload failed.`);
    }
  };

  const props = {
    action: baseURL + "/upload",
    onChange: handleChange,
    multiple: true,
  };

  const { Title } = Typography
  let menuItems: string[] = ['Upload Assignment']

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

          <Upload {...props} fileList={fileList}>
            <Button icon={<UploadOutlined />}>Upload</Button>
          </Upload>

          <p>{loading}</p>


          {/* <Space.Compact style={{ width: '100%' }}>
            <Input
              onChange={(e) => setTextbox(e.target.value)}
            />
            <Button 
              type="primary" 
              onClick={
                () => axios.post(baseURL + "/message", { message: textbox })
              }
            >
            Submit Message
            </Button>
          </Space.Compact>
          <Button
            type="primary"
            onClick={
              () => axios.get(baseURL + "/getlatestmessage").then((response) => setText(response.data.message))
            }
          >
            Get Latest Message
          </Button>
          <p>{text}</p>
          <p>{textbox}</p> */}

      </Content>
      <Footer style={{ textAlign: 'center' }}>Created by Allen Wu</Footer>
    </Layout>
  );
};

export default App;

{/* axios.get(baseURL).then((response) => { setMessage(response.data); }) */}
{/* axios.post(baseURL + "/message", { message: textbox }) */}