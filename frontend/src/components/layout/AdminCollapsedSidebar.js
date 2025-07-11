import React from 'react';
import { MenuUnfoldOutlined, BookOutlined, UserOutlined, TeamOutlined } from '@ant-design/icons';
import { Typography, Modal, Menu, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { GlobalContext } from '../../App';

const { Title } = Typography;

function AdminCollapsedSidebar({ toggleCollapsed }) {
  const navigate = useNavigate();
  const { updateUserInfo } = useContext(GlobalContext);

  const handleLogout = () => {
    Modal.confirm({
      title: 'Confirm Logout',
      content: 'Are you sure you want to logout?',
      okText: 'Yes',
      cancelText: 'No',
      onOk: () => {
        localStorage.removeItem("userInfo");
        updateUserInfo(null);
        navigate('/');
      }
    });
  };

  return (
    <div style={{ 
      width: 80, 
      backgroundColor: '#f0f2f5',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh'
    }}>
      <div style={{ padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
          <MenuUnfoldOutlined onClick={toggleCollapsed} style={{ fontSize: '18px', cursor: 'pointer' }} />
        </div>

        <Menu
          mode="inline"
          style={{ border: 'none', backgroundColor: 'transparent' }}
          defaultSelectedKeys={['dashboard']}
        >
          <Menu.Item key="courses" icon={<BookOutlined />} onClick={() => navigate('/admin/courses')} />
          <Menu.Item key="students" icon={<UserOutlined />} onClick={() => navigate('/admin/students')} />
          <Menu.Item key="instructors" icon={<TeamOutlined />} onClick={() => navigate('/admin/instructors')} />
        </Menu>
      </div>

      {/* Account Section at Bottom */}
      <div style={{ 
        marginTop: 'auto', 
        borderTop: '1px solid #e8e8e8',
        padding: '16px',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <Button 
          type="text"
          style={{ minWidth: 'unset', width: '100%' }}
          onClick={handleLogout}
        >
          A
        </Button>
      </div>
    </div>
  );
}

export default AdminCollapsedSidebar; 