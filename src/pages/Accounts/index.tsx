// 账号管理页面
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Table, 
  Space, 
  Modal, 
  Form, 
  Input, 
  Switch,
  message,
  Popconfirm,
  Tag
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  UserOutlined
} from '@ant-design/icons';

interface Account {
  id: string;
  username: string;
  password: string;
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

interface AccountsProps {}

const Accounts: React.FC<AccountsProps> = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [form] = Form.useForm();

  // 获取账号列表
  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:3001/api/accounts');
      const data = await response.json();
      if (data.success) {
        setAccounts(data.data);
      } else {
        message.error(data.error || '获取账号列表失败');
      }
    } catch (error) {
      message.error('获取账号列表失败');
      console.error('获取账号列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 创建或更新账号
  const handleSubmit = async (values: any) => {
    try {
      setLoading(true);
      let response;
      
      if (editingAccount) {
        // 更新账号
        response = { success: true }; // await window.electronAPI.account.update(editingAccount.id, values);
      } else {
        // 创建账号
        response = { success: true }; // await window.electronAPI.account.create(values);
      }
      
      if (response.success) {
        message.success(editingAccount ? '账号更新成功' : '账号创建成功');
        setModalVisible(false);
        setEditingAccount(null);
        form.resetFields();
        await fetchAccounts();
      } else {
        message.error(response.error || '操作失败');
      }
    } catch (error) {
      message.error('操作失败');
      console.error('账号操作失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 删除账号
  const handleDelete = async (id: string) => {
    try {
      const response = { success: true }; // await window.electronAPI.account.delete(id);
      if (response.success) {
        message.success('账号删除成功');
        await fetchAccounts();
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      message.error('删除失败');
      console.error('删除账号失败:', error);
    }
  };

  // 编辑账号
  const handleEdit = (account: Account) => {
    setEditingAccount(account);
    form.setFieldsValue({
      name: (account as any).name,
      gameAccount: (account as any).gameAccount,
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
      render: (name: string, record: Account) => (
        <Space>
          <UserOutlined />
          <span>{name}</span>
          {record.isActive && <Tag color="green">活跃</Tag>}
        </Space>
      )
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
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: '最后登录',
      dataIndex: 'lastLoginAt',
      key: 'lastLoginAt',
      render: (date: string) => date ? new Date(date).toLocaleString() : '从未登录'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Account) => (
        <Space>
          <Button 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个账号吗？"
            description="删除后将无法恢复，相关的任务记录也会被清除。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              size="small" 
              icon={<DeleteOutlined />}
              danger
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>账号管理</h1>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          添加账号
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={accounts}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个账号`
          }}
          locale={{ emptyText: '暂无账号数据' }}
        />
      </Card>

      {/* 添加/编辑账号模态框 */}
      <Modal
        title={editingAccount ? '编辑账号' : '添加账号'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={handleCancel}
        confirmLoading={loading}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            isActive: true
          }}
        >
          <Form.Item
            name="name"
            label="账号名称"
            rules={[
              { required: true, message: '请输入账号名称' },
              { max: 50, message: '账号名称不能超过50个字符' }
            ]}
          >
            <Input placeholder="请输入账号名称" />
          </Form.Item>
          
          <Form.Item
            name="gameAccount"
            label="游戏账号"
            rules={[
              { required: true, message: '请输入游戏账号' },
              { max: 100, message: '游戏账号不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入游戏账号（UID或邮箱）" />
          </Form.Item>
          
          <Form.Item
            name="isActive"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Accounts;