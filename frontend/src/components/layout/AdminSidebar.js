import React, { useState } from 'react';
import { MenuFoldOutlined, BookOutlined, UserOutlined, TeamOutlined } from '@ant-design/icons';
import { Typography, Modal, Menu, Popover } from 'antd';
import { Link, useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { GlobalContext } from '../../App';
import AccountPopoverContent from './accountPopoverContent';
import AdminCollapsedSidebar from './AdminCollapsedSidebar';

function AdminSidebar() {
  const navigate = useNavigate();
  const { updateUserInfo } = useContext(GlobalContext);
  const [collapsed, setCollapsed] = useState(false);

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

  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  if (collapsed) {
    return <AdminCollapsedSidebar toggleCollapsed={toggleCollapsed} />;
  }

  return (
    <div style={{
      width: 200,
      height: '100vh',
      backgroundColor: '#fff',
      borderRight: '1px solid #e8e8e8',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      position: 'relative',
      boxSizing: 'border-box'
    }}>
      <div>
        <div>
          <Typography.Title
                    level={4}
                    style={{
                      fontWeight: 'bold',
                      color: '#1890ff',
                      marginLeft: '15px',
                      marginTop: '12px',
                    }}
                  >
          <Link to='/admin/dashboard'>Feedback</Link>
          <MenuFoldOutlined onClick={toggleCollapsed} style={{ marginLeft: '30px' }} />
          </Typography.Title>
        </div>
        <Menu mode="vertical" selectable={false}>
          <Menu.Item key="courses" icon={<BookOutlined />}>
            <Link to="/admin/courses">Courses</Link>
          </Menu.Item>
          <Menu.Item key="students" icon={<UserOutlined />}>
            <Link to="/admin/students">Students</Link>
          </Menu.Item>
          <Menu.Item key="instructors" icon={<TeamOutlined />}>
            <Link to="/admin/instructors">Instructors</Link>
          </Menu.Item>
        </Menu>
      </div>

      <Popover content={<AccountPopoverContent />} placement='topLeft'>
        <div
          style={{
            backgroundColor: '#1890ff',
            color: 'white',
            padding: '10px 20px',
            fontWeight: 'bold',
            cursor: 'pointer',
            flexShrink: 0
          }}
        >
          <UserOutlined />
          <span style={{ marginLeft: 8 }}>Account</span>
        </div>
      </Popover>
    </div>
  );
}

export default AdminSidebar;