import { useMemo } from 'react'
import { useAppStore } from '../store/app'
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

export default function AnalyticsPage() {
  const exams = useAppStore((s) => s.exams)
  const selectedExamId = useAppStore((s) => s.selectedExamId)
  const selectExam = useAppStore((s) => s.selectExam)
  const papers = useAppStore((s) => s.papers)
  const tas = useAppStore((s) => s.tas)
  const exam = useMemo(() => exams.find((e) => e.exam_id === selectedExamId) || exams[0], [exams, selectedExamId])
  const data = useMemo(() => {
    if (!exam) return { labels: [], values: [] }
    const values = exam.questions.map((q) => {
      const scores = papers
        .filter((p) => p.exam_id === exam.exam_id)
        .map((p) => {
          const pq = p.questions.find((x) => x.question_id === q.question_id)
          const s = pq?.manual_score ?? pq?.ai_grading.score ?? 0
          return s
        })
      const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0
      return Number(avg.toFixed(2))
    })
    const labels = exam.questions.map((q) => `Q${q.question_id}`)
    return { labels, values }
  }, [exam, papers])
  const chart = {
    labels: data.labels,
    datasets: [
      {
        label: '平均分',
        data: data.values,
        backgroundColor: 'rgba(31, 142, 241, 0.5)'
      }
    ]
  }
  const exportJson = () => {
    const payload = { exam, papers: papers.filter((p) => p.exam_id === exam?.exam_id) }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'report.json'
    a.click()
  }
  const exportPdf = () => {
    window.print()
  }
  if (!exam) return <div className="card">暂无数据</div>
  return (
    <div className="row">
      <div className="card">
        <div className="title">得分分布</div>
        <Bar data={chart} options={{ responsive: true, plugins: { legend: { display: true } } }} />
      </div>
      <div className="card">
        <div className="title">试卷列表</div>
        <div className="grid-3" style={{ marginTop: 8 }}>
          <div className="field">
            <label>选择考试</label>
            <select value={exam?.exam_id} onChange={(e) => selectExam(e.target.value)}>
              {exams.map((e) => (
                <option key={e.exam_id} value={e.exam_id}>{e.title}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="btnbar" style={{ marginTop: 8 }}>
          <button className="btn" onClick={exportJson}>导出 JSON</button>
          <button className="btn" onClick={exportPdf}>导出 PDF</button>
        </div>
        <table className="table" style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>学生代码</th>
              <th>总分</th>
              <th>批阅人</th>
            </tr>
          </thead>
          <tbody>
            {papers.filter((p) => p.exam_id === exam.exam_id).map((p) => {
              const total = p.questions.reduce((sum, q) => sum + (q.manual_score ?? q.ai_grading.score), 0)
              return (
                <tr key={p.paper_id}>
                  <td>{p.test_code}</td>
                  <td>{total.toFixed(1)}</td>
                  <td>{tas.find((t) => t.ta_id === p.ta_id)?.ta_name || '-'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
