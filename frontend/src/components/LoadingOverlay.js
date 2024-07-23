import React from 'react';
import { Spin } from 'antd';
import './LoadingOverlay.css'; // Add your CSS styles here

const LoadingOverlay = ({ loading }) => {
  return (
    loading ? (
      <div className="loading-overlay">
        <Spin size="large" />
      </div>
    ) : null
  );
};

export default LoadingOverlay;
