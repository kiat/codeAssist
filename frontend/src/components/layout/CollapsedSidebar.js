import React from 'react';
import { MenuUnfoldOutlined, PicRightOutlined, UserOutlined } from '@ant-design/icons';
import { Typography } from 'antd';

function CollapsedSidebar({ toggleCollapsed, pathname }) {
    return (
        <>
            <div
                style={{
                    fontWeight: "bold",
                    color: '#1890ff',
                    paddingLeft: "20px",
                }}
            >
                <div>
                    <Typography.Title
                        level={4}
                        style={{
                            marginLeft: '15px',
                            marginTop: '12px',
                            marginBottom: "20px",
                        }}
                    >
                        <MenuUnfoldOutlined onClick={toggleCollapsed} />
                    </Typography.Title>
                </div>
                {/\/dashboard/.test(pathname) ? null : (
                    <>
                        {/* Additional icons or components can be added here */}
                    </>
                )}
            </div>
            <div         
                style={{
                    backgroundColor: "#1890ff",
                    position: "fixed",
                    bottom: "0",
                    width: "80px",
                    lineHeight: "40px",
                    paddingLeft: "20px",
                }}
            >
                <UserOutlined />
            </div>
        </>
    );
}

export default CollapsedSidebar;
