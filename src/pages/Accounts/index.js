import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// 账号管理页面
import { useState, useEffect } from 'react';
import { Card, Button, Table, Space, Modal, Form, Input, Switch, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
const Accounts = () => {
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalVisible, setModalVisible] = useState(false);
    const [editingAccount, setEditingAccount] = useState(null);
    const [form] = Form.useForm();
    // 获取账号列表
    const fetchAccounts = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:3001/api/accounts');
            const data = await response.json();
            if (data.success) {
                setAccounts(data.data);
            }
            else {
                message.error(data.error || '获取账号列表失败');
            }
        }
        catch (error) {
            message.error('获取账号列表失败');
            console.error('获取账号列表失败:', error);
        }
        finally {
            setLoading(false);
        }
    };
    // 创建或更新账号
    const handleSubmit = async (values) => {
        try {
            setLoading(true);
            let response;
            if (editingAccount) {
                // 更新账号
                response = { success: true }; // await window.electronAPI.account.update(editingAccount.id, values);
            }
            else {
                // 创建账号
                response = { success: true }; // await window.electronAPI.account.create(values);
            }
            if (response.success) {
                message.success(editingAccount ? '账号更新成功' : '账号创建成功');
                setModalVisible(false);
                setEditingAccount(null);
                form.resetFields();
                await fetchAccounts();
            }
            else {
                message.error(response.error || '操作失败');
            }
        }
        catch (error) {
            message.error('操作失败');
            console.error('账号操作失败:', error);
        }
        finally {
            setLoading(false);
        }
    };
    // 删除账号
    const handleDelete = async (id) => {
        try {
            const response = { success: true }; // await window.electronAPI.account.delete(id);
            if (response.success) {
                message.success('账号删除成功');
                await fetchAccounts();
            }
            else {
                message.error('删除失败');
            }
        }
        catch (error) {
            message.error('删除失败');
            console.error('删除账号失败:', error);
        }
    };
    // 编辑账号
    const handleEdit = (account) => {
        setEditingAccount(account);
        form.setFieldsValue({
            name: account.name,
            gameAccount: account.gameAccount,
            isActive: account.isActive
        });
        setModalVisible(true);
    };
    // 新建账号
    const handleCreate = () => {
        setEditingAccount(null);
        form.resetFields();
        setModalVisible(true);
    };
    // 取消操作
    const handleCancel = () => {
        setModalVisible(false);
        setEditingAccount(null);
        form.resetFields();
    };
    // 组件挂载时获取数据
    useEffect(() => {
        fetchAccounts();
    }, []);
    // 表格列定义
    const columns = [
        {
            title: '账号名称',
            dataIndex: 'name',
            key: 'name',
            render: (name, record) => (_jsxs(Space, { children: [_jsx(UserOutlined, {}), _jsx("span", { children: name }), record.isActive && _jsx(Tag, { color: "green", children: "\u6D3B\u8DC3" })] }))
        },
        {
            title: '游戏账号',
            dataIndex: 'gameAccount',
            key: 'gameAccount'
        },
        {
            title: '状态',
            dataIndex: 'isActive',
            key: 'isActive',
            render: (isActive) => (_jsx(Tag, { color: isActive ? 'green' : 'default', children: isActive ? '启用' : '禁用' }))
        },
        {
            title: '创建时间',
            dataIndex: 'createdAt',
            key: 'createdAt',
            render: (date) => new Date(date).toLocaleString()
        },
        {
            title: '最后登录',
            dataIndex: 'lastLoginAt',
            key: 'lastLoginAt',
            render: (date) => date ? new Date(date).toLocaleString() : '从未登录'
        },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (_jsxs(Space, { children: [_jsx(Button, { size: "small", icon: _jsx(EditOutlined, {}), onClick: () => handleEdit(record), children: "\u7F16\u8F91" }), _jsx(Popconfirm, { title: "\u786E\u5B9A\u8981\u5220\u9664\u8FD9\u4E2A\u8D26\u53F7\u5417\uFF1F", description: "\u5220\u9664\u540E\u5C06\u65E0\u6CD5\u6062\u590D\uFF0C\u76F8\u5173\u7684\u4EFB\u52A1\u8BB0\u5F55\u4E5F\u4F1A\u88AB\u6E05\u9664\u3002", onConfirm: () => handleDelete(record.id), okText: "\u786E\u5B9A", cancelText: "\u53D6\u6D88", children: _jsx(Button, { size: "small", icon: _jsx(DeleteOutlined, {}), danger: true, children: "\u5220\u9664" }) })] }))
        }
    ];
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, children: [_jsx("h1", { style: { margin: 0 }, children: "\u8D26\u53F7\u7BA1\u7406" }), _jsx(Button, { type: "primary", icon: _jsx(PlusOutlined, {}), onClick: handleCreate, children: "\u6DFB\u52A0\u8D26\u53F7" })] }), _jsx(Card, { children: _jsx(Table, { columns: columns, dataSource: accounts, rowKey: "id", loading: loading, pagination: {
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 个账号`
                    }, locale: { emptyText: '暂无账号数据' } }) }), _jsx(Modal, { title: editingAccount ? '编辑账号' : '添加账号', open: modalVisible, onOk: () => form.submit(), onCancel: handleCancel, confirmLoading: loading, width: 500, children: _jsxs(Form, { form: form, layout: "vertical", onFinish: handleSubmit, initialValues: {
                        isActive: true
                    }, children: [_jsx(Form.Item, { name: "name", label: "\u8D26\u53F7\u540D\u79F0", rules: [
                                { required: true, message: '请输入账号名称' },
                                { max: 50, message: '账号名称不能超过50个字符' }
                            ], children: _jsx(Input, { placeholder: "\u8BF7\u8F93\u5165\u8D26\u53F7\u540D\u79F0" }) }), _jsx(Form.Item, { name: "gameAccount", label: "\u6E38\u620F\u8D26\u53F7", rules: [
                                { required: true, message: '请输入游戏账号' },
                                { max: 100, message: '游戏账号不能超过100个字符' }
                            ], children: _jsx(Input, { placeholder: "\u8BF7\u8F93\u5165\u6E38\u620F\u8D26\u53F7\uFF08UID\u6216\u90AE\u7BB1\uFF09" }) }), _jsx(Form.Item, { name: "isActive", label: "\u542F\u7528\u72B6\u6001", valuePropName: "checked", children: _jsx(Switch, { checkedChildren: "\u542F\u7528", unCheckedChildren: "\u7981\u7528" }) })] }) })] }));
};
export default Accounts;
