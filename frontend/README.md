# Vue 3 算法管理系统前端

这是一个基于 Vue 3 + Element Plus + Axios 开发的算法评测管理系统前端。

## 📦 项目结构

```
src/
├── api/              # API 接口层
│   ├── request.js   # Axios 实例配置
│   └── contest.js   # 算法相关接口
├── views/           # 页面组件
│   ├── Home.vue              # 首页/仪表盘
│   ├── CreateContest.vue     # 创建算法
│   ├── ContestList.vue       # 算法列表
│   └── SubmitTask.vue        # 提交任务
├── router/
│   └── index.js     # Vue Router 配置
├── App.vue          # 根组件
├── main.js          # 应用入口
└── styles/          # 全局样式
```

## 🚀 快速开始

### 前置要求

- Node.js >= 14
- npm >= 6

### 安装依赖

```bash
npm install
```

### 开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:5173` 启动，并自动代理 API 请求到后端 `http://localhost:5000`

### 生产构建

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 📋 功能特性

### 首页 (Home)

- 系统功能卡片展示
- 后端连接状态检查
- 快捷导航

### 创建算法 (CreateContest)

- 算法标题和描述输入
- 参赛者镜像文件上传 (.tar, ≤500MB)
- 测试数据集上传 (.zip, ≤200MB)
- 评测数据集上传 (.zip, ≤200MB)
- 拖拽上传支持
- 实时文件验证
- 上传进度显示

### 算法列表 (ContestList)

- 算法卡片网格展示
- 搜索/过滤功能
- 分页显示
- 查看算法详情
- 快速提交任务

### 提交任务 (SubmitTask)

- 算法选择器（支持搜索）
- 参赛者镜像上传
- 实时上传进度
- 结果展示：
  - 参赛者镜像执行日志
  - 主办方镜像执行日志（如果启用）
  - 主办方 results.json 查看器
  - 任务状态指示

## 🔧 配置说明

### Vite 配置 (vite.config.js)

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

### Axios 配置 (src/api/request.js)

```javascript
const request = axios.create({
  baseURL: "http://localhost:5000",
  timeout: 30000,
});
```

**注意**: 任务提交接口超时设置为 600 秒（因为评测可能较耗时）

## 📡 API 接口

### 获取算法列表

```
GET /api/contests
返回: { code: 0, data: [...] }
```

### 创建算法

```
POST /create
Content-Type: multipart/form-data
参数:
  - title: 算法标题
  - description: 算法描述
  - image: 参赛者镜像 .tar 文件
  - source: 评测数据源 .zip 文件
  - result: 结果集 .zip 文件
返回: { code: 0, contest_id: "xxx" }
```

### 提交任务

```
POST /submit
Content-Type: multipart/form-data
参数:
  - contest_id: 算法 ID
  - file: 参赛者镜像 .tar 文件
返回: {
  code: 0|1|2|3,
  desc: "描述",
  participant_logs: "参赛者日志",
  participant_image: "镜像相对路径",
  organizer_logs: "主办方日志或 null",
  organizer_results: "results.json 内容或 null"
}
```

## 🔄 响应码说明

| 码  | 描述     | 说明                         |
| --- | -------- | ---------------------------- |
| 0   | 评测成功 | 参赛者和主办方镜像都成功执行 |
| 1   | 评测超时 | 容器执行超过 10 分钟限制     |
| 2   | 容器错误 | 镜像加载或启动失败           |
| 3   | 执行错误 | 容器执行过程中发生错误       |

## 🎨 界面特性

- ✨ 现代化的卡片设计
- 🎯 响应式布局（移动端、平板、桌面适配）
- 🔍 完整的搜索和过滤功能
- 📊 进度条和状态指示
- 💬 用户友好的消息提示
- 🎬 平滑的页面过渡

## 📝 开发说明

### 新增页面

1. 在 `src/views/` 创建 `.vue` 文件
2. 在 `src/router/index.js` 中注册路由
3. 在 `src/App.vue` 中添加菜单项（可选）

### 新增 API

1. 在 `src/api/contest.js` 中添加方法
2. 使用 `request` 实例发送请求

### 样式指南

- 使用 Element Plus 组件库的内置样式变量
- 在组件中使用 `scoped` 样式保证隔离
- 深度选择器使用 `:deep()` 修改子组件样式

## 🐛 常见问题

### 后端连接失败

- 确保 Flask 后端运行在 `http://localhost:5000`
- 检查防火墙是否阻止了 5000 端口

### 文件上传失败

- 检查文件大小是否超过限制（镜像 500MB, 数据集 200MB）
- 确保文件格式正确（镜像为 .tar, 数据集为 .zip）

### 跨域问题

- Vite 代理已配置，所有 `/api/*` 请求会自动转发到后端
- 开发时无需额外配置

## 📚 技术栈

- **Vue 3** - 前端框架
- **Vite** - 构建工具
- **Element Plus** - UI 组件库
- **Axios** - HTTP 客户端
- **Vue Router** - 路由管理

## 📄 许可证

MIT
