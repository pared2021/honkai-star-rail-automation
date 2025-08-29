import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// 设置页面
import { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Switch, Button, Select, Space, message, Row, Col, Tabs } from 'antd';
import { SaveOutlined, ReloadOutlined, SettingOutlined, SafetyOutlined, BellOutlined, MonitorOutlined, FolderOpenOutlined } from '@ant-design/icons';
const { TabPane } = Tabs;
const { Option } = Select;
const Settings = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    // 从localStorage加载设置
    const loadSettingsFromStorage = () => {
        try {
            const savedSettings = localStorage.getItem('app_settings');
            if (savedSettings) {
                return JSON.parse(savedSettings);
            }
        }
        catch (error) {
            console.error('加载设置失败:', error);
        }
        // 返回默认设置
        return {
            gameSettings: {
                detectionInterval: 1000,
                autoStart: false,
                gameWindowTitle: '崩坏：星穹铁道',
                screenshotQuality: 80
            },
            gameMonitorSettings: {
                gamePath: '',
                autoLaunchGame: false,
                launchDelay: 5000,
                enableGameMonitoring: true,
                monitorInterval: 5000,
                enableFilterDetection: true,
                filterCheckInterval: 30000,
                enableInjectionDetection: true,
                enableDriverFilterDetection: true,
                autoTerminateOnExit: false
            },
            taskSettings: {
                maxConcurrentTasks: 3,
                taskTimeout: 300000,
                retryAttempts: 3,
                autoRetry: true
            },
            securitySettings: {
                enableSafeMode: true,
                randomDelay: true,
                minDelay: 500,
                maxDelay: 2000,
                enableAntiDetection: true
            },
            notificationSettings: {
                enableNotifications: true,
                notifyOnTaskComplete: true,
                notifyOnTaskFailed: true,
                notifyOnGameClosed: true,
                soundEnabled: true
            }
        };
    };
    const [settings, setSettings] = useState(loadSettingsFromStorage());
    // 加载设置
    const loadSettings = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/settings');
            const data = await response.json();
            if (data.success) {
                setSettings(data.data);
                form.setFieldsValue(data.data);
            }
            else {
                form.setFieldsValue(settings);
            }
        }
        catch (error) {
            console.error('加载设置失败:', error);
            message.error('加载设置失败');
            form.setFieldsValue(settings);
        }
    };
    // 保存设置
    const saveSettings = async (values) => {
        try {
            setLoading(true);
            // 保存设置到localStorage
            localStorage.setItem('app_settings', JSON.stringify(values));
            // 更新状态
            setSettings(values);
            message.success('设置保存成功');
        }
        catch (error) {
            console.error('保存设置失败:', error);
            message.error('保存设置失败');
        }
        finally {
            setLoading(false);
        }
    };
    // 重置设置
    const resetSettings = () => {
        form.setFieldsValue(settings);
        message.info('设置已重置');
    };
    // 恢复默认设置
    const restoreDefaults = () => {
        const defaultSettings = {
            gameSettings: {
                detectionInterval: 1000,
                autoStart: false,
                gameWindowTitle: '崩坏：星穹铁道',
                screenshotQuality: 80
            },
            gameMonitorSettings: {
                gamePath: '',
                autoLaunchGame: false,
                launchDelay: 5000,
                enableGameMonitoring: true,
                monitorInterval: 5000,
                enableFilterDetection: true,
                filterCheckInterval: 30000,
                enableInjectionDetection: true,
                enableDriverFilterDetection: true,
                autoTerminateOnExit: false
            },
            taskSettings: {
                maxConcurrentTasks: 3,
                taskTimeout: 300000,
                retryAttempts: 3,
                autoRetry: true
            },
            securitySettings: {
                enableSafeMode: true,
                randomDelay: true,
                minDelay: 500,
                maxDelay: 2000,
                enableAntiDetection: true
            },
            notificationSettings: {
                enableNotifications: true,
                notifyOnTaskComplete: true,
                notifyOnTaskFailed: true,
                notifyOnGameClosed: true,
                soundEnabled: true
            }
        };
        form.setFieldsValue(defaultSettings);
        message.info('已恢复默认设置');
    };
    // 组件挂载时加载设置
    useEffect(() => {
        loadSettings();
    }, []);
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, children: [_jsx("h1", { style: { margin: 0 }, children: "\u8BBE\u7F6E" }), _jsxs(Space, { children: [_jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: resetSettings, children: "\u91CD\u7F6E" }), _jsx(Button, { onClick: restoreDefaults, children: "\u6062\u590D\u9ED8\u8BA4" }), _jsx(Button, { type: "primary", icon: _jsx(SaveOutlined, {}), loading: loading, onClick: () => form.submit(), children: "\u4FDD\u5B58\u8BBE\u7F6E" })] })] }), _jsx(Form, { form: form, layout: "vertical", onFinish: saveSettings, initialValues: settings, children: _jsxs(Tabs, { defaultActiveKey: "game", children: [_jsx(TabPane, { tab: _jsxs("span", { children: [_jsx(SettingOutlined, {}), "\u6E38\u620F\u8BBE\u7F6E"] }), children: _jsx(Card, { children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameSettings', 'detectionInterval'], label: "\u6E38\u620F\u68C0\u6D4B\u95F4\u9694\uFF08\u6BEB\u79D2\uFF09", tooltip: "\u68C0\u6D4B\u6E38\u620F\u72B6\u6001\u7684\u65F6\u95F4\u95F4\u9694\uFF0C\u503C\u8D8A\u5C0F\u68C0\u6D4B\u8D8A\u9891\u7E41\u4F46\u6D88\u8017\u66F4\u591A\u8D44\u6E90", children: _jsx(InputNumber, { min: 500, max: 5000, step: 100, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameSettings', 'screenshotQuality'], label: "\u622A\u56FE\u8D28\u91CF\uFF08%\uFF09", tooltip: "\u622A\u56FE\u7684\u538B\u7F29\u8D28\u91CF\uFF0C\u5F71\u54CD\u56FE\u50CF\u8BC6\u522B\u7CBE\u5EA6\u548C\u6587\u4EF6\u5927\u5C0F", children: _jsx(InputNumber, { min: 10, max: 100, step: 10, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameSettings', 'gameWindowTitle'], label: "\u6E38\u620F\u7A97\u53E3\u6807\u9898", tooltip: "\u7528\u4E8E\u8BC6\u522B\u6E38\u620F\u7A97\u53E3\u7684\u6807\u9898\u5173\u952E\u8BCD", children: _jsx(Input, { placeholder: "\u5D29\u574F\uFF1A\u661F\u7A79\u94C1\u9053" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameSettings', 'autoStart'], label: "\u81EA\u52A8\u542F\u52A8\u68C0\u6D4B", valuePropName: "checked", tooltip: "\u7A0B\u5E8F\u542F\u52A8\u65F6\u81EA\u52A8\u5F00\u59CB\u6E38\u620F\u68C0\u6D4B", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) })] }) }) }, "game"), _jsx(TabPane, { tab: _jsxs("span", { children: [_jsx(MonitorOutlined, {}), "\u6E38\u620F\u76D1\u63A7"] }), children: _jsxs("div", { children: [_jsx(Card, { title: "\u6E38\u620F\u542F\u52A8\u8BBE\u7F6E", style: { marginBottom: '16px' }, children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 24, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'gamePath'], label: "\u6E38\u620F\u5B89\u88C5\u8DEF\u5F84", tooltip: "\u6E38\u620F\u53EF\u6267\u884C\u6587\u4EF6\u7684\u5B8C\u6574\u8DEF\u5F84", children: _jsxs(Input.Group, { compact: true, children: [_jsx(Input, { style: { width: 'calc(100% - 40px)' }, placeholder: "\u8BF7\u9009\u62E9\u6E38\u620F\u53EF\u6267\u884C\u6587\u4EF6\u8DEF\u5F84" }), _jsx(Button, { icon: _jsx(FolderOpenOutlined, {}), onClick: () => {
                                                                        message.info('文件选择功能开发中...');
                                                                    } })] }) }) }), _jsx(Col, { span: 24, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'autoLaunchGame'], label: "\u81EA\u52A8\u542F\u52A8\u6E38\u620F", valuePropName: "checked", tooltip: "\u5F00\u542F\u540E\uFF0C\u7A0B\u5E8F\u542F\u52A8\u65F6\u4F1A\u81EA\u52A8\u68C0\u6D4B\u5E76\u542F\u52A8\u6E38\u620F\u3002\u5982\u679C\u5173\u95ED\uFF0C\u53EA\u6709\u5728\u6267\u884C\u4EFB\u52A1\u6216\u81EA\u52A8\u5316\u65F6\u624D\u4F1A\u63D0\u793A\u542F\u52A8\u6E38\u620F\u3002", extra: _jsxs("div", { style: { color: '#666', fontSize: '12px', marginTop: '4px' }, children: [_jsx("div", { children: "\u2022 \u5F00\u542F\uFF1A\u7A0B\u5E8F\u542F\u52A8\u65F6\u81EA\u52A8\u542F\u52A8\u6E38\u620F" }), _jsx("div", { children: "\u2022 \u5173\u95ED\uFF1A\u4EC5\u5728\u9700\u8981\u65F6\u63D0\u793A\u542F\u52A8\u6E38\u620F\uFF08\u534A\u81EA\u52A8\u6A21\u5F0F\uFF09" }), _jsx("div", { style: { color: '#ff7875' }, children: "\u6CE8\u610F\uFF1A\u9700\u8981\u5148\u8BBE\u7F6E\u6B63\u786E\u7684\u6E38\u620F\u8DEF\u5F84" })] }), children: _jsx(Switch, { checkedChildren: "\u81EA\u52A8\u542F\u52A8", unCheckedChildren: "\u534A\u81EA\u52A8\u6A21\u5F0F", style: { minWidth: '100px' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'launchDelay'], label: "\u542F\u52A8\u5EF6\u8FDF\uFF08\u6BEB\u79D2\uFF09", tooltip: "\u542F\u52A8\u6E38\u620F\u524D\u7684\u7B49\u5F85\u65F6\u95F4\uFF0C\u5EFA\u8BAE\u8BBE\u7F6E3-10\u79D2", children: _jsx(InputNumber, { min: 0, max: 30000, step: 1000, style: { width: '100%' }, placeholder: "5000" }) }) }), _jsx(Col, { span: 24, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'autoTerminateOnExit'], label: "\u7A0B\u5E8F\u9000\u51FA\u65F6\u5173\u95ED\u6E38\u620F", valuePropName: "checked", tooltip: "\u7A0B\u5E8F\u9000\u51FA\u65F6\u81EA\u52A8\u5173\u95ED\u6E38\u620F\u8FDB\u7A0B", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) })] }) }), _jsx(Card, { title: "\u6E38\u620F\u76D1\u63A7\u8BBE\u7F6E", style: { marginBottom: '16px' }, children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'enableGameMonitoring'], label: "\u542F\u7528\u6E38\u620F\u72B6\u6001\u76D1\u63A7", valuePropName: "checked", tooltip: "\u76D1\u63A7\u6E38\u620F\u8FD0\u884C\u72B6\u6001", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'monitorInterval'], label: "\u76D1\u63A7\u95F4\u9694\uFF08\u6BEB\u79D2\uFF09", tooltip: "\u6E38\u620F\u72B6\u6001\u76D1\u63A7\u7684\u65F6\u95F4\u95F4\u9694", children: _jsx(InputNumber, { min: 1000, max: 60000, step: 1000, style: { width: '100%' } }) }) })] }) }), _jsx(Card, { title: "\u6EE4\u955C\u68C0\u6D4B\u8BBE\u7F6E", children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'enableFilterDetection'], label: "\u542F\u7528\u6EE4\u955C\u68C0\u6D4B", valuePropName: "checked", tooltip: "\u68C0\u6D4B\u6E38\u620F\u4E2D\u7684\u6EE4\u955C\u7A0B\u5E8F", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'filterCheckInterval'], label: "\u68C0\u6D4B\u95F4\u9694\uFF08\u6BEB\u79D2\uFF09", tooltip: "\u6EE4\u955C\u68C0\u6D4B\u7684\u65F6\u95F4\u95F4\u9694", children: _jsx(InputNumber, { min: 10000, max: 300000, step: 10000, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'enableInjectionDetection'], label: "\u68C0\u6D4B\u8FDB\u7A0B\u6CE8\u5165", valuePropName: "checked", tooltip: "\u68C0\u6D4B\u662F\u5426\u6709\u7A0B\u5E8F\u6CE8\u5165\u5230\u6E38\u620F\u8FDB\u7A0B", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['gameMonitorSettings', 'enableDriverFilterDetection'], label: "\u68C0\u6D4B\u9A71\u52A8\u7EA7\u6EE4\u955C", valuePropName: "checked", tooltip: "\u68C0\u6D4B\u9A71\u52A8\u7EA7\u522B\u7684\u6EE4\u955C\u7A0B\u5E8F", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) })] }) })] }) }, "gameMonitor"), _jsx(TabPane, { tab: _jsxs("span", { children: [_jsx(SettingOutlined, {}), "\u4EFB\u52A1\u8BBE\u7F6E"] }), children: _jsx(Card, { children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['taskSettings', 'maxConcurrentTasks'], label: "\u6700\u5927\u5E76\u53D1\u4EFB\u52A1\u6570", tooltip: "\u540C\u65F6\u8FD0\u884C\u7684\u6700\u5927\u4EFB\u52A1\u6570\u91CF", children: _jsx(InputNumber, { min: 1, max: 10, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['taskSettings', 'taskTimeout'], label: "\u4EFB\u52A1\u8D85\u65F6\u65F6\u95F4\uFF08\u6BEB\u79D2\uFF09", tooltip: "\u5355\u4E2A\u4EFB\u52A1\u7684\u6700\u5927\u6267\u884C\u65F6\u95F4", children: _jsx(InputNumber, { min: 60000, max: 3600000, step: 60000, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['taskSettings', 'retryAttempts'], label: "\u91CD\u8BD5\u6B21\u6570", tooltip: "\u4EFB\u52A1\u5931\u8D25\u65F6\u7684\u91CD\u8BD5\u6B21\u6570", children: _jsx(InputNumber, { min: 0, max: 10, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['taskSettings', 'autoRetry'], label: "\u81EA\u52A8\u91CD\u8BD5", valuePropName: "checked", tooltip: "\u4EFB\u52A1\u5931\u8D25\u65F6\u81EA\u52A8\u91CD\u8BD5", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) })] }) }) }, "task"), _jsx(TabPane, { tab: _jsxs("span", { children: [_jsx(SafetyOutlined, {}), "\u5B89\u5168\u8BBE\u7F6E"] }), children: _jsx(Card, { children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['securitySettings', 'enableSafeMode'], label: "\u542F\u7528\u5B89\u5168\u6A21\u5F0F", valuePropName: "checked", tooltip: "\u542F\u7528\u5B89\u5168\u6A21\u5F0F\u4EE5\u964D\u4F4E\u88AB\u68C0\u6D4B\u7684\u98CE\u9669", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['securitySettings', 'enableAntiDetection'], label: "\u542F\u7528\u53CD\u68C0\u6D4B", valuePropName: "checked", tooltip: "\u542F\u7528\u53CD\u68C0\u6D4B\u673A\u5236", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['securitySettings', 'randomDelay'], label: "\u968F\u673A\u5EF6\u8FDF", valuePropName: "checked", tooltip: "\u5728\u64CD\u4F5C\u95F4\u6DFB\u52A0\u968F\u673A\u5EF6\u8FDF", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['securitySettings', 'minDelay'], label: "\u6700\u5C0F\u5EF6\u8FDF\uFF08\u6BEB\u79D2\uFF09", tooltip: "\u968F\u673A\u5EF6\u8FDF\u7684\u6700\u5C0F\u503C", children: _jsx(InputNumber, { min: 100, max: 5000, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['securitySettings', 'maxDelay'], label: "\u6700\u5927\u5EF6\u8FDF\uFF08\u6BEB\u79D2\uFF09", tooltip: "\u968F\u673A\u5EF6\u8FDF\u7684\u6700\u5927\u503C", children: _jsx(InputNumber, { min: 500, max: 10000, style: { width: '100%' } }) }) })] }) }) }, "security"), _jsx(TabPane, { tab: _jsxs("span", { children: [_jsx(BellOutlined, {}), "\u901A\u77E5\u8BBE\u7F6E"] }), children: _jsx(Card, { children: _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['notificationSettings', 'enableNotifications'], label: "\u542F\u7528\u901A\u77E5", valuePropName: "checked", tooltip: "\u542F\u7528\u7CFB\u7EDF\u901A\u77E5", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['notificationSettings', 'soundEnabled'], label: "\u58F0\u97F3\u63D0\u9192", valuePropName: "checked", tooltip: "\u542F\u7528\u58F0\u97F3\u63D0\u9192", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['notificationSettings', 'notifyOnTaskComplete'], label: "\u4EFB\u52A1\u5B8C\u6210\u901A\u77E5", valuePropName: "checked", tooltip: "\u4EFB\u52A1\u5B8C\u6210\u65F6\u53D1\u9001\u901A\u77E5", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['notificationSettings', 'notifyOnTaskFailed'], label: "\u4EFB\u52A1\u5931\u8D25\u901A\u77E5", valuePropName: "checked", tooltip: "\u4EFB\u52A1\u5931\u8D25\u65F6\u53D1\u9001\u901A\u77E5", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: ['notificationSettings', 'notifyOnGameClosed'], label: "\u6E38\u620F\u5173\u95ED\u901A\u77E5", valuePropName: "checked", tooltip: "\u68C0\u6D4B\u5230\u6E38\u620F\u5173\u95ED\u65F6\u53D1\u9001\u901A\u77E5", children: _jsx(Switch, { checkedChildren: "\u5F00\u542F", unCheckedChildren: "\u5173\u95ED" }) }) })] }) }) }, "notification")] }) })] }));
};
export default Settings;
