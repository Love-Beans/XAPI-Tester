layui.use(['table', 'form', 'layer', 'element'], function(){
    var table = layui.table;
    var form = layui.form;
    var layer = layui.layer;
    var element = layui.element;
    const urlParams = new URLSearchParams(window.location.search);
    var currentProjectId = urlParams.get('project_id');;
    var currentRequestId = null;
    var requestName="";
    var requestList = [];
    
    // 初始化
    init();
    
    function init() {
        // 监听来自父页面的消息
        window.addEventListener('message', function(event) {
            if (event.data.type === 'loadRequestInfo') {
                // currentProjectId = event.data.projectId;
                currentRequestId = event.data.requestId;
                console.log('advanced info:currentProjectId:', currentProjectId,'currentRequestId:',currentRequestId);
                loadRequestList();
                loadProjectEnv();
                initTables();
                //loadGlobalTable();
                //loadCustomTable();
            }
        });
        
        // 初始化表格
        //initTables();
        
        // 绑定事件
        bindEvents();
    }
    
    // 初始化表格
    function initTables() {
        console.log(currentRequestId);
        // 全局配置表格
        table.render({
            elem: '#global-table',
            url: '/api/advanced-config/list',
            lineStyle: 'height: 100px;',
            where: {
                project_id: currentProjectId || 0,
                private_request_id: currentRequestId || 0,
                is_global: true
            },
            headers: getAuthHeaders(),
            initSort: {
                field: 'id',
                type: 'desc'
            },
            cols: [[
                {field: 'id', title: 'ID', width: 80, sort: true},
                {field: 'request_name', title: '接口名称', width: 200},
                {field: 'body_info',title: 'Body参数', minWidth:100, templet: function(d){
                    var bodyInfo = d.body_info;
                    if (typeof bodyInfo === 'object' && bodyInfo !== null) {
                        bodyInfo = JSON.stringify(bodyInfo, null, 2);
                    }
                    return '<div style="max-height:100px;overflow:auto;"><pre>' + (bodyInfo || '') + '</pre></div>';
                }},
                {field: 'query_info',title: 'Query参数', minWidth:100, templet: function(d){
                    var queryInfo = d.query_info;
                    if (typeof queryInfo === 'object' && queryInfo !== null) {
                        queryInfo = JSON.stringify(queryInfo, null, 2);
                    }
                    return '<div style="max-height:100px;overflow:auto;"><pre>' + (queryInfo || '') + '</pre></div>';
                }},
                {field: 'host', title: 'Host地址', width: 150},
                {field: 'created_at', title: '创建时间', minWidth:100},
                {title: '操作', minWidth:100, toolbar: '#globalBarDemo', fixed: 'right'}
            ]],
            page: true,
            limit: 10,
            limits: [10, 20, 50],
            loading: true,
            response: {
                statusName: 'code',
                statusCode: 200,
                msgName: 'message',
                countName: 'total',
                dataName: 'data'
            },
            parseData: function(res) {
                return {
                    code: res.error ? 500 : 200,
                    message: res.error || 'success',
                    total: res.total ? res.configs.length : 0,
                    data: res.configs || []
                };
            }
        });
        
        // 自定义配置表格
        table.render({
            elem: '#custom-table',
            url: '/api/advanced-config/list',
            lineStyle: 'height: 100px;',
            where: {
                project_id: currentProjectId || 0,
                private_request_id: currentRequestId || 0,
                is_global: false
            },
            headers: getAuthHeaders(),
            initSort: {
                field: 'id',
                type: 'desc'
            },
            cols: [[
                {field: 'id', title: 'ID', width: 80, sort: true},
                {field: 'request_name', title: '接口名称', width: 200},
                {field: 'body_info',title: 'Body参数', minWidth:100, templet: function(d){
                    var bodyInfo = d.body_info;
                    if (typeof bodyInfo === 'object' && bodyInfo !== null) {
                        bodyInfo = JSON.stringify(bodyInfo, null, 2);
                    }
                    return '<div style="max-height:100px;overflow:auto;"><pre>' + (bodyInfo || '') + '</pre></div>';
                }},
                {field: 'query_info',title: 'Query参数', minWidth:100, templet: function(d){
                    var queryInfo = d.query_info;
                    if (typeof queryInfo === 'object' && queryInfo !== null) {
                        queryInfo = JSON.stringify(queryInfo, null, 2);
                    }
                    return '<div style="max-height:100px;overflow:auto;"><pre>' + (queryInfo || '') + '</pre></div>';
                }},
                {field: 'host', title: 'Host地址', width: 150},
                {field: 'created_at', title: '创建时间', minWidth:100},
                {title: '操作', width: 100, toolbar: '#customBarDemo', fixed: 'right'}
            ]],
            page: true,
            limit: 10,
            limits: [10, 20, 50],
            loading: true,
            response: {
                statusName: 'code',
                statusCode: 200,
                msgName: 'message',
                countName: 'total',
                dataName: 'data'
            },
            parseData: function(res) {
                return {
                    code: res.error ? 500 : 200,
                    message: res.error || 'success',
                    total: res.total ? res.configs.length : 0,
                    data: res.configs || []
                };
            }
        });
    }
    
    // 加载项目环境配置
    function loadProjectEnv() {
        if (!currentProjectId) {
            return;
        }
        
        fetch('/api/project_env/' + currentProjectId, {
            headers: getAuthHeaders()
        })
        .then(response => response.json())
        .then(result => {
            $("#hostSelect").html(''); 
            $('#hostSelect').append($('<option>',{value: 'custom', text: '自定义'}));
            if (result.success && result.data && result.data.env && result.data.env.host) {
                // 动态添加选项到 hostSelect
                var hosts = result.data.env.host;
                Object.keys(hosts).forEach(function(key) {
                    var hostValue = hosts[key].trim();
                    $('#hostSelect').append($('<option>', { 
                        value: hostValue,
                        text : key + ' (' + hostValue + ')'
                    }));
                });
            }
            form.render('select');
        })
        .catch(error => {
            console.error('加载项目环境配置失败:', error);
        });
    }
    
    // 绑定事件
    function bindEvents() {
        // 添加配置按钮
        document.getElementById('addConfigBtn').addEventListener('click', function() {
            showAddConfigForm();
        });
        
        // 表单提交
        form.on('submit(submitConfig)', function(data) {
            saveConfig(data.field);
            return false;
        });
        
        // 全局配置表格工具栏事件
        table.on('tool(global-table)', function(obj) {
            var data = obj.data;
            if (obj.event === 'edit') {
                editConfig(data);
            } else if (obj.event === 'del') {
                deleteConfig(data.id, 'global');
            }
        });
        
        // 自定义配置表格工具栏事件
        table.on('tool(custom-table)', function(obj) {
            var data = obj.data;
            if (obj.event === 'edit') {
                editConfig(data);
            } else if (obj.event === 'del') {
                deleteConfig(data.id, 'custom');
            }
        });
        
        // Host选择器事件
        form.on('select(hostSelect)', function(data) {
            var customHostItem = document.getElementById('customHostItem');
            if (data.value === 'custom') {
                customHostItem.style.display = 'block';
            } else {
                customHostItem.style.display = 'none';
            }
        });
    }
    
    // 获取认证头信息
    function getAuthHeaders() {
        
        return parent.get_x_token();
    }
    
    // 加载请求列表
    function loadRequestList() {
        if (!currentProjectId) return;
        
        fetch('/api/projects/' + currentProjectId + '/requests', {
            headers: getAuthHeaders()
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                showMessage('加载请求列表失败: ' + result.error, 'error');
                return;
            }
            requestList = result.data || [];
            updateRequestSelect();
        })
        .catch(error => {
            console.error('加载请求列表失败:', error);
            showMessage('加载请求列表失败', 'error');
        });
    }
    
    // 更新请求选择框
    function updateRequestSelect() {
        $("#requestId").html(''); 
        // 动态添加选项到 select
        requestList.forEach(function(option) {
            $('#requestId').append($('<option>', { 
                value: option.id,
                text : option.request_name 
            }));
        });
        form.render('select');
    }
    form.on('select(requestId)', function(data){
        requestName=  data.elem.options[data.elem.selectedIndex].text;
        console.log('选中的值是: ' + data.value+requestName); // data.value 即为选中值    
    });
    // 显示添加配置表单
    function showAddConfigForm() {
        if (!currentProjectId) {
            showMessage('请先选择项目', 'warning');
            return;
        }
        layer.open({
            type: 1,
            title: '添加配置',
            content: $('#addConfigForm'),
            area: ['600px', '500px'],
            btn: false,
            success: function() {
                form.render();
            },
            end: function(){
                $('#addConfigForm').css('display', 'none');
                console.log('弹层已被移除');
            }
        });
    }
    
    // 保存配置
    function saveConfig(formData) {
        if (!currentProjectId) {
            showMessage('项目ID不能为空', 'error');
            return;
        }
        
        // 验证JSON格式
        if (formData.bodyInfo && !isValidJSON(formData.bodyInfo)) {
            showMessage('Body参数不是有效的JSON格式', 'error');
            return;
        }
        
        if (formData.queryInfo && !isValidJSON(formData.queryInfo)) {
            showMessage('Query参数不是有效的JSON格式', 'error');
            return;
        }
        var $requestIdSelect = $('#requestId');
        var selectedText = $requestIdSelect.find('option:selected').text();
        console.log('requestName', requestName,"selectedText",selectedText);
        
        // 处理host字段
        var hostValue = formData.host;
        if (hostValue === 'custom') {
            hostValue = formData.customHost || '';
        }
        
        var data = {
            project_id: currentProjectId,
            request_info_id: formData.requestId,
            is_global: formData.configType === 'global',
            body_info: formData.bodyInfo || '',
            query_info: formData.queryInfo || '',
            request_name: requestName || selectedText,
            private_request_id: currentRequestId,
            host: hostValue
        };
        
        var method = formData.id ? 'PUT' : 'POST';
        var url = formData.id ? '/api/advanced-config/' + formData.id : '/api/advanced-config';
        
        fetch(url, {
            method: method,
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                showMessage(result.error, 'error');
            } else {
                showMessage('配置保存成功', 'success');
                layer.closeAll();
                loadGlobalTable();
                loadCustomTable();
            }
            $('#addConfigForm').css('display', 'none');
        })
        .catch(error => {
            console.error('保存配置失败:', error);
            showMessage('保存失败，请重试', 'error');
        });
    }
    
    // 编辑配置
    function editConfig(data) {
        if (!currentProjectId) {
            showMessage('请先选择项目', 'warning');
            return;
        }
        requestName=""
        layer.open({
            type: 1,
            title: '编辑配置',
            content: $('#addConfigForm'),
            area: ['600px', '500px'],
            btn: false,
            success: function(layero, index) {
                $('#hiddenInputContainer', layero).html('<input type="hidden" name="id" value="'+data.id+'">');
                form.val('configForm', {
                    "bodyInfo": data.body_info || {}, // text 赋值
                    "configType": data.is_global ? 'global' : 'custom', // radio 赋值（选中 value="2"）
                    "queryInfo": data.query_info || {}, // select 赋值（选中 value="3"）
                    "requestId": data.request_info_id // textarea 赋值
                });
                form.render();
            },
            end: function () { 
                $('#addConfigForm').css('display', 'none');
            }
        });
    }
    
    // 删除配置
    function deleteConfig(configId, tableType) {
        layer.confirm('确定要删除这个配置吗？', function(index) {
            fetch('/api/advanced-config/' + configId, {
                method: 'DELETE',
                headers: getAuthHeaders(),
                data: JSON.stringify({
                    project_id: currentProjectId
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.error) {
                    showMessage(result.error, 'error');
                } else {
                    showMessage('配置删除成功', 'success');
                    if (tableType === 'global') {
                        loadGlobalTable();
                    } else {
                        loadCustomTable();
                    }
                }
            })
            .catch(error => {
                console.error('删除配置失败:', error);
                showMessage('删除失败，请重试', 'error');
            });
            
            layer.close(index);
        });
    }
    
    // 重新加载全局配置表格
    function loadGlobalTable() {
        if (!currentProjectId) return;
        
        table.reload('global-table', {
            where: {
                project_id: currentProjectId,
                private_request_id: currentRequestId || 0,
                is_global: true
            },
            headers: getAuthHeaders()
        });
    }
    
    // 重新加载自定义配置表格
    function loadCustomTable() {
        if (!currentProjectId) return;
        
        table.reload('custom-table', {
            where: {
                project_id: currentProjectId,
                private_request_id: currentRequestId || 0,
                is_global: false
            },
            headers: getAuthHeaders()
        });
    }
    
    // 验证JSON格式
    function isValidJSON(str) {
        try {
            JSON.parse(str);
            return true;
        } catch (e) {
            return false;
        }
    }
    
    // 显示消息
    function showMessage(message, type) {
        type = type || 'success';
        
        var messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + type;
        messageDiv.textContent = message;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(function() {
            messageDiv.classList.add('show');
        }, 100);
        
        setTimeout(function() {
            messageDiv.classList.remove('show');
            setTimeout(function() {
                document.body.removeChild(messageDiv);
            }, 300);
        }, 3000);
    }
});

// 添加表格操作按钮模板
document.addEventListener('DOMContentLoaded', function() {
    // 全局配置操作按钮
    var globalBarScript = document.createElement('script');
    globalBarScript.type = 'text/html';
    globalBarScript.id = 'globalBarDemo';
    globalBarScript.innerHTML = '<a class="layui-btn layui-btn-xs" lay-event="edit">编辑</a><a class="layui-btn layui-btn-danger layui-btn-xs" lay-event="del">删除</a>';
    document.head.appendChild(globalBarScript);
    
    // 自定义配置操作按钮
    var customBarScript = document.createElement('script');
    customBarScript.type = 'text/html';
    customBarScript.id = 'customBarDemo';
    customBarScript.innerHTML = '<a class="layui-btn layui-btn-xs" lay-event="edit">编辑</a><a class="layui-btn layui-btn-danger layui-btn-xs" lay-event="del">删除</a>';
    document.head.appendChild(customBarScript);
});