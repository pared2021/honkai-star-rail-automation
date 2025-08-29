import React, { useState } from 'react';
import { Modal, Button, Space, Typography, Alert, Spin } from 'antd';
import { PlayCircleOutlined, CloseOutlined, ExclamationCircleOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

interface GameStatusDialogProps {
  visible: boolean;
  onClose: () => void;
  onLaunch: () => Promise<void>;
  onCancel: () => void;
  title?: string;
  message?: string;
}

const GameStatusDialog: React.FC<GameStatusDialogProps> = ({
  visible,
  onClose,
  onLaunch,
  onCancel,
  title = '游戏未启动',
  message = '检测到游戏未启动，是否需要启动游戏后继续操作？'
}) => {
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLaunch = async () => {
    setLaunching(true);
    setError(null);
    
    try {
      await onLaunch();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动游戏失败');
    } finally {
      setLaunching(false);
    }
  };

  const handleCancel = () => {
    setError(null);
    onCancel();
    onClose();
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ExclamationCircleOutlined style={{ color: '#faad14' }} />
          <span>{title}</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={480}
      centered
    >
      <div style={{ padding: '16px 0' }}>
        <Alert
          message={message}
          type="warning"
          showIcon
          style={{ marginBottom: '16px' }}
        />
        
        {error && (
          <Alert
            message="启动失败"
            description={error}
            type="error"
            showIcon
            style={{ marginBottom: '16px' }}
          />
        )}
        
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Space size="large">
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              loading={launching}
              onClick={handleLaunch}
              size="large"
            >
              {launching ? '启动中...' : '启动游戏'}
            </Button>
            
            <Button
              icon={<CloseOutlined />}
              onClick={handleCancel}
              size="large"
              disabled={launching}
            >
              取消操作
            </Button>
          </Space>
        </div>
        
        <div style={{ marginTop: '16px', textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            提示：您也可以在游戏监控页面手动启动游戏
          </Text>
        </div>
      </div>
    </Modal>
  );
};

export default GameStatusDialog;