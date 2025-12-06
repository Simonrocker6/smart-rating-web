AI智能阅卷系统 — 前端产品需求（简化版）
🎯 核心目标
为教师/助教提供一个直观、高效、有未来感的网页界面，用于完成从考试配置到学生试卷批阅再到成绩分析的全流程操作。

🖥️ 页面与功能需求
1. 考试配置页（创建评分规则）
界面干净，采用卡片式分步引导。
支持动态添加题目，每题可填写：
满分值、标准答案（支持 LaTeX 显示预览）
解答页码 & 最终答案页码（数字输入）
评分模板（文本框，支持占位符如 {solution}，带示例提示）
“保存考试”按钮醒目，操作后平滑过渡到上传页。
2. 试卷上传页
中央大区域为拖拽上传区，支持多 PDF 文件。
自动从文件名识别学生标识（如 MIDTERM_ALICE_101.pdf → 显示“学生：ALICE_101”）。
顶部下拉菜单选择已配置的考试（默认选中最新一个）。
上传后显示文件列表，带“开始批阅”主按钮。
3. 题目级批阅页
左侧：导航栏显示所有题目（Q1, Q2...），当前题高亮。
右侧主内容区：
显示该题满分和标准答案（LaTeX 渲染，浅灰底色突出）
并排展示两张图片：
上：学生解答截图（模拟图像）
下：学生最终答案截图
AI 评阅结果：
得分输入框（默认填入 AI 建议分，可修改，范围锁定在 0~满分）
评语区域（只读，简洁自然语言，如“区间正确但未验证端点”）
底部固定操作栏：“上一题” / “下一题” / “保存并继续”
4. 成绩分析页
顶部选择考试下拉框。
主视图包含两个模块：
得分分布图：横向柱状图，每题平均分，配色清爽（蓝/青渐变）
试卷列表：表格形式，列包括：学生代码、总分、批阅人（默认当前 TA）
右上角“导出报告”按钮（图标 + 文字），点击下载 JSON 或 PDF（示意即可）
🎨 设计风格要求
整体色调：深蓝/石墨灰为主背景，搭配青色、白色作为强调色，体现“教育+AI”科技感。
字体：使用现代无衬线字体（如 HarmonyOS Sans、Inter 或系统默认）。
动效：微交互（如按钮悬停、页面切换淡入）提升流畅感，但不过度。
布局：留白充足，信息层级清晰，避免拥挤。
响应式：适配桌面为主，兼顾平板横屏体验。
✅ 用户体验原则
零学习成本：界面自解释，无需文档即可操作。
操作可逆：关键步骤（如修改分数）允许撤销或重新编辑。
反馈即时：输入校验、保存成功等状态有明确视觉提示。
专注核心任务：隐藏高级选项，默认路径最简。

补充：前端需遵循的数据模型（Sample Format）
前端所有页面应基于以下三种核心对象渲染，字段命名和嵌套结构必须严格一致。

1. 考试配置（Exam）
json
编辑
{
  "exam_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Calculus Midterm Fall 2025",
  "total_questions": 2,
  "created_at": "2025-11-20T10:00:00Z",
  "questions": [
    {
      "question_id": 1,
      "max_score": 5.0,
      "correct_answer": "[-3, 5]",
      "solution_page": 3,
      "final_answer_page": 3,
      "rubrics": [
        {
          "rubric_title": "Detailed Step-by-Step",
          "rubric_template": "1. step by step approach:\n- Step1 (2 points): Condition for \\sqrt{5-x} to be defined is 5-x ≥ 0...\n- Step2 (2 points): ...\n- Step3 (1 point): Final interval written as [-3,5]."
        },
        {
          "rubric_title": "Simple Final-Answer Focused",
          "rubric_template": "Award full {max_score} points if final answer is [-3,5] and student mentions both x≤5 and x≥-3."
        }
      ]
    },
    {
      "question_id": 2,
      "max_score": 4.0,
      "correct_answer": "f'(x) = 3x^2 - 6x",
      "solution_page": 4,
      "final_answer_page": 4,
      "rubrics": [
        {
          "rubric_title": "Default Rubric",
          "rubric_template": "Correct derivative earns full {max_score} points. Minor algebra error: -1. Missing chain rule: -2."
        }
      ]
    }
  ]
}
2. 试卷记录（Paper）
json
编辑
{
  "paper_id": "p9876543210",
  "exam_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "test_code": "ALICE_101",
  "ta_id": 1,
  "file_name": "MIDTERM_ALICE_101.pdf",
  "submitted_at": "2025-11-25T14:30:00Z",
  "questions": [
    {
      "question_id": 1,
      "solution_image_url": "https://picsum.photos/600/800?random=1 ",
      "final_answer_image_url": "https://picsum.photos/600/200?random=2 ",
      "ai_grading": {
        "score": 4.5,
        "explanation": "Correct interval but missed justification for x ≥ -3.",
        "graded_at": "2025-11-25T15:00:00Z"
      }
    },
    {
      "question_id": 2,
      "solution_image_url": "https://picsum.photos/600/800?random=3 ",
      "final_answer_image_url": "https://picsum.photos/600/200?random=4 ",
      "ai_grading": {
        "score": 3.0,
        "explanation": "Derivative correct except sign error in second term.",
        "graded_at": "2025-11-25T15:02:00Z"
      }
    }
  ]
}
3. 助教信息（TA）—— 仅用于显示
json
编辑
{
  "ta_id": 1,
  "ta_name": "Alice Chen",
  "email": "alice@univ.edu"
}
💡 前端只需在分析页或试卷列表中显示 ta_name，无需编辑。

🧪 建议的 Mock 数据（用于前端演示）
为快速搭建可交互原型，请在前端预置以下数据：

✅ 预置 1 个 Exam：
标题："微积分期中测验 2025"
包含 2 道题（如上所示）
✅ 预置 2 份 Papers：
test_code: "ALICE_101" → 总分 7.5 / 9
test_code: "BOB_205" → 总分 6.0 / 9（第二题得分为 2.0，评语：“未使用乘积法则”）
✅ 当前 TA：
ta_name: "张老师"（中文更友好）
🖼️ 前端展示映射建议
页面 使用的数据
考试配置页 可编辑的 Exam 对象（初始为空或复制 mock exam）
上传页 从下拉框选择已有的 mock Exam；上传后生成 mock Paper
批阅页 渲染一份 mock Paper，关联其 Exam.questions 获取满分和标准答案
分析页 汇总所有 mock Paper，按 exam_id 分组计算平均分
✅ 最终目标
前端在无后端情况下，能完整走通以下流程：

创建/选择考试 → 上传 PDF（模拟）→ 查看并修改每题得分 → 查看班级统计图表

所有 UI 元素均基于上述 JSON 结构渲染，确保未来对接 API 时字段无缝衔接。