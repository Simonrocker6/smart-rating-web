# Smart Rating AI

一个端到端的智能阅卷系统（前后端分离）：
- 前端：React + TypeScript + MUI（浅色 Material 风格）
- 后端：FastAPI + SQLAlchemy，支持 AWS Secrets Manager（Postgres 凭证）与 S3 预签名上传

## 目录结构
- `frontend/` 前端工程（Vite）
- `backend/app/` 后端应用（FastAPI）
- `product_doc.md` 产品与架构需求参考

## 先决条件
- Node.js 18+
- Python 3.11+
- AWS 账号（Secrets Manager、S3、RDS Postgres）

## 后端开发
1) 安装依赖并启动
```
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary boto3
uvicorn backend.app.main:app --reload --port 8000
```

2) 环境变量（按需设置）
- `ENV=development|test|production`
- `AWS_REGION=ap-southeast-1`
- `DB_SECRET_ARN=arn:aws:secretsmanager:...:secret:db-prod-credential-...`（优先）
- 或 `DATABASE_URL_DEV/TEST/PROD=postgresql+psycopg2://user:pass@host:port/dbname`
- `S3_BUCKET_UPLOADS_DEV/TEST/PROD` 或 `S3_BUCKET_UPLOADS`
- `S3_PRESIGN_EXPIRE`（可选，默认 3600 秒）

3) Secrets Manager 凭证 JSON 示例
```
{
  "username": "app_user",
  "password": "******",
  "host": "db-xxxx.rds.amazonaws.com",
  "port": 5432,
  "dbname": "smart_rating"
}
```
后端会自动从 Secrets 拉取并强制 `sslmode=require`。

4) 主要接口
- 考试：`GET /exams/`、`GET /exams/{exam_id}`、`POST /exams/`、`PUT /exams/{exam_id}`
- 助教：`GET /tas/`、`GET /tas/{ta_id}`、`POST /tas/`、`PUT /tas/{ta_id}`
- 预签名上传：`POST /files/presign`
- 试卷：`GET /papers?exam_id=...`、`POST /papers/`

## 前端开发
1) 安装与启动
```
cd frontend
npm install
npm run dev
```
本地预览：`http://localhost:5173/`

2) 功能入口
- 考试配置/查看：编辑题目、满分、标准答案与评分模板
- 上传试卷：选择考试与 TA，上传 PDF（走 S3 预签名直传），创建 `Paper`
- 批阅：按考试筛选，题目与试卷导航，得分与评语
- 成绩分析：按考试筛选，图表与导出
- 助教管理：新增与查看 TA 列表

3) 质量检查
```
cd frontend
npm run typecheck
npm run lint
```

## 环境与安全最佳实践
- 分环境隔离：`dev/staging/prod` 独立资源（账号/VPC/安全组）
- 数据库账号最小权限；生产开启快照与 PITR；仅私网访问
- 凭证托管 Secrets Manager（或 RDS IAM Auth），禁用明文密码入库
- S3 按环境独立 bucket，严格 bucket policy 与生命周期策略
- IaC（Terraform/CDK）与 CI/CD（分支/标签）管理发布与回滚

## 部署建议
- 前端：构建静态资源（`npm run build`），推荐托管到 S3 + CloudFront
- 后端：容器化部署至 ECS/EKS，ALB 暴露 HTTP API，结合 Secrets 与 IAM Role

## 备注
- 本仓库默认本地开发可回退 SQLite 加速联调；生产需配置 Secrets 或环境数据库 URL
- 请勿将任何真实密钥写入代码或提交到版本库

## Next Steps
- 传大文件限制，需要先把文件传S3，再从S3下载到后端处理，首先后端接口生成S3 presigned URL，前端上传文件到该 URL，后端从 URL 下载文件到本地处理
- 需要用Job Batch，包括建表和处理Job，处理Job时需要从S3下载文件，处理完成后上传结果到S3