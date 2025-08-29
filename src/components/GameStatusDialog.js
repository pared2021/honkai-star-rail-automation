import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Modal, Button, Space, Typography, Alert } from 'antd';
import { PlayCircleOutlined, CloseOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
const { Text, Title } = Typography;
const GameStatusDialog = ({ visible, onClose, onLaunch, onCancel, title = '游戏未启动', message = '检测到游戏未启动，是否需要启动游戏后继续操作？' }) => {
    const [launching, setLaunching] = useState(false);
    const [error, setError] = useState(null);
    const handleLaunch = async () => {
        setLaunching(true);
        setError(null);
        try {
            await onLaunch();
            onClose();
        }
        catch (err) {
            setError(err instanceof Error ? err.message : '启动游戏失败');
        }
        finally {
            setLaunching(false);
        }
    };
    const handleCancel = () => {
        setError(null);
        onCancel();
        onClose();
    };
    return (_jsx(Modal, { title: _jsxs("div", { style: { display: 'flex', alignItems: 'center', gap: '8px' }, children: [_jsx(ExclamationCircleOutlined, { style: { color: '#faad14' } }), _jsx("span", { children: title })] }), open: visible, onCancel: onClose, footer: null, width: 480, centered: true, children: _jsxs("div", { style: { padding: '16px 0' }, children: [_jsx(Alert, { message: message, type: "warning", showIcon: true, style: { marginBottom: '16px' } }), error && (_jsx(Alert, { message: "\u542F\u52A8\u5931\u8D25", description: error, type: "error", showIcon: true, style: { marginBottom: '16px' } })), _jsx("div", { style: { textAlign: 'center', marginTop: '24px' }, children: _jsxs(Space, { size: "large", children: [_jsx(Button, { type: "primary", icon: _jsx(PlayCircleOutlined, {}), loading: launching, onClick: handleLaunch, size: "large", children: launching ? '启动中...' : '启动游戏' }), _jsx(Button, { icon: _jsx(CloseOutlined, {}), onClick: handleCancel, size: "large", disabled: launching, children: "\u53D6\u6D88\u64CD\u4F5C" })] }) }), _jsx("div", { style: { marginTop: '16px', textAlign: 'center' }, children: _jsx(Text, { type: "secondary", style: { fontSize: '12px' }, children: "\u63D0\u793A\uFF1A\u60A8\u4E5F\u53EF\u4EE5\u5728\u6E38\u620F\u76D1\u63A7\u9875\u9762\u624B\u52A8\u542F\u52A8\u6E38\u620F" }) })] }) }));
};
export default GameStatusDialog;
