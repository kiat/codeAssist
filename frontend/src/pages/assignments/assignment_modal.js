import React, { useState } from 'react';
import { message, Modal, Upload } from "antd";
import { LoadingOutlined, PlusOutlined } from '@ant-design/icons';

export default function AssignmentModal({ open, onCancel, submit }) {

    const [loading, setLoading] = useState(false);

    // TODO: ALTER THIS FOR ALL RELEVANT FILE RESTRICTIONS.
    const beforeUpload = (file) => {
        const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
        if (!isJpgOrPng) {
          message.error('You can only upload JPG/PNG file!');
        }
        const isLt2M = file.size / 1024 / 1024 < 2;
        if (!isLt2M) {
          message.error('Image must smaller than 2MB!');
        }
        return isJpgOrPng && isLt2M;
      };

    const uploadButton = (
        <div>
          {loading ? <LoadingOutlined /> : <PlusOutlined />}
          <div style={{ marginTop: 8 }}>Upload</div>
        </div>
      );

    return (
        <Modal title="Submit Assignment" open={open} onCancel={onCancel}>
            <Upload name="submission" listType="picture-card" className="submission-uploader" showUploadList={false} >
                {/* YOU MUST SET UPLOAD ACTION HERE IN UPLOAD. THIS MUST CONNECT TO THE DATABASE*/}
                {uploadButton}
            </Upload>
        </Modal>
    );
}